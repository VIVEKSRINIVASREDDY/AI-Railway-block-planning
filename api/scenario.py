"""
What-If Scenario Simulator API Router.

Allows operations managers to test counterfactual situations:
- Heavy track machine breakdown (Tamper / Tower Wagon failure)
- Corridor maintenance window duration cuts (traffic demand surge)
- Departmental crew shortages
- Restricting daytime windows (only night maintenance permitted)

Returns side-by-side comparative KPI analysis and operational recommendations.
"""

import time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import pandas as pd

from api.state import state
from optimizer.solver import solve_block_scheduling

router = APIRouter(prefix="/api/scenario", tags=["What-If Scenario Simulator"])


class ScenarioRequest(BaseModel):
    scenario_name: str = Field(default="Custom What-If", description="Name of the scenario")
    scenario_type: str = Field(
        default="equipment_breakdown",
        description="One of: 'equipment_breakdown', 'window_squeeze', 'crew_shortage', 'night_only', 'custom'"
    )
    # Equipment parameters
    disabled_equipment: Optional[List[str]] = Field(
        default=["tamper"],
        description="Equipment types rendered unavailable (e.g. ['tamper'], ['tower'])"
    )
    # Window duration parameters
    window_duration_reduction_pct: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=80.0,
        description="Percentage reduction in available window durations (0-80%)"
    )
    # Night only toggle
    night_only: Optional[bool] = Field(
        default=False,
        description="If True, only night windows (00:00 - 05:00) are permitted"
    )
    # Max block days per section
    max_block_days_per_section: Optional[int] = Field(
        default=3,
        ge=1,
        le=7,
        description="Maximum block days permitted per section per week"
    )


SCENARIO_PRESETS = [
    {
        "id": "tamper_breakdown",
        "name": "Track Tamper Fleet Breakdown",
        "scenario_type": "equipment_breakdown",
        "description": "Both Track Tampers (TM-01, TM-02) undergo unscheduled breakdown. Tests how many deep-screening and tamping tasks can still proceed.",
        "disabled_equipment": ["tamper"],
        "window_duration_reduction_pct": 0,
        "night_only": False,
        "max_block_days_per_section": 3
    },
    {
        "id": "tower_wagon_failure",
        "name": "OHE Tower Wagon Failure",
        "scenario_type": "equipment_breakdown",
        "description": "Tower Wagon electrical maintenance units unavailable. Simulates impact on traction power and catenary block scheduling.",
        "disabled_equipment": ["tower"],
        "window_duration_reduction_pct": 0,
        "night_only": False,
        "max_block_days_per_section": 3
    },
    {
        "id": "window_squeeze_30",
        "name": "Corridor Window Squeeze (-30% Time)",
        "scenario_type": "window_squeeze",
        "description": "High freight surge on Western/Central corridor cuts all available maintenance window lengths by 30%.",
        "disabled_equipment": [],
        "window_duration_reduction_pct": 30.0,
        "night_only": False,
        "max_block_days_per_section": 3
    },
    {
        "id": "night_only_protocol",
        "name": "Strict Night-Only Maintenance Protocol",
        "scenario_type": "night_only",
        "description": "High passenger punctuality protocol restricts all daytime block corridors. Only 00:00 to 05:00 night windows allowed.",
        "disabled_equipment": [],
        "window_duration_reduction_pct": 0,
        "night_only": True,
        "max_block_days_per_section": 3
    }
]


@router.get("/presets")
async def get_scenario_presets():
    """Retrieve predefined counterfactual scenarios for 1-click simulation."""
    return {"presets": SCENARIO_PRESETS}


@router.post("")
@router.post("/simulate")
async def run_scenario_simulation(req: ScenarioRequest):
    """
    Simulate a What-If operational scenario and compare against active baseline schedule.
    """
    if not state["is_ready"] or state["blocks_df"] is None or state["coa_df"] is None:
        raise HTTPException(status_code=400, detail="Pipeline not initialized. POST /api/generate first.")

    t0 = time.time()
    base_stats = state["stats"] or {}
    base_schedule = state["schedule_df"]

    # Clone working datasets
    scenario_blocks = state["blocks_df"].copy()
    scenario_coa = state["coa_df"].copy()
    raw_equip = state["data"].get("equipment") if state.get("data") else None
    scenario_equip = raw_equip.copy() if raw_equip is not None else None

    # Apply Perturbations
    # 1. Equipment constraints
    if req.disabled_equipment and scenario_equip is not None:
        for eq_type in req.disabled_equipment:
            # Mark equipment as Under Repair / Unavailable
            scenario_equip.loc[
                scenario_equip["equipment_type"].str.lower().str.contains(eq_type.lower()),
                "availability"
            ] = "Under Repair"

    # 2. Window duration reduction
    if req.window_duration_reduction_pct > 0:
        factor = 1.0 - (req.window_duration_reduction_pct / 100.0)
        scenario_coa["duration_hours"] = (scenario_coa["duration_hours"] * factor).clip(lower=0.5)

    # 3. Night only protocol
    if req.night_only:
        scenario_coa = scenario_coa[scenario_coa["train_density"] == "night"].copy().reset_index(drop=True)
        if scenario_coa.empty:
            raise HTTPException(status_code=400, detail="No night windows available in current corridor dataset.")

    # 4. Solve Scenario
    crews_df = state["data"].get("crews") if state.get("data") else None
    trains_df = state["data"].get("trains") if state.get("data") else None

    scenario_schedule, scenario_stats = solve_block_scheduling(
        blocks_df=scenario_blocks,
        coa_df=scenario_coa,
        crews_df=crews_df,
        equipment_df=scenario_equip,
        trains_df=trains_df,
        max_block_days_per_section=req.max_block_days_per_section,
        time_limit_seconds=15,
    )

    elapsed_ms = round((time.time() - t0) * 1000, 1)

    # Compute Comparative Metrics (Delta)
    base_blocks_sched = base_stats.get("blocks_scheduled", 0)
    scen_blocks_sched = scenario_stats.get("blocks_scheduled", 0)
    diff_blocks = scen_blocks_sched - base_blocks_sched

    base_util = base_stats.get("block_utilization_pct", 0.0)
    scen_util = scenario_stats.get("block_utilization_pct", 0.0)

    base_avail = base_stats.get("asset_availability_pct", 0.0)
    scen_avail = scenario_stats.get("asset_availability_pct", 0.0)

    # Synthesize Operational Recommendation
    recommendations = []
    if diff_blocks < 0:
        drop_pct = abs(diff_blocks) / max(base_blocks_sched, 1) * 100
        recommendations.append(
            f"Block throughput drops by {drop_pct:.1f}% ({abs(diff_blocks)} fewer blocks scheduled)."
        )
    else:
        recommendations.append("Scenario maintains or improves overall block execution throughput.")

    if req.disabled_equipment:
        recommendations.append(
            f"Requisition emergency auxiliary {' & '.join(req.disabled_equipment)} units from adjacent railway division."
        )

    if req.night_only:
        recommendations.append(
            "Shift crew rosters to nocturnal shift schedules; illuminate high-risk chainages with portable LED towers."
        )

    if req.window_duration_reduction_pct >= 25:
        recommendations.append(
            "High window compression detected: prioritize multi-department bundling to preserve track maintenance quota."
        )

    report = {
        "scenario_name": req.scenario_name,
        "scenario_type": req.scenario_type,
        "simulation_time_ms": elapsed_ms,
        "parameters_applied": {
            "disabled_equipment": req.disabled_equipment,
            "window_reduction_pct": req.window_duration_reduction_pct,
            "night_only": req.night_only,
            "max_block_days_per_section": req.max_block_days_per_section,
        },
        "comparison": {
            "blocks_scheduled": {
                "baseline": base_blocks_sched,
                "scenario": scen_blocks_sched,
                "delta": diff_blocks,
                "pct_change": round((diff_blocks / max(base_blocks_sched, 1)) * 100, 1)
            },
            "total_blocks_available": {
                "baseline": base_stats.get("total_blocks", 0),
                "scenario": scenario_stats.get("total_blocks", 0),
            },
            "block_utilization_pct": {
                "baseline": base_util,
                "scenario": scen_util,
                "delta": round(scen_util - base_util, 1)
            },
            "asset_availability_pct": {
                "baseline": base_avail,
                "scenario": scen_avail,
                "delta": round(scen_avail - base_avail, 1)
            },
            "multi_department_blocks": {
                "baseline": base_stats.get("multi_dept_blocks_scheduled", 0),
                "scenario": scenario_stats.get("multi_dept_blocks_scheduled", 0),
                "delta": scenario_stats.get("multi_dept_blocks_scheduled", 0) - base_stats.get("multi_dept_blocks_scheduled", 0)
            },
            "total_scheduled_hours": {
                "baseline": base_stats.get("total_scheduled_hours", 0.0),
                "scenario": scenario_stats.get("total_scheduled_hours", 0.0),
                "delta": round(scenario_stats.get("total_scheduled_hours", 0.0) - base_stats.get("total_scheduled_hours", 0.0), 1)
            }
        },
        "baseline_stats": base_stats,
        "scenario_stats": scenario_stats,
        "recommendations": recommendations,
        "scenario_schedule_sample": scenario_schedule.head(10).to_dict(orient="records") if not scenario_schedule.empty else [],
    }

    state["last_scenario"] = report
    return report
