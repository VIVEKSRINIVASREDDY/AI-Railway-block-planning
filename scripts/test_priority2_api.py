"""
Verification script for Priority 2 Endpoints & Backend Differentiators.
Tests:
- Emergency Replanning & Diff Tracking
- What-If Scenario Simulations (Equipment breakdown, window squeeze, night only)
- AI Explainability (Factor breakdown, weights, XGBoost blend)
- Baseline vs AI Optimizer Comparison
"""

import sys
import os
import asyncio
from fastapi.testclient import TestClient

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.routes import app
from api.state import state

client = TestClient(app)

def test_pipeline_and_endpoints():
    print("\n" + "=" * 60)
    print("  RUNNING PRIORITY 2 VERIFICATION SUITE")
    print("=" * 60)

    # 1. Warm up pipeline
    print("\n[1/7] Testing POST /api/generate (Pipeline Warmup)...")
    res = client.post("/api/generate")
    assert res.status_code == 200, f"Generate failed: {res.text}"
    gen_data = res.json()
    print(f"  --> Success: {gen_data['message']}")
    print(f"  --> Blocks scheduled: {gen_data['stats']['blocks_scheduled']}/{gen_data['stats']['total_blocks']}")

    # 2. Health check
    print("\n[2/7] Testing GET /api/health...")
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["pipeline_ready"] is True
    print("  --> Health check OK (Pipeline Ready: True)")

    # 3. Tasks & Explainability
    print("\n[3/7] Testing AI Explainability Endpoint (GET /api/tasks/{id}/explain)...")
    res_tasks = client.get("/api/tasks")
    assert res_tasks.status_code == 200
    tasks = res_tasks.json()["tasks"]
    assert len(tasks) > 0, "No tasks returned!"
    sample_task_id = tasks[0]["task_id"]
    print(f"  --> Inspecting task '{sample_task_id}' (Dept: {tasks[0]['department']})...")

    res_explain = client.get(f"/api/tasks/{sample_task_id}/explain")
    assert res_explain.status_code == 200, f"Explain failed: {res_explain.text}"
    explain_data = res_explain.json()
    print(f"  --> Criticality Index: {explain_data['criticality_index']} ({explain_data['priority_tier']})")
    print(f"  --> Factors: {list(explain_data['factor_breakdown'].keys())}")
    print(f"  --> XGBoost Blend Contribution: {explain_data['blend_breakdown']['xgboost_component_20pct']}")
    print(f"  --> Audit narrative: {explain_data['audit_narrative']}")

    # Explainability summary
    res_summary = client.get("/api/explainability/summary")
    assert res_summary.status_code == 200
    summary_data = res_summary.json()
    print(f"  --> Priority tiers distribution: {summary_data['priority_distribution']}")

    # 4. Baseline Comparison
    print("\n[4/7] Testing Baseline vs AI Comparison (GET /api/baseline-comparison)...")
    res_comp = client.get("/api/baseline-comparison")
    assert res_comp.status_code == 200, f"Comparison failed: {res_comp.text}"
    comp_data = res_comp.json()
    print(f"  --> AI Integration Rate: {comp_data['ai_optimizer']['integration_rate_pct']}% vs Manual: {comp_data['manual_baseline']['integration_rate_pct']}%")
    print(f"  --> Track disruption hours saved: {comp_data['efficiency_gains']['hours_saved']} hours")
    print(f"  --> Executive verdict: {comp_data['executive_summary']}")

    # 5. What-If Scenario Presets & Simulation
    print("\n[5/7] Testing What-If Scenario Simulator...")
    res_presets = client.get("/api/scenario/presets")
    assert res_presets.status_code == 200
    presets = res_presets.json()["presets"]
    print(f"  --> Loaded {len(presets)} scenario presets.")

    # Run Tamper Breakdown Scenario
    print("  --> Simulating scenario: Track Tamper Fleet Breakdown...")
    tamper_payload = {
        "scenario_name": "Tamper Fleet Breakdown Test",
        "scenario_type": "equipment_breakdown",
        "disabled_equipment": ["tamper"],
        "window_duration_reduction_pct": 0,
        "night_only": False,
        "max_block_days_per_section": 3
    }
    res_sim = client.post("/api/scenario", json=tamper_payload)
    assert res_sim.status_code == 200, f"Scenario failed: {res_sim.text}"
    sim_data = res_sim.json()
    print(f"  --> Baseline Blocks: {sim_data['comparison']['blocks_scheduled']['baseline']} | Scenario: {sim_data['comparison']['blocks_scheduled']['scenario']}")
    print(f"  --> Delta: {sim_data['comparison']['blocks_scheduled']['delta']} blocks")
    print(f"  --> Recommendation: {sim_data['recommendations'][0]}")

    # 6. Emergency Dynamic Replanning
    print("\n[6/7] Testing Emergency Dynamic Replanning (POST /api/emergency)...")
    emergency_payload = {
        "incident_type": "Broken Rail",
        "km_marker": 42.5,
        "corridor": "Mumbai-Pune",
        "severity": "CRITICAL",
        "required_hours": 3.0,
        "description": "Severe transverse rail fracture detected by ultrasonic van near Kalyan Jn."
    }
    res_emg = client.post("/api/emergency", json=emergency_payload)
    assert res_emg.status_code == 200, f"Emergency replanning failed: {res_emg.text}"
    emg_data = res_emg.json()
    print(f"  --> Replanning computation: {emg_data['replanning_time_ms']} ms")
    print(f"  --> Emergency Block Assigned: {emg_data['diff']['emergency_block_id']} in Window {emg_data['diff']['window_id']}")
    print(f"  --> Displaced Blocks Detected: {emg_data['diff']['displaced_count']}")
    print(f"  --> Unaffected Blocks: {emg_data['diff']['unaffected_blocks_count']}")

    # Check emergency history
    res_hist = client.get("/api/emergency/history")
    assert res_hist.status_code == 200
    assert res_hist.json()["count"] >= 1
    print(f"  --> Emergency history logged: {res_hist.json()['count']} record(s).")

    # 7. Backward compatibility check
    print("\n[7/7] Testing Backward Compatibility (POST /api/inject-incident)...")
    compat_payload = {
        "incident_type": "OHE Wire Snap",
        "km_marker": 88.0,
        "corridor": "Mumbai-Pune",
        "severity": "HIGH",
        "required_hours": 2.5
    }
    res_compat = client.post("/api/inject-incident", json=compat_payload)
    assert res_compat.status_code == 200
    print("  --> Backward-compatible /api/inject-incident successfully processed.")

    print("\n" + "=" * 60)
    print("  ALL PRIORITY 2 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    test_pipeline_and_endpoints()
