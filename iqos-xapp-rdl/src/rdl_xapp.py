import time
import threading
import json
import os
from typing import Dict, Any

from ricxappframe.xapp_frame import Xapp
from src.utils import setup_logger, now_ts
from src.memory_module import MemoryModule
from src.perception_agent import PerceptionAgent
from src.reasoning_agent import ReasoningAgent
from src.refinement_agent import RefinementAgent
from src.metrics_server import MetricsServer
from src.asn1_decoder import E2SMKPMDecoder
from src.conflict_types import XAppAction, KPMReport, ConflictSeverity

logger = setup_logger("rdl_xapp")

# Message Types Constants
RIC_INDICATION = 12050
RIC_CONTROL_REQ = 12010
RIC_CONTROL_ACK = 12011
RIC_CONTROL_FAILURE = 12012
RDL_ACTION_PROPOSAL = 30000

class RDLxApp:
    def __init__(self):
        self.memory = MemoryModule()
        self.perception = PerceptionAgent()
        self.reasoning = ReasoningAgent(self.memory, config={})
        self.refinement = RefinementAgent(self.memory)
        self.metrics = MetricsServer(port=8081)
        self.asn1_decoder = E2SMKPMDecoder()
        
        use_fake_sdl = os.getenv("USE_FAKE_SDL", "True").lower() in ("true", "1", "yes")
        
        self.xapp = Xapp(
            entrypoint=self._entrypoint,
            rmr_port=4560,
            rmr_wait_for_ready=True,
            use_fake_sdl=use_fake_sdl
        )
        
        self.xapp.register_callback(self._kpm_indication_handler, RIC_INDICATION)
        self.xapp.register_callback(self._action_proposal_handler, RDL_ACTION_PROPOSAL)
        self.xapp.register_callback(self._control_ack_handler, RIC_CONTROL_ACK)
        self.xapp.register_callback(self._control_failure_handler, RIC_CONTROL_FAILURE)
        
        self.running = False

    def start(self):
        logger.info("Iniciando xApp RDL")
        self.metrics.start()
        self.running = True
        self.xapp.run()

    def stop(self):
        self.running = False
        self.xapp.stop()
        
    def _entrypoint(self, xapp_instance: Xapp):
        logger.info("xApp Framework Ready")
        # Em um cenário real, aqui seria feita a descoberta de E2 Nodes via E2Manager (REST)
        # e o envio de RIC_SUBSCRIPTION_REQUEST para KPM (se a RDL for responsável por assinar)
        threading.Thread(target=self._decision_loop, daemon=True).start()

    def _kpm_indication_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        self.metrics.record_kpm()
        payload = summary.get("payload")
        if payload:
            reports_data = self.asn1_decoder.decode_indication(payload)
            if reports_data:
                for data in reports_data:
                    report = KPMReport(
                        node_id=data.get("node_id", "gnb_01"),
                        ue_id=data.get("ue_id", "unknown"),
                        drb_thp_dl=data.get("drb_thp_dl", 0.0),
                        drb_thp_ul=data.get("drb_thp_ul", 0.0),
                        drb_delay_dl=data.get("drb_delay_dl", 0.0),
                        prb_used_dl=data.get("prb_used_dl", 0)
                    )
                    self.perception.update_kpm_report(report)
        xapp_instance.rmr_free(sbuf)

    def _action_proposal_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        """Recebe ações propostas por outras xApps via RMR"""
        payload = summary.get("payload")
        if payload:
            try:
                data = json.loads(payload.decode('utf-8'))
                action = XAppAction(
                    xapp_id=data['xapp_id'],
                    node_id=data['node_id'],
                    parameter=data['parameter'],
                    value=data['value'],
                    priority=data.get('priority', 50)
                )
                self._process_action(action)
            except Exception as e:
                logger.error("Erro ao processar RDL_ACTION_PROPOSAL", error=str(e))
        xapp_instance.rmr_free(sbuf)

    def _control_ack_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        logger.info("Recebido RIC_CONTROL_ACK", summary=summary)
        xapp_instance.rmr_free(sbuf)

    def _control_failure_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        logger.warning("Recebido RIC_CONTROL_FAILURE", summary=summary)
        xapp_instance.rmr_free(sbuf)

    def inject_xapp_action(self, action: XAppAction):
        """API pública para injeção de ações simuladas (usada em testes)"""
        self._process_action(action)

    def _process_action(self, action: XAppAction):
        self.memory.add_action(action)
        t0 = now_ts()
        conflicts = self.perception.register_xapp_action(action)
        self.metrics.update_active_xapps(len(self.perception.get_active_xapps()))
        
        for conflict in conflicts:
            logger.info("Conflito Detectado", conflict_id=conflict.conflict_id, type=conflict.conflict_type.name)
            self.memory.add_conflict(conflict)
            self.metrics.record_conflict(conflict)
            
            resolution = self.reasoning.resolve(conflict)
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
        """Constrói e envia um RIC_CONTROL_REQUEST real via RMR."""
        # Em produção, aqui empacotaríamos os dados usando o PyCrate para E2SM-RC APER
        # Como fallback/mock representativo, enviamos um payload JSON simples 
        # (o E2Term espera ASN.1 real, mas para RMR xApp->xApp JSON é comum).
        logger.info(f"Preparando envio de Controle E2 para {node_id}: {parameter}={value}")
        
        payload_dict = {
            "node_id": node_id,
            "parameter": parameter,
            "value": value
        }
        payload_bytes = json.dumps(payload_dict).encode('utf-8')
        
        success = self.xapp.rmr_send(payload=payload_bytes, mtype=RIC_CONTROL_REQ)
        if success:
            logger.info("RIC_CONTROL_REQUEST enviado com sucesso")
        else:
            logger.error("Falha ao enviar RIC_CONTROL_REQUEST")

if __name__ == "__main__":
    app = RDLxApp()
    try:
        app.start()
    except KeyboardInterrupt:
        app.stop()
