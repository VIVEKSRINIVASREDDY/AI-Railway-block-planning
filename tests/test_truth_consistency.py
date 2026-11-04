import pytest
from unittest.mock import patch
from api.routes import compute_unified_kpis
from api.state import state

def test_single_source_of_truth_kpis_endpoint():
    """Verify compute_unified_kpis returns standardized KPI formulas and values."""
    state["is_ready"] = True
    state["stats"] = {
        "run_id": "RUN-TEST-01",
        "blocks_scheduled": 112,
        "total_blocks": 132,
        "tasks_scheduled": 232,
        "total_tasks": 260,
        "asset_availability_pct": 91.5,
        "block_utilization_pct": 40.6,
        "integration_rate_pct": 90.0,
        "solver_status": "OPTIMAL",
        "total_hours_used": 392.1,
        "solve_time_seconds": 0.24
    }

    # Test the compute logic directly to be resilient against network timeouts in sandboxed tests
    data = compute_unified_kpis()
    
    # Required keys per docs/kpis.md
    assert "asset_availability_pct" in data
    assert "block_utilization_pct" in data
    assert "joint_block_rate_pct" in data
    assert "schedule_rate_pct" in data
    assert "target_asset_availability_pct" in data
    assert data["target_asset_availability_pct"] == 88.0
    assert "formulas" in data
    assert "asset_availability" in data["formulas"]
    assert "joint_block_rate" in data["formulas"]
    assert data["provenance"] in ["REAL", "SYNTHETIC", "SIMULATED", "LIVE"]

def test_resilience_is_none_before_incident():
    """Verify resilience score is N/A (None) on clean baseline plan."""
    from analytics.resilience import compute_resilience_score
    res = compute_resilience_score()
    assert res["overall_score"] is None
    assert res["stability"] is None
    assert "N/A" in res["message"]

def test_resilience_is_none_before_incident():
    """Verify resilience score is N/A (None) on clean baseline plan."""
    from analytics.resilience import compute_resilience_score
    res = compute_resilience_score()
    assert res["overall_score"] is None
    assert res["stability"] is None
    assert "N/A" in res["message"]
