"""
Emergency Dynamic Replanning API Router.

Enables instant injection of critical track/OHE/signal incidents,
rapid re-clustering, and constraint-based re-optimization.
Computes before/after plan diffs and displaced blocks.
"""

import json
import random
import time
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import pandas as pd

from api.state import state, manager
from ai_engine.clustering import cluster_tasks
from optimizer.solver import solve_block_scheduling
from config.settings import SCHEDULE_CSV, BLOCKS_CSV, SCORED_TASKS_CSV, STATS_JSON

router = APIRouter(prefix="/api", tags=["Emergency Replanning"])


class EmergencyRequest(BaseModel):
    incident_type: str = Field(..., description="e.g. Broken Rail, OHE Wire Snap, Signal Failure, Point Machine Fault")
    km_marker: float = Field(..., ge=0, le=300, description="Kilometer location of incident")
    corridor: str = Field(default="Mumbai-Pune", description="Railway corridor")
    section: Optional[str] = Field(default=None, description="Section, e.g. CSMT-KYN")
    severity: str = Field(default="CRITICAL", description="CRITICAL, HIGH, or MEDIUM")
    required_hours: float = Field(default=3.0, ge=0.5, le=8.0, description="Hours required for emergency rectification")
    required_equipment: Optional[str] = Field(default=None, description="Equipment needed (tamper, tower, etc.)")
    description: Optional[str] = Field(default=None, description="Details of emergency incident")


def _deduce_section(km: float) -> str:
    """Map chainage km to Mumbai-Pune corridor sections."""
    if km <= 55:
        return "CSMT-KYN"
    elif km <= 120:
        return "KYN-IGP"
    elif km <= 180:
        return "IGP-NSK"
    elif km <= 185:
        return "NSK-DWD"
    else:
        return "DWD-MMR"


def _deduce_department_and_equip(incident_type: str, custom_equip: Optional[str]):
    inc_lower = incident_type.lower()
    if any(k in inc_lower for k in ["ohe", "wire", "power", "catenary", "substation", "pantograph"]):
        dept = "Electrical"
        default_eq = "tower"
    elif any(k in inc_lower for k in ["signal", "point", "interlocking", "circuit", "axle", "relay"]):
        dept = "S&T"
        default_eq = "signal"
    else:
        dept = "Engineering"
        default_eq = "tamper"

    equip = custom_equip or default_eq
    return dept, equip


@router.post("/emergency")
@router.post("/inject-incident")
async def trigger_emergency_replan(req: EmergencyRequest):
    """
    Inject an emergency incident into the system and execute dynamic replanning.
    Returns:
      - Emergency task details
      - Assigned emergency block and corridor window
      - Schedule diff (displaced blocks, unaffected blocks, new blocks)
      - Updated system KPIs
    """
    if not state["is_ready"] or state["tasks_df"] is None or state["coa_df"] is None:
        raise HTTPException(status_code=400, detail="Pipeline not initialized. POST /api/generate first.")

    t0 = time.time()
    section = req.section or _deduce_section(req.km_marker)
    dept, equip = _deduce_department_and_equip(req.incident_type, req.required_equipment)

    task_id = f"EMG-{dept[:3].upper()}-{int(time.time() % 100000):05d}"
    incident_desc = req.description or f"EMERGENCY: {req.incident_type} reported at Km {req.km_marker:.1f} ({section})"

    # Construct the emergency task record
    explanation = {
        "reason": f"UNSCHEDULED EMERGENCY: {req.incident_type}",
        "safety_impact": "100 (Critical Safety Threat)",
        "operational_impact": "100 (Track Blockage/Restriction Required)",
        "overdue_score": "100 (Immediate Action Mandatory)",
        "speed_score": "100 (Class A Corridor)",
        "failure_risk": "100 (Active Disruption)",
        "disruption_class": "Immediate Safety Intervention"
    }

    new_task = {
        "task_id": task_id,
        "asset_id": f"AST-{dept[:3].upper()}-{int(req.km_marker):03d}",
        "department": dept,
        "corridor": req.corridor,
        "section": section,
        "chainage_km": req.km_marker,
        "latitude": 18.9398 + (req.km_marker / 256.0) * (20.2509 - 18.9398),
        "longitude": 72.8355 + (req.km_marker / 256.0) * (74.4398 - 72.8355),
        "defect_type": req.incident_type,
        "description": incident_desc,
        "severity": 5,
        "safety_impact": "High",
        "operational_impact": "High",
        "speed_class": "A",
        "days_overdue": 30,
        "required_hours": req.required_hours,
        "estimated_duration": req.required_hours,
        "reported_date": "2026-09-14",
        "last_maintenance_days": 180,
        "required_crew": 4,
        "required_equipment": equip,
        "mandatory": True,
        "emergency": True,
        "status": "EMERGENCY_OPEN",
        "dependency": "",
        "heuristic_ci": 100.0,
        "score_explanation": json.dumps(explanation),
        "xgb_urgency_prob": 1.0,
        "criticality_index": 100.0,
        "priority_tier": "Critical",
    }

    # Backup previous schedule for diff comparison
    old_schedule_df = state["schedule_df"].copy() if state["schedule_df"] is not None else pd.DataFrame()
    old_blocks_df = state["blocks_df"].copy() if state["blocks_df"] is not None else pd.DataFrame()

    # Append to current tasks DataFrame
    tasks_df = state["tasks_df"].copy()
    new_task_df = pd.DataFrame([new_task])
    for col in tasks_df.columns:
        if col not in new_task_df.columns:
            new_task_df[col] = None
    combined_tasks = pd.concat([tasks_df, new_task_df[tasks_df.columns]], ignore_index=True)

    # Fast re-clustering
    blocks_df, tasks_clustered = cluster_tasks(combined_tasks)

    # Re-optimize with full constraints
    crews_df = state["data"].get("crews") if state.get("data") else None
    equipment_df = state["data"].get("equipment") if state.get("data") else None
    trains_df = state["data"].get("trains") if state.get("data") else None

    schedule_df, stats = solve_block_scheduling(
        blocks_df=blocks_df,
        coa_df=state["coa_df"],
        crews_df=crews_df,
        equipment_df=equipment_df,
        trains_df=trains_df,
        time_limit_seconds=10,
    )

    elapsed_ms = round((time.time() - t0) * 1000, 1)

    # Locate assigned block for the emergency task
    emergency_block_id = None
    emergency_window_id = None
    emergency_block_details = None

    if not schedule_df.empty:
        for _, row in schedule_df.iterrows():
            tids = str(row.get("task_ids", ""))
            if task_id in tids:
                emergency_block_id = row.get("block_id")
                emergency_window_id = row.get("window_id")
                emergency_block_details = row.to_dict()
                break

    # Calculate schedule diff
    displaced_blocks = []
    unaffected_count = 0

    if not old_schedule_df.empty and not schedule_df.empty:
        old_map = {r["block_id"]: r["window_id"] for _, r in old_schedule_df.iterrows()}
        new_map = {r["block_id"]: r["window_id"] for _, r in schedule_df.iterrows()}

        for b_id, old_w in old_map.items():
            if b_id not in new_map:
                # Block was dropped or unscheduled due to emergency priority
                displaced_blocks.append({
                    "block_id": b_id,
                    "previous_window": old_w,
                    "new_window": "UNSCHEDULED (Displaced by Emergency)",
                    "status": "UNSCHEDULED"
                })
            elif new_map[b_id] != old_w:
                # Block was shifted to a different window
                displaced_blocks.append({
                    "block_id": b_id,
                    "previous_window": old_w,
                    "new_window": new_map[b_id],
                    "status": "RESCHEDULED"
                })
            else:
                unaffected_count += 1

    # Update system state
    state["schedule_df"] = schedule_df
    state["tasks_df"] = tasks_clustered
    state["blocks_df"] = blocks_df
    state["stats"] = stats

    # Persist changes to disk so they are saved permanently
    try:
        if schedule_df is not None and not schedule_df.empty:
            schedule_df.to_csv(SCHEDULE_CSV, index=False)
        if blocks_df is not None and not blocks_df.empty:
            blocks_df.to_csv(BLOCKS_CSV, index=False)
        if tasks_clustered is not None and not tasks_clustered.empty:
            tasks_clustered.to_csv(SCORED_TASKS_CSV, index=False)
        if stats:
            with open(STATS_JSON, "w") as f:
                json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"[EMERGENCY] Warning: could not persist to disk: {e}")

    history_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "incident_type": req.incident_type,
        "km_marker": req.km_marker,
        "corridor": req.corridor,
        "section": section,
        "emergency_task_id": task_id,
        "emergency_block_id": emergency_block_id,
        "window_assigned": emergency_window_id,
        "displaced_blocks_count": len(displaced_blocks),
        "computation_time_ms": elapsed_ms,
        "status": "RESOLVED" if emergency_block_id else "FAILED_TO_SCHEDULE",
    }
    state["emergency_history"].insert(0, history_entry)

    # Broadcast WebSocket updates for all listening components
    await manager.broadcast(json.dumps({
        "event": "incident_injected",
        "incident_type": req.incident_type,
        "km_marker": req.km_marker,
        "severity": req.severity,
        "section": section,
        "stats": stats,
    }))
    await manager.broadcast(json.dumps({
        "event": "pipeline_updated",
        "stats": stats,
    }))
    await manager.broadcast(json.dumps({
        "event": "emergency_replanned",
        "emergency": history_entry,
        "stats": stats,
    }))

    return {
        "status": "success",
        "message": f"Emergency replanning completed in {elapsed_ms}ms.",
        "emergency_task": new_task,
        "emergency_assignment": emergency_block_details,
        "diff": {
            "emergency_scheduled": emergency_block_id is not None,
            "emergency_block_id": emergency_block_id,
            "window_id": emergency_window_id,
            "displaced_blocks": displaced_blocks,
            "displaced_count": len(displaced_blocks),
            "unaffected_blocks_count": unaffected_count,
            "total_blocks_scheduled": stats.get("blocks_scheduled", 0),
        },
        "stats": stats,
        "replanning_time_ms": elapsed_ms,
    }


@router.get("/emergency/history")
async def get_emergency_history():
    """Return historical log of emergency injections and dynamic replan results."""
    return {
        "count": len(state["emergency_history"]),
        "history": state["emergency_history"],
    }
