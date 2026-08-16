"""
Graph Reasoner
Realiza inferências semânticas sobre o grafo para descobrir relações implícitas,
prever impactos de ações (AFFECTS) e detectar conflitos indiretos.
"""

class GraphReasoner:
    def __init__(self, graph_store):
        self.graph_store = graph_store

    def detect_indirect_conflicts(self, proposed_action):
        """
        Infere se uma ação afeta indiretamente os KPIs de outra xApp ou
        degrada parâmetros relacionados usando queries Cypher complexas.
        """
        # Busca se a ação proposta em Parameter(X) afeta um KPI(Y) que é monitorado
        # ou otimizado por outra xApp ativa (TARGETS).
        query = """
        MATCH (action_xapp:XApp {id: $xapp_id})-[:CONTROLS]->(param:Parameter {name: $parameter})
        MATCH (param)-[:AFFECTS]->(kpi:KPI)<-[:TARGETS]-(other_xapp:XApp)
        WHERE action_xapp.id <> other_xapp.id
        RETURN other_xapp.id AS conflicting_xapp, kpi.name AS affected_kpi
        """
        parameters = {
            "xapp_id": proposed_action.xapp_id,
            "parameter": proposed_action.parameter
        }
        
        # Executa a query através do Graph Store (Neo4j)
        result = self.graph_store.execute_query(query, parameters)
        
        conflicts = []
        if result:
            for record in result:
                conflicts.append({
                    "type": "INDIRECT",
                    "conflicting_xapp": record["conflicting_xapp"],
                    "affected_kpi": record["affected_kpi"]
                })
        return conflicts

    def check_policy_violations(self, proposed_action):
        """
        Verifica se a ação viola regras semânticas estabelecidas pelo operador
        (ex: cobertura mínima vs potência).
        """
        # Busca se o parâmetro alterado tem uma política que governa o valor.
        query = """
        MATCH (param:Parameter {name: $parameter})<-[:GOVERNS]-(policy:Policy)
        RETURN policy.name AS policy_name, policy.operator AS operator, policy.limit AS limit
        """
        parameters = {
            "parameter": proposed_action.parameter
        }
        
        result = self.graph_store.execute_query(query, parameters)
        
        violations = []
        if result:
            for record in result:
                # Mock lógica de avaliação da política extraída do grafo
                op = record["operator"]
                limit = float(record["limit"])
                val = float(proposed_action.value)
                
                is_violation = False
                if op == "<" and val >= limit: is_violation = True
                elif op == ">" and val <= limit: is_violation = True
                elif op == "==" and val != limit: is_violation = True
                
                if is_violation:
                    violations.append({
                        "policy": record["policy_name"],
                        "expected": f"{op} {limit}",
                        "actual": val
                    })
        return violations
