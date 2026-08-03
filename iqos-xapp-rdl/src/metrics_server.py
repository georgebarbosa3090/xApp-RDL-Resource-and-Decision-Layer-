from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog
from src.conflict_types import ConflictEvent, ResolutionAction

logger = structlog.get_logger("metrics")

class MetricsServer:
    def __init__(self, port=8081):
        self.port = port
        
        # Define Metrics
        self.conflicts_detected = Counter(
            'rdl_conflicts_detected_total', 
            'Total conflicts detected',
            ['conflict_type', 'severity']
        )
        
        self.conflicts_resolved = Counter(
            'rdl_conflicts_resolved_total',
            'Total conflicts resolved',
            ['strategy', 'success']
        )
        
        self.decision_latency = Histogram(
            'rdl_decision_latency_seconds',
            'Time spent making a resolution decision',
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
        )
        
        self.active_xapps = Gauge('rdl_active_xapps', 'Number of active xApps interacting with RDL')
        self.kpm_messages = Counter('rdl_kpm_messages_total', 'Total KPM messages processed')
        
    def start(self):
        try:
            start_http_server(self.port)
            logger.info("Servidor Prometheus iniciado", port=self.port)
        except Exception as e:
            logger.error("Falha ao iniciar servidor de métricas", error=str(e))
            
    def record_conflict(self, conflict: ConflictEvent):
        self.conflicts_detected.labels(
            conflict_type=conflict.conflict_type.name,
            severity=conflict.severity.name
        ).inc()
        
    def record_resolution(self, resolution: ResolutionAction, latency_s: float):
        self.conflicts_resolved.labels(
            strategy=resolution.strategy_used.name,
            success=str(resolution.validation_level > 0)
        ).inc()
        self.decision_latency.observe(latency_s)
        
    def record_kpm(self):
        self.kpm_messages.inc()
        
    def update_active_xapps(self, count: int):
        self.active_xapps.set(count)
