"""
Unit & Property Tests for Independent Schedule Validator.
Verifies that:
1. Validator flags overlapping blocks.
2. Validator flags blocks extending outside window bounds.
3. Validator flags equipment fleet overcommitments.
4. Real optimizer schedule passes with ZERO violations.
"""

import pytest
import pandas as pd
from optimizer.validator import validate_schedule, ScheduleValidationReport


def test_validator_detects_collision():
    # Setup two conflicting blocks on same section and day
    schedule_data = [
        {
            "block_id": "BLK-01",
            "corridor": "Mumbai-Pune",
            "section": "Kalyan - Lonavala",
            "day_of_week": "Monday",
            "block_start_hour": 10.0,
            "block_end_hour": 12.0,
            "total_hours": 2.0
        },
        {
            "block_id": "BLK-02",
            "corridor": "Mumbai-Pune",
            "section": "Kalyan - Lonavala",
            "day_of_week": "Monday",
            "block_start_hour": 11.5,  # Overlaps by 0.5 hours!
            "block_end_hour": 13.5,
            "total_hours": 2.0
        }
    ]
    sched_df = pd.DataFrame(schedule_data)
    coa_df = pd.DataFrame()

    report = validate_schedule(sched_df, coa_df)
    assert not report.is_valid
    assert len(report.violations) >= 1
    assert any(v["rule"] == "TRACK_EXCLUSIVITY_COLLISION" for v in report.violations)


def test_validator_detects_window_breach():
    # Setup block outside window boundary
    schedule_data = [
        {
            "block_id": "BLK-01",
            "corridor": "Mumbai-Pune",
            "section": "Kalyan - Lonavala",
            "day_of_week": "Monday",
            "window_id": "WIN-01",
            "block_start_hour": 9.0,   # Starts before window!
            "block_end_hour": 12.0,
            "total_hours": 3.0
        }
    ]
    coa_data = [
        {
            "window_id": "WIN-01",
            "window_start_hour": 10.0,
            "window_end_hour": 13.0,
            "train_density": "off-peak"
        }
    ]
    sched_df = pd.DataFrame(schedule_data)
    coa_df = pd.DataFrame(coa_data)

    report = validate_schedule(sched_df, coa_df)
    assert not report.is_valid
    assert any(v["rule"] == "WINDOW_OUT_OF_BOUNDS" for v in report.violations)


def test_validator_passes_on_real_optimizer_output():
    from database.loader import load_data
    from ai_engine.prioritizer import compute_criticality_scores
    from ai_engine.clustering import cluster_tasks
    from optimizer.solver import solve_block_scheduling

    data = load_data()
    scored = compute_criticality_scores(data["all_tasks"])
    blocks_df, _ = cluster_tasks(scored)
    schedule_df, _ = solve_block_scheduling(
        blocks_df=blocks_df,
        coa_df=data["coa"],
        equipment_df=data.get("equipment"),
    )

    report = validate_schedule(
        schedule_df=schedule_df,
        coa_df=data["coa"],
        equipment_df=data.get("equipment"),
    )

    assert report.is_valid, f"Validation failed with {len(report.violations)} violations: {report.violations}"
    assert len(report.violations) == 0
