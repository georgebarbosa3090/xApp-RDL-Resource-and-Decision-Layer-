from src.agents.perception_agent import PerceptionAgent
from src.conflict_types import ConflictType

def test_direct_conflict(perception_agent, action_qos, action_energy):
    # Registra ação 1
    conflicts_1 = perception_agent.register_xapp_action(action_qos)
    assert len(conflicts_1) == 0
    
    # Registra ação 2 (mesmo nó, mesmo parâmetro) -> Conflito direto
    conflicts_2 = perception_agent.register_xapp_action(action_energy)
    assert len(conflicts_2) == 1
    assert conflicts_2[0].conflict_type == ConflictType.DIRECT
    assert len(conflicts_2[0].involved_xapps) == 2

def test_indirect_conflict(perception_agent, action_qos, action_handover):
    # Registra ação 1 (afeta DRB.UEThpDl)
    perception_agent.register_xapp_action(action_qos)
    
    # Registra ação 2 (afeta DRB.UEThpDl) -> Conflito indireto
    conflicts = perception_agent.register_xapp_action(action_handover)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.INDIRECT
    assert "DRB.UEThpDl" in conflicts[0].affected_kpis
