import uuid
import time
import structlog
import json
import numpy as np

def setup_logger(name: str, level: str = "INFO"):
    """Configura o logger estruturado usando structlog."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.JSONRenderer()
        ]
    )
    return structlog.get_logger(name)

def generate_conflict_id() -> str:
    return str(uuid.uuid4())

def now_ts() -> float:
    return time.time()

def cosine_similarity(vec1: list, vec2: list) -> float:
    """Calcula a similaridade de cosseno entre dois vetores."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

def load_config(path: str) -> dict:
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger = setup_logger("utils")
        logger.error(f"Erro ao carregar configuração: {e}")
        return {}
