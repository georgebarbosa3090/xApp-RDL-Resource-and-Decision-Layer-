import pytest
from src.conflict_types import XAppAction, ConflictEvent, ConflictType, ConflictSeverity
from src.infrastructure.sdl_repository import SdlRepository
from src.agents.reasoning_agent import ReasoningAgent

def test_static_priority_resolution():
    memory = SdlRepository()
    reasoning = ReasoningAgent(memory, config={})
    
    action1 = XAppAction(xapp_id="qos_xapp", node_id="gnb_01", parameter="PRB_QUOTA", value=80, priority=100)
    action2 = XAppAction(xapp_id="energy_xapp", node_id="gnb_01", parameter="PRB_QUOTA", value=40, priority=60)
    
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[action1, action2],
        affected_kpis=["DRB.UEThpDl"],
        description="Direct conflict on PRB_QUOTA"
    )
    
    # Resolvendo o conflito
    resolution = reasoning.resolve(conflict)
    
    # O ReasoningAgent deve escolher a ação com maior prioridade (qos_xapp, priority 100)
    assert resolution.winning_action is not None
    assert resolution.winning_action.xapp_id == "qos_xapp"
    assert resolution.strategy_used.name == "PRIORITY_TABLE"

def test_marl_fallback_for_indirect():
    memory = SdlRepository()
    reasoning = ReasoningAgent(memory, config={})
    
    action1 = XAppAction(xapp_id="qos_xapp", node_id="gnb_01", parameter="SCHEDULER_WEIGHT", value=5)
    action2 = XAppAction(xapp_id="energy_xapp", node_id="gnb_01", parameter="TX_POWER", value=-10)
    
    conflict = ConflictEvent(
        conflict_type=ConflictType.INDIRECT,
        severity=ConflictSeverity.MEDIUM,
        involved_xapps=[action1, action2],
        affected_kpis=["DRB.UEThpDl"],
        description="Indirect conflict via throughput KPI"
    )
    
    # Para conflitos indiretos, deve usar MARL
    resolution = reasoning.resolve(conflict)
    
    assert resolution.winning_action is not None
    assert resolution.strategy_used.name == "MARL_AGENT"
