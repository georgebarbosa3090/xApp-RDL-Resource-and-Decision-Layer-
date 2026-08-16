from typing import Dict, List, Optional
from collections import deque
import math
from src.conflict_types import XAppAction, ConflictEvent, ConflictType, ConflictSeverity, KPMReport
import networkx as nx

class PerceptionAgent:
    def __init__(self):
        # Grafo de dependências KPI modelando as relações lógicas da rede
        # Parâmetro -> Afeta -> KPI
        self.kpi_dependency_graph = {
            "PRB_QUOTA": ["DRB.UEThpDl", "RRU.PrbUsedDl"],
            "SCHEDULER_WEIGHT": ["DRB.UEThpDl", "DRB.RlcSduDelayDl"],
            "TX_POWER": ["L1M.DL-sinr", "DRB.UEThpDl"]
        }
        # Registro das últimas ações: node_id -> parameter -> XAppAction
        self._action_registry: Dict[str, Dict[str, XAppAction]] = {}
        self.latest_kpm: Optional[KPMReport] = None
        
        # Monitoramento Adaptativo (Baseado em Matheus Dória, 2025)
        self.kpi_history = deque(maxlen=20)
        self.adaptive_threshold = 1.51  # Limiar θ calibrado na Fase KEP
        self.current_sampling_interval_ms = 1  # 1ms (Alto risco) ou 2ms (Baixo risco)

    def update_kpm_report(self, report: KPMReport):
        self.latest_kpm = report
        
        # Adaptive Monitoring: Armazena histórico para análise de risco na Fase KEP
        # Utilizando o Throughput de Downlink (drb_thp_dl) como proxy para variabilidade
        kpi_value = report.drb_thp_dl
        self.kpi_history.append(kpi_value)
        
        self._evaluate_monitoring_risk()

    def _evaluate_monitoring_risk(self):
        """
        Fases KEP (KPI Evaluation Phase) e SDP (Sampling Time Definition Phase).
        Ajusta a frequência de amostragem dinamicamente para economizar recursos (CPU/Energia).
        """
        if len(self.kpi_history) < 2:
            return
            
        # Calcula vetor de diferenças consecutivas (delta)
        history = list(self.kpi_history)
        deltas = [abs(history[i+1] - history[i]) for i in range(len(history)-1)]
        
        # Desvio Padrão dos deltas (σΔ)
        mean_delta = sum(deltas) / len(deltas)
        variance = sum((d - mean_delta)**2 for d in deltas) / len(deltas)
        sigma_delta = math.sqrt(variance)
        
        # Define o novo tempo de amostragem (Fase SDP)
        if sigma_delta < self.adaptive_threshold:
            # Risco Baixo -> Coleta mais esparsa para economizar CPU
            self.current_sampling_interval_ms = 2
        else:
            # Risco Alto -> Coleta detalhada para evitar perda de informações de conflito
            self.current_sampling_interval_ms = 1
            
        # Na integração final, este valor é usado para reenviar um E2 Subscription Request
        # alterando a frequência de reporte do E2 Node (via RIC).

    def get_active_xapps(self) -> Dict[str, List[XAppAction]]:
        active = {}
        for node, params in self._action_registry.items():
            for param, action in params.items():
                if action.xapp_id not in active:
                    active[action.xapp_id] = []
                active[action.xapp_id].append(action)
        return active

    def register_xapp_action(self, action: XAppAction) -> List[ConflictEvent]:
        conflicts = []
        
        # 1. Verifica Conflito Direto
        direct = self._detect_direct_conflict(action)
        if direct:
            conflicts.append(direct)
            
        # 2. Verifica Conflito Indireto
        indirects = self._detect_indirect_conflict(action)
        conflicts.extend(indirects)
        
        # Registra a nova ação
        if action.node_id not in self._action_registry:
            self._action_registry[action.node_id] = {}
        self._action_registry[action.node_id][action.parameter] = action
        
        return conflicts

    def _detect_direct_conflict(self, new_action: XAppAction) -> Optional[ConflictEvent]:
        if new_action.node_id in self._action_registry:
            if new_action.parameter in self._action_registry[new_action.node_id]:
                old_action = self._action_registry[new_action.node_id][new_action.parameter]
                if old_action.xapp_id != new_action.xapp_id:
                    # Conflito! Duas xApps diferentes mexendo no mesmo parâmetro
                    return ConflictEvent(
                        conflict_type=ConflictType.DIRECT,
                        severity=ConflictSeverity.HIGH,
                        involved_xapps=[old_action, new_action],
                        affected_kpis=self.kpi_dependency_graph.get(new_action.parameter, []),
                        description=f"Direct conflict on parameter {new_action.parameter}"
                    )
        return None

    def _detect_indirect_conflict(self, new_action: XAppAction) -> List[ConflictEvent]:
        conflicts = []
        new_kpis = self.kpi_dependency_graph.get(new_action.parameter, [])
        
        if not new_kpis or new_action.node_id not in self._action_registry:
            return conflicts
            
        for param, old_action in self._action_registry[new_action.node_id].items():
            if param == new_action.parameter or old_action.xapp_id == new_action.xapp_id:
                continue
            
            old_kpis = self.kpi_dependency_graph.get(param, [])
            common_kpis = set(new_kpis).intersection(set(old_kpis))
            
            if common_kpis:
                conflicts.append(ConflictEvent(
                    conflict_type=ConflictType.INDIRECT,
                    severity=ConflictSeverity.MEDIUM,
                    involved_xapps=[old_action, new_action],
                    affected_kpis=list(common_kpis),
                    description=f"Indirect conflict on KPIs {common_kpis} via params {param} and {new_action.parameter}"
                ))
        return conflicts
