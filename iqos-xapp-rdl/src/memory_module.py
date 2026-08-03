from typing import List, Optional
from collections import deque
import networkx as nx
from neo4j import GraphDatabase
import structlog
from src.conflict_types import XAppAction, ConflictEvent, ResolutionAction

logger = structlog.get_logger("memory")

class MemoryModule:
    def __init__(self, max_buffer_size=1000, memgraph_uri="bolt://localhost:7687", user="", password=""):
        self.action_buffer = deque(maxlen=max_buffer_size)
        self.conflict_buffer = deque(maxlen=max_buffer_size)
        self.resolution_buffer = deque(maxlen=max_buffer_size)
        
        self.kg = nx.DiGraph()
        
        self.neo4j_driver = None
        try:
            self.neo4j_driver = GraphDatabase.driver(memgraph_uri, auth=(user, password))
            self.neo4j_driver.verify_connectivity()
            logger.info("Conectado ao Memgraph com sucesso")
            self._init_knowledge_graph()
        except Exception as e:
            logger.warning("Memgraph indisponível. Usando NetworkX (In-Memory) como fallback.", error=str(e))
            
    def _init_knowledge_graph(self):
        if not self.neo4j_driver:
            return
        query = "CREATE INDEX ON :XAppAction(xapp_id);"
        try:
            with self.neo4j_driver.session() as session:
                session.run(query)
        except Exception as e:
            pass # Index already exists or not supported
            
    def add_action(self, action: XAppAction):
        self.action_buffer.append(action)
        node_name = f"action_{action.xapp_id}_{action.timestamp}"
        self.kg.add_node(node_name, type="Action", xapp_id=action.xapp_id, parameter=action.parameter, value=action.value)
        
        if self.neo4j_driver:
            query = (
                "CREATE (a:XAppAction {xapp_id: $xapp_id, parameter: $parameter, value: $value, timestamp: $timestamp})"
            )
            try:
                with self.neo4j_driver.session() as session:
                    session.run(query, xapp_id=action.xapp_id, parameter=action.parameter, value=action.value, timestamp=action.timestamp)
            except Exception as e:
                logger.error("Erro ao inserir ação no Memgraph", error=str(e))

    def add_conflict(self, event: ConflictEvent):
        self.conflict_buffer.append(event)
        
    def add_resolution(self, resolution: ResolutionAction):
        self.resolution_buffer.append(resolution)
        
    def get_recent_actions(self, n=50) -> List[XAppAction]:
        return list(self.action_buffer)[-n:]
        
    def get_similar_resolutions(self, conflict: ConflictEvent, top_k=5) -> List[ResolutionAction]:
        results = []
        for res in reversed(self.resolution_buffer):
            results.append(res)
            if len(results) >= top_k:
                break
        return results
