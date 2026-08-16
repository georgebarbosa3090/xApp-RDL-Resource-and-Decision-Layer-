import pytest
from src.knowledge_graph import GraphStore, GraphBuilder, GraphReasoner

def test_knowledge_graph_skeletons():
    store = GraphStore()
    builder = GraphBuilder(store)
    reasoner = GraphReasoner(store)
    
    # Asserting instantiation
    assert store is not None
    assert builder is not None
    assert reasoner is not None
    
    # Checking interfaces
    assert hasattr(store, 'execute_query')
    assert hasattr(store, 'add_node')
    assert hasattr(store, 'add_edge')
    
    assert hasattr(builder, 'build_from_kpm')
    assert hasattr(builder, 'build_from_action')
    
    assert hasattr(reasoner, 'detect_indirect_conflicts')
    assert hasattr(reasoner, 'check_policy_violations')
