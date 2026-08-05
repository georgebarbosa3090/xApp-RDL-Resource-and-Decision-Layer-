from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Target(BaseModel):
    node_id: str
    cell_id: str
    ue_ids: List[str] = Field(default_factory=list)
    slice_ids: List[str] = Field(default_factory=list)

class Action(BaseModel):
    type: str
    parameters: Dict[str, Any]

class ActionProposal(BaseModel):
    schema_version: str = "1.0"
    proposal_id: str
    source_xapp: str
    timestamp: str
    valid_until: str
    target: Target
    action: Action
    priority: int = 0
    utility: float = 0.0
    constraints: List[str] = Field(default_factory=list)
    expected_effect: Dict[str, Any] = Field(default_factory=dict)
    rollback: Dict[str, Any] = Field(default_factory=dict)
