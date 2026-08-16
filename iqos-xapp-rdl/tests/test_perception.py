import pytest
from src.agents.perception_agent import PerceptionAgent
from src.conflict_types import KPMReport

def create_kpm(thp: float) -> KPMReport:
    return KPMReport(
        node_id="gnb_01",
        ue_id="ue_01",
        drb_thp_dl=thp,
        drb_thp_ul=0.0,
        drb_delay_dl=0.0,
        prb_used_dl=0
    )

def test_adaptive_monitoring_high_risk():
    agent = PerceptionAgent()
    # High risk values -> high variance in deltas -> 1ms interval
    values = [0, 0, 10, 10, 20, 0]
    for v in values:
        agent.update_kpm_report(create_kpm(v))
    
    assert agent.current_sampling_interval_ms == 1

def test_adaptive_monitoring_low_risk():
    agent = PerceptionAgent()
    # Low risk values -> low variance in deltas -> 2ms interval
    values = [10, 10, 11, 11, 10, 10]
    for v in values:
        agent.update_kpm_report(create_kpm(v))
        
    assert agent.current_sampling_interval_ms == 2
