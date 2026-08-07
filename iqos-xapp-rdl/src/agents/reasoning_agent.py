from typing import List, Tuple
from src.conflict_types import ConflictEvent, ResolutionAction, ResolutionStrategy, XAppAction
from src.infrastructure.sdl_repository import SdlRepository
from src.agents.marl.mappo_agent import MAPPOCoordinator
import math
import itertools

class ReasoningAgent:
    def __init__(self, memory: SdlRepository, config: dict):
        self.memory = memory
        self.config = config
        
        # MAPPOCoordinator setup
        self.mappo = MAPPOCoordinator(n_agents=2, obs_dim=10, action_dim=5, config=config)

    def resolve(self, conflict: ConflictEvent) -> ResolutionAction:
        # 1. Busca no Histórico (KG)
        similar_resolutions = self.memory.get_similar_resolutions(conflict)
        if similar_resolutions:
            best_res = similar_resolutions[0]
            if best_res.confidence > 0.8:
                return self._resolve_by_history(conflict, similar_resolutions)
                
        # 2. Conflitos Diretos: TVS ou EEVS (SLA-based) ou Combinatória MOCK
        if conflict.conflict_type.name == "DIRECT":
            # Escolhemos TVS (Throughput Violation-based Selection) como política padrão
            return self._resolve_by_sla_utility(conflict, policy="TVS")
            
        # 3. Conflitos Indiretos: MARL ou Combinatória
        return self._resolve_by_marl(conflict)

    def _resolve_by_sla_utility(self, conflict: ConflictEvent, policy: str) -> ResolutionAction:
        # Avaliação combinatória (Feature 2) & SLA Policies (Feature 3)
        # O paper do MLO (2026) avalia 2^N combinações.
        # Aqui fazemos um Mock da utilidade prevista para cada subconjunto de ações envolvidas no conflito.
        
        actions = conflict.involved_xapps
        best_score = -float('inf')
        best_subset = []
        best_policy_used = ResolutionStrategy.TVS if policy == "TVS" else ResolutionStrategy.EEVS

        # Gera o power set (todas as combinações possíveis)
        # Pula o conjunto vazio (nenhuma ação) a menos que todas sejam muito ruins
        powerset = []
        for i in range(1, len(actions) + 1):
            powerset.extend(list(itertools.combinations(actions, i)))
            
        for subset in powerset:
            score = self._mock_evaluate_subset(list(subset), policy)
            if score > best_score:
                best_score = score
                best_subset = list(subset)
                
        # Se for escolhida mais de uma ação num conflito direto, significa que as ações são complementares
        # (na prática, em conflito direto sobre o MESMO parâmetro, a combinação falhará no mock se for contraditória)
        
        modified_val = best_subset[0].value if len(best_subset) == 1 else None

        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=best_policy_used,
            winning_actions=best_subset,
            modified_value=modified_val,
            confidence=0.9,
            validation_level=0
        )

    def _mock_evaluate_subset(self, subset: List[XAppAction], policy: str) -> float:
        """
        Calcula as pontuações s_j(t) como descrito no COMIX (2025).
        Como não temos NDT integrado ainda, usamos heurísticas para simular UEs insatisfeitos.
        """
        # Checagem de sanidade: Se o subset tem ações diretas contraditórias sobre o mesmo parâmetro, 
        # a utilidade afunda (pois fisicamente na RAN não dá pra setar 2 valores pro mesmo PRB simultaneamente)
        param_targets = {}
        for act in subset:
            key = f"{act.node_id}_{act.parameter}"
            if key in param_targets and param_targets[key] != act.value:
                return -9999.0 # Inconsistência física, utilidade mínima
            param_targets[key] = act.value

        # Heurística MOCK para SLA Violations
        # Supondo 10 UEs na rede para cálculo. 
        total_ues = 10
        violations = 0
        total_power = 0.0
        
        # Simula efeito baseado no valor do parâmetro (MOCK)
        for act in subset:
            if act.parameter == "TX_POWER":
                total_power += act.value
                # Quanto maior a potência, menos violações de throughput, mas mais consumo
                if act.value < 20.0:
                    violations += 3
                elif act.value < 30.0:
                    violations += 1
            else:
                total_power += 10.0 # valor base

        if policy == "TVS":
            # Equação 11 do paper COMIX: s_j^4(t) = - \sum C_u(t) - 1 / (1 + exp(-p_total))
            penalty = 1 / (1 + math.exp(-total_power)) if total_power > 0 else 0.5
            return -violations - penalty

        elif policy == "EEVS":
            # Equação 13 do paper COMIX: s_j^5(t) = - \sum E_u(t) - 1 / (1 + exp(-p_total))
            # Para EEVS, potências muito altas também geram violações de EE (Efficiency = Throughput / Power)
            if total_power > 30.0:
                violations += 4 # alta penalidade por ineficiência
            penalty = 1 / (1 + math.exp(-total_power)) if total_power > 0 else 0.5
            return -violations - penalty

        return 0.0

    def _resolve_by_marl(self, conflict: ConflictEvent) -> ResolutionAction:
        kpm_state = {}
        winning_action, confidence = self.mappo.decide(conflict, kpm_state)
        
        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=ResolutionStrategy.MARL_AGENT,
            winning_actions=[winning_action] if winning_action else [],
            modified_value=winning_action.value if winning_action else None,
            confidence=confidence,
            validation_level=0
        )

    def _resolve_by_history(self, conflict: ConflictEvent, similar: List[ResolutionAction]) -> ResolutionAction:
        best_past_res = similar[0]
        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=best_past_res.strategy_used,
            winning_actions=best_past_res.winning_actions,
            modified_value=best_past_res.modified_value,
            confidence=best_past_res.confidence,
            validation_level=0
        )
