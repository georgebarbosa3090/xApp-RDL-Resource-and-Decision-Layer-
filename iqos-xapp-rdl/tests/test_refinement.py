import pytest
from src.conflict_types import XAppAction, ConflictEvent, ConflictType, ConflictSeverity, ResolutionAction, ResolutionStrategy
from src.infrastructure.sdl_repository import SdlRepository
from src.agents.refinement_agent import RefinementAgent

def test_validation_ranges():
    memory = SdlRepository()
    refinement = RefinementAgent(memory)
    
    # Ação com PRB_QUOTA dentro do limite (0 a 100)
    action_valid = XAppAction(xapp_id="qos", node_id="gnb", parameter="PRB_QUOTA", value=80)
    conflict = ConflictEvent(ConflictType.DIRECT, ConflictSeverity.LOW, [action_valid], [])
    resolution_valid = ResolutionAction(conflict.conflict_id, ResolutionStrategy.PRIORITY_TABLE, action_valid, confidence=1.0)
    
    is_valid, level, reason = refinement.validate(resolution_valid, conflict)
    assert is_valid is True
    
    # Ação com PRB_QUOTA fora do limite (> 100)
    action_invalid = XAppAction(xapp_id="qos", node_id="gnb", parameter="PRB_QUOTA", value=150)
    resolution_invalid = ResolutionAction(conflict.conflict_id, ResolutionStrategy.PRIORITY_TABLE, action_invalid, confidence=1.0)
    
    is_valid, level, reason = refinement.validate(resolution_invalid, conflict)
    assert is_valid is False
    assert "fora do limite" in reason

def test_formal_validation_critical_conflict():
    memory = SdlRepository()
    refinement = RefinementAgent(memory)
    
    # Simula um conflito CRÍTICO que deve passar pela checagem formal
    action1 = XAppAction(xapp_id="app1", node_id="gnb", parameter="PRB_QUOTA", value=60)
    action2 = XAppAction(xapp_id="app2", node_id="gnb", parameter="PRB_QUOTA", value=50)
    
    conflict = ConflictEvent(ConflictType.DIRECT, ConflictSeverity.CRITICAL, [action1, action2], [])
    
    # Se a resolução aprovar action1 (60), e a outra (50) for descartada, a soma das ativas (mock) 
    # poderia passar de 100 se o refinement checar a soma total real. No mock simples atual, valida a lógica.
    resolution = ResolutionAction(conflict.conflict_id, ResolutionStrategy.PRIORITY_TABLE, action1, confidence=1.0)
    
    is_valid, level, reason = refinement.validate(resolution, conflict)
    assert is_valid is True
    assert level == 3  # Passou pela checagem Nível 3 (formal)
