from typing import Protocol, List
from src.domain.proposals import ActionProposal
from src.domain.conflicts import Conflict
from src.domain.decisions import Decision

class NetworkState:
    # Representa o estado atual da rede baseado nos relatórios KPM
    pass

class DecisionStrategy(Protocol):
    def decide(
        self,
        state: NetworkState,
        proposals: List[ActionProposal],
        conflicts: List[Conflict]
    ) -> Decision:
        ...
