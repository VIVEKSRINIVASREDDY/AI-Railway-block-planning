"""
AI Explainability & Transparency API Router.

Provides deep, transparent reasoning for every task's Criticality Index:
- Multi-factor breakdown (Safety, Operational, Overdue, Speed Class, Exponential Failure Risk)
- XGBoost ML probability vs Heuristic weighted contribution
- Natural language audit explanation
- Associated optimized block & execution window status
"""

import json
from typing import Optional
from fastapi import APIRouter, HTTPException
import pandas as pd

from api.state import state
from ai_engine.prioritizer import WEIGHTS, SPEED_CLASS_SCORES, compute_impact_score, compute_overdue_score, compute_failure_probability

router = APIRouter(prefix="/api", tags=["AI Explainability"])


@router.get("/tasks/{task_id}/explain")
async def explain_task_criticality(task_id: str):
    """
    Return comprehensive, auditable explanation of a maintenance task's criticality score.
    """
    if not state["is_ready"] or state["tasks_df"] is None:
        raise HTTPException(status_code=400, detail="Pipeline not initialized. POST /api/generate first.")

    df = state["tasks_df"]
    matches = df[df["task_id"] == task_id]
    if matches.empty:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found in active maintenance pool.")

    task = matches.iloc[0].to_dict()

    # Raw scores
    safety_score = compute_impact_score(str(task.get("safety_impact", "Low")))
    operational_score = compute_impact_score(str(task.get("operational_impact", "Low")))
    overdue_score = compute_overdue_score(int(task.get("days_overdue", 0)))
    speed_score = SPEED_CLASS_SCORES.get(str(task.get("speed_class", "B")), 50)
    failure_prob = compute_failure_probability(int(task.get("last_maintenance_days", 60)))

    # Weighted contributions
    safety_contrib = round(safety_score * WEIGHTS["safety_impact"], 2)
    operational_contrib = round(operational_score * WEIGHTS["operational_impact"], 2)
    overdue_contrib = round(overdue_score * WEIGHTS["days_overdue"], 2)
    speed_contrib = round(speed_score * WEIGHTS["speed_class"], 2)
    failure_contrib = round(failure_prob * WEIGHTS["failure_probability"], 2)

    heuristic_ci = round(safety_contrib + operational_contrib + overdue_contrib + speed_contrib + failure_contrib, 2)
    xgb_prob = float(task.get("xgb_urgency_prob", 0.5))
    xgb_contrib = round(xgb_prob * 100 * 0.20, 2)
    heuristic_blended = round(heuristic_ci * 0.80, 2)

    final_ci = float(task.get("criticality_index", heuristic_ci))
    priority_tier = str(task.get("priority_tier", "Medium"))

    # Determine assigned block/window if scheduled
    assigned_block = None
    schedule_df = state.get("schedule_df")
    if schedule_df is not None and not schedule_df.empty:
        for _, block in schedule_df.iterrows():
            tids = str(block.get("task_ids", ""))
            if task_id in tids:
                assigned_block = {
                    "block_id": block.get("block_id"),
                    "window_id": block.get("window_id"),
                    "corridor": block.get("corridor"),
                    "section": block.get("section"),
                    "day_of_week": block.get("day_of_week"),
                    "start_hour": block.get("block_start_hour"),
                    "end_hour": block.get("block_end_hour"),
                    "is_multi_department": block.get("is_multi_department", False),
                    "joint_departments": block.get("departments", ""),
                }
                break

    # Build human-readable narrative
    narrative_points = []
    if task.get("emergency", False):
        narrative_points.append("OVERRIDE: Flagged as EMERGENCY incident — elevated unconditionally to maximum priority (100.0).")
    else:
        if safety_score >= 100:
            narrative_points.append("High Safety Threat: Critical safety impact directly drives priority score.")
        if task.get("days_overdue", 0) > 30:
            narrative_points.append(f"Overdue Maintenance: Exceeded standard inspection cycle by {task['days_overdue']} days.")
        if task.get("speed_class") == "A":
            narrative_points.append("High-Speed Corridor: Speed Class 'A' (130 km/h) mandates strict track tolerance.")
        if failure_prob > 60:
            narrative_points.append(f"High Failure Likelihood ({failure_prob:.1f}%): Elevated risk based on {task.get('last_maintenance_days', 0)} days elapsed since last maintenance.")

    narrative = " ".join(narrative_points) if narrative_points else "Standard routine maintenance task with nominal priority indicators."

    return {
        "task_id": task_id,
        "department": task.get("department"),
        "defect_type": task.get("defect_type"),
        "description": task.get("description"),
        "corridor": task.get("corridor"),
        "section": task.get("section"),
        "chainage_km": task.get("chainage_km"),
        "criticality_index": final_ci,
        "priority_tier": priority_tier,
        "is_emergency": bool(task.get("emergency", False)),
        "is_mandatory": bool(task.get("mandatory", False)),
        "factor_breakdown": {
            "safety": {
                "raw_value": task.get("safety_impact"),
                "score": safety_score,
                "weight_pct": int(WEIGHTS["safety_impact"] * 100),
                "contribution_points": safety_contrib,
            },
            "operational": {
                "raw_value": task.get("operational_impact"),
                "score": operational_score,
                "weight_pct": int(WEIGHTS["operational_impact"] * 100),
                "contribution_points": operational_contrib,
            },
            "overdue": {
                "raw_value": f"{task.get('days_overdue')} days",
                "score": round(overdue_score, 1),
                "weight_pct": int(WEIGHTS["days_overdue"] * 100),
                "contribution_points": overdue_contrib,
            },
            "speed_class": {
                "raw_value": f"Class {task.get('speed_class')}",
                "score": speed_score,
                "weight_pct": int(WEIGHTS["speed_class"] * 100),
                "contribution_points": speed_contrib,
            },
            "failure_probability": {
                "raw_value": f"{task.get('last_maintenance_days')} days elapsed",
                "score": round(failure_prob, 1),
                "weight_pct": int(WEIGHTS["failure_probability"] * 100),
                "contribution_points": failure_contrib,
            },
        },
        "blend_breakdown": {
            "heuristic_component_80pct": heuristic_blended,
            "xgboost_component_20pct": xgb_contrib,
            "xgboost_raw_probability": xgb_prob,
        },
        "audit_narrative": narrative,
        "schedule_status": {
            "scheduled": assigned_block is not None,
            "assignment": assigned_block,
        }
    }


@router.get("/explainability/summary")
async def get_explainability_summary():
    """
    Return global explainability breakdown across all tasks in the active plan.
    """
    if not state["is_ready"] or state["tasks_df"] is None:
        raise HTTPException(status_code=400, detail="Pipeline not initialized. POST /api/generate first.")

    df = state["tasks_df"]
    tier_counts = df["priority_tier"].value_counts().to_dict() if "priority_tier" in df.columns else {}
    dept_counts = df["department"].value_counts().to_dict() if "department" in df.columns else {}

    # Average criticality by department
    dept_avg_ci = df.groupby("department")["criticality_index"].mean().round(1).to_dict() if "criticality_index" in df.columns else {}

    # Top 5 most critical tasks
    top_critical = []
    if "criticality_index" in df.columns:
        sorted_top = df.sort_values(by="criticality_index", ascending=False).head(5)
        for _, row in sorted_top.iterrows():
            top_critical.append({
                "task_id": row["task_id"],
                "department": row["department"],
                "defect_type": row["defect_type"],
                "section": row["section"],
                "chainage_km": row.get("chainage_km", 0.0),
                "criticality_index": row["criticality_index"],
                "priority_tier": str(row.get("priority_tier", "High")),
            })

    return {
        "total_tasks": len(df),
        "priority_distribution": {str(k): v for k, v in tier_counts.items()},
        "department_task_distribution": dept_counts,
        "department_avg_criticality": dept_avg_ci,
        "weights_configuration": {k: f"{int(v*100)}%" for k, v in WEIGHTS.items()},
        "top_critical_tasks": top_critical,
    }
