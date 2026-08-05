from typing import Tuple, Dict, Any
import time
from src.domain.proposals import ActionProposal
from src.domain.decisions import Decision
from src.observability.logging import setup_logger

logger = setup_logger("RefinementAgent")

class RefinementAgent:
    def __init__(self, config: dict):
        self.config = config.get("safety", {
            "enabled": True,
            "max_prb_delta_percent": 20,
            "minimum_control_interval_ms": 1000,
            "reject_unknown_targets": True,
            "require_policy_compliance": True
        })
        self.last_control_time: Dict[str, float] = {}

    def validate(self, decision: Decision) -> Tuple[bool, str]:
        """
        Safety Guard que valida se o controle proposto é seguro (RF-16).
        """
        if not self.config.get("enabled", True):
            return True, "Safety guard disabled"
            
        action = decision.selected_action
        if not action:
            return False, "No action selected"

        target_key = f"{action.target.node_id}_{action.target.cell_id}"
        
        # 1. Validade temporal (frequência máxima de controle)
        now = time.time() * 1000
        last_time = self.last_control_time.get(target_key, 0)
        if (now - last_time) < self.config.get("minimum_control_interval_ms", 1000):
            return False, "Control frequency exceeded"
            
        # 2. Valores negativos ou fora de escopo para PRB/Power
        if action.action.type == "PRB_ALLOCATION":
            prb_val = action.action.parameters.get("prb_value", 0)
            if prb_val < 0 or prb_val > 100:
                return False, "PRB value out of bounds (0-100)"
                
        elif action.action.type == "TX_POWER":
            pwr = action.action.parameters.get("tx_power", 0)
            if pwr < -10 or pwr > 23:
                return False, "TX Power out of bounds (-10 to 23 dBm)"
        
        # 3. Alvos desconhecidos (mock, precisa integrar com e2_manager)
        if self.config.get("reject_unknown_targets", True):
            if action.target.node_id == "" or action.target.cell_id == "":
                return False, "Unknown target node/cell"

        # Se passou
        self.last_control_time[target_key] = now
        return True, "Passed safety checks"
