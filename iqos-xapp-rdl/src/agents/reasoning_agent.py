from typing import List
from src.conflict_types import ConflictEvent, ResolutionAction, ResolutionStrategy
from src.infrastructure.sdl_repository import SdlRepository
from src.agents.marl.mappo_agent import MAPPOCoordinator

class ReasoningAgent:
    def __init__(self, memory: SdlRepository, config: dict):
        self.memory = memory
        self.config = config
        
        # Priority Table Estática
        self._priority_table = {
            "QoS": 100,
            "HandoverOpt": 80,
            "EnergyEfficiency": 60,
            "LoadBalance": 40
        }
        
        # MAPPOCoordinator setup
        self.mappo = MAPPOCoordinator(n_agents=2, obs_dim=10, action_dim=5, config=config)

    def resolve(self, conflict: ConflictEvent) -> ResolutionAction:
        # 1. Busca no Histórico (KG)
        similar_resolutions = self.memory.get_similar_resolutions(conflict)
        if similar_resolutions:
            best_res = similar_resolutions[0]
            if best_res.confidence > 0.8:
                return self._resolve_by_history(conflict, similar_resolutions)
                
        # 2. Conflitos Diretos: Prioridade
        if conflict.conflict_type.name == "DIRECT":
            return self._resolve_by_priority(conflict)
            
        # 3. Conflitos Indiretos: MARL
        return self._resolve_by_marl(conflict)

    def _resolve_by_priority(self, conflict: ConflictEvent) -> ResolutionAction:
        best_action = None
        highest_priority = -1
        
        for action in conflict.involved_xapps:
            if action.priority > highest_priority:
                highest_priority = action.priority
                best_action = action
                
        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=ResolutionStrategy.PRIORITY_TABLE,
            winning_action=best_action,
            modified_value=best_action.value if best_action else None,
            confidence=0.9,
            validation_level=0
        )

    def _resolve_by_marl(self, conflict: ConflictEvent) -> ResolutionAction:
        kpm_state = {}
        winning_action, confidence = self.mappo.decide(conflict, kpm_state)
        
        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=ResolutionStrategy.MARL_AGENT,
            winning_action=winning_action,
            modified_value=winning_action.value if winning_action else None,
            confidence=confidence,
            validation_level=0
        )

    def _resolve_by_history(self, conflict: ConflictEvent, similar: List[ResolutionAction]) -> ResolutionAction:
        best_past_res = similar[0]
        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=best_past_res.strategy_used,
            winning_action=best_past_res.winning_action,
            modified_value=best_past_res.modified_value,
            confidence=best_past_res.confidence,
            validation_level=0
        )
