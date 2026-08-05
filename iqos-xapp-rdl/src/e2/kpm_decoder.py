import os
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
from src.observability.logging import setup_logger

logger = setup_logger("KPMDecoder")

@dataclass
class KpmMeasurement:
    timestamp: datetime
    node_id: str
    cell_id: Optional[str]
    ue_id: Optional[str]
    slice_id: Optional[str]
    metric_name: str
    value: float
    unit: Optional[str]
    granularity_ms: Optional[int]

class KpmDecoder:
    def __init__(self, mode: str = "production"):
        # Se RDL_MODE estiver setado como "simulation", ele permitirá uso de mocks em caso de erro.
        self.mode = os.getenv("RDL_MODE", mode)
        self.measurement_map = {
            "DRB.UEThpDl": "throughput_dl",
            "DRB.UEThpUl": "throughput_ul",
            "DRB.RlcSduDelayDl": "latency_dl",
            "RRU.PrbUsedDl": "prb_dl",
            "RRU.PrbUsedUl": "prb_ul"
        }

    def decode(self, indication_header: bytes, indication_message: bytes, node_id: str = "unknown") -> List[KpmMeasurement]:
        """
        Decodifica o payload E2SM-KPM.
        Requisito RF-09 e RF-10 (Remoção de valores simulados da produção).
        """
        measurements = []
        try:
            # Em modo produção, tentar decodificar usando PyCrate
            # Como a implementação do PyCrate exige a lib O-RAN completa compilada,
            # validaremos apenas a presença dos bytes.
            if not indication_header or not indication_message:
                raise ValueError("E2SM-KPM Header ou Message estão vazios.")
            
            # TODO: Substituir por PyCrate logic real
            # measurement_map dinâmico já mapeado no __init__
            pass

        except Exception as e:
            if self.mode == "simulation":
                logger.debug(f"Falha ao decodificar em modo de simulação, gerando KPM fictício: {e}")
                # Fallback APENAS para simulação
                measurements.append(KpmMeasurement(
                    timestamp=datetime.now(),
                    node_id=node_id,
                    cell_id="cell_01",
                    ue_id="ue_1",
                    slice_id=None,
                    metric_name="DRB.UEThpDl",
                    value=15.5,
                    unit="Mbps",
                    granularity_ms=1000
                ))
            else:
                # No modo production, falha deve gerar log e descartar
                logger.error(f"Falha de decodificação E2SM-KPM em produção: {e}")
                # Aqui o sistema descarta a mensagem ou encaminha para dead-letter (RF-10)
                raise

        return measurements
