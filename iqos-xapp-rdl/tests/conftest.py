import pytest
from src.conflict_types import XAppAction, KPMReport
from src.perception_agent import PerceptionAgent

@pytest.fixture
def perception_agent():
    return PerceptionAgent()

@pytest.fixture
def action_qos():
    return XAppAction(
        xapp_id="qos_xapp",
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=80.0,
        priority=100
    )

@pytest.fixture
def action_energy():
    return XAppAction(
        xapp_id="energy_xapp",
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=30.0,
        priority=60
    )

@pytest.fixture
def action_handover():
    return XAppAction(
        xapp_id="handover_xapp",
        node_id="gnb_01",
        parameter="SCHEDULER_WEIGHT",
        value=5.0,
        priority=80
    )
