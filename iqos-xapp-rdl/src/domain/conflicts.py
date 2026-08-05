from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from src.domain.proposals import ActionProposal

class ConflictType(str, Enum):
    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"
    RESOURCE = "RESOURCE"
    TEMPORAL = "TEMPORAL"
    POLICY = "POLICY"
    OBJECTIVE = "OBJECTIVE"

class Conflict(BaseModel):
    conflict_id: str
    type: ConflictType
    proposals: List[ActionProposal]
    detected_at: float
    description: str
