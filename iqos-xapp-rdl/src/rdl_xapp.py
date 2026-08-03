import time
import threading
from typing import Dict, Any

from ricxappframe.xapp_frame import Xapp
from src.utils import setup_logger, now_ts
from src.memory_module import MemoryModule
from src.perception_agent import PerceptionAgent
from src.reasoning_agent import ReasoningAgent
from src.refinement_agent import RefinementAgent
from src.metrics_server import MetricsServer
from src.asn1_decoder import E2SMKPMDecoder
from src.conflict_types import XAppAction

logger = setup_logger("rdl_xapp")

class RDLxApp:
    def __init__(self):
        # Módulos Core
        self.memory = MemoryModule()
        self.perception = PerceptionAgent()
        self.reasoning = ReasoningAgent(self.memory, config={})
        self.refinement = RefinementAgent(self.memory)
        self.metrics = MetricsServer(port=8081)
        self.asn1_decoder = E2SMKPMDecoder()
        
        # RIC xApp Framework handler
        self.xapp = Xapp(
            entrypoint=self._entrypoint,
            rmr_port=4560,
            rmr_wait_for_ready=True,
            use_fake_sdl=True
        )
        
        self.xapp.register_callback(self._kpm_indication_handler, 12050)
        self.running = False

    def start(self):
        logger.info("Iniciando xApp RDL")
        self.metrics.start()
        self.running = True
        self.xapp.run() # Bloqueia até a xapp parar

    def stop(self):
        self.running = False
        self.xapp.stop()
        
    def _entrypoint(self, xapp_instance: Xapp):
        logger.info("xApp Framework Ready")
        # Inicia loop assíncrono para processar buffer de decisões
        threading.Thread(target=self._decision_loop, daemon=True).start()

    def _kpm_indication_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        self.metrics.record_kpm()
        payload = summary.get("payload")
        if payload:
            reports = self.asn1_decoder.decode_indication(payload)
            if reports:
                # Mock: Pass reports to perception
                pass
        xapp_instance.rmr_free(sbuf)

    def inject_xapp_action(self, action: XAppAction):
        """API pública para injetar ações de outras xApps simuladas"""
        self.memory.add_action(action)
        
        t0 = now_ts()
        conflicts = self.perception.register_xapp_action(action)
        self.metrics.update_active_xapps(len(self.perception.get_active_xapps()))
        
        for conflict in conflicts:
            logger.info("Conflito Detectado", conflict_id=conflict.conflict_id, type=conflict.conflict_type.name)
            self.memory.add_conflict(conflict)
            self.metrics.record_conflict(conflict)
            
            # Reasoning
            resolution = self.reasoning.resolve(conflict)
            
            # Refinement
            is_valid, level, reason = self.refinement.validate(resolution, conflict)
            latency = now_ts() - t0
            
            self.memory.add_resolution(resolution)
            self.metrics.record_resolution(resolution, latency)
            
            if is_valid and resolution.winning_action:
                logger.info("Conflito Resolvido", conflict=conflict.conflict_id, strategy=resolution.strategy_used.name, action=resolution.winning_action.parameter)
                self._send_control(resolution.winning_action.node_id, resolution.winning_action.parameter, resolution.winning_action.value)
            else:
                logger.warning("Resolução Rejeitada", reason=reason)

    def _decision_loop(self):
        while self.running:
            time.sleep(1.0)
            
    def _send_control(self, node_id: str, parameter: str, value: float):
        """Envia RIC_CONTROL_REQUEST via RMR"""
        # Exemplo simplificado de envio de controle via xApp frame
        logger.info(f"Enviando Controle E2: {node_id} -> {parameter}={value}")

if __name__ == "__main__":
    app = RDLxApp()
    try:
        app.start()
    except KeyboardInterrupt:
        app.stop()
