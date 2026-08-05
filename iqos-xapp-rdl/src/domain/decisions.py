from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from src.domain.proposals import ActionProposal
from src.domain.conflicts import Conflict

class Decision(BaseModel):
    decision_id: str
    correlation_id: str
    timestamp: float
    source_xapps: List[str]
    affected_node: str
    affected_cell: str
    affected_ues: List[str]
    affected_slices: List[str]
    detected_conflicts: List[str]
    strategy: str
    model_version: str
    input_state: Dict[str, Any]
    selected_action: Optional[ActionProposal]
    confidence: float
    safety_validation: bool
    control_status: str
    control_latency: float
    result: str
