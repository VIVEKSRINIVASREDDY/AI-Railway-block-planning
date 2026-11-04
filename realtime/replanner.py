# -*- coding: utf-8 -*-
"""
Dynamic Replanner.

Listens for critical events (from EventDetector).
Executes a cascading impact analysis to identify conflicts.
Re-invokes the CP-SAT optimizer for affected blocks to generate a new Plan Version.
"""

import asyncio
import json
import time
from typing import Dict, Any

from realtime.state_manager import digital_twin_state, RailwayEvent
from api.state import manager, state as app_state

# Impact analysis engine
import analytics.impact_analysis as impact_engine


async def trigger_dynamic_replan(event: RailwayEvent):
    """
    Called when a MEDIUM/HIGH/CRITICAL event occurs.
    Executes cascading impact analysis, modifies corridor constraints,
    and re-invokes the CP-SAT optimizer to produce an updated block plan.
    """
    start_time = time.time()
    print(f"[REPLANNER] Initiating dynamic replan due to {event.event_id} ({event.event_type})")

    # 1. Cascading Impact Analysis
    impact_graph = impact_engine.calculate_impact(event)

    # Broadcast impact to UI so the graph updates immediately
    await manager.broadcast(json.dumps({
        "event": "IMPACT_ANALYSIS_COMPLETE",
        "data": impact_graph
    }))

    affected_block_count = len(impact_graph.get("affected_blocks", []))
    print(f"[REPLANNER] Impact analysis complete. Affected blocks: {affected_block_count}")

    # 2. Re-invoke the CP-SAT optimizer with modified constraints
    try:
        # Import pipeline components here to avoid circular imports at module level
        from database.loader import load_data
        from ai_engine.prioritizer import compute_criticality_scores
        from ai_engine.clustering import cluster_tasks
        from optimizer.solver import solve_block_scheduling

        # Use existing data from the API state if available; otherwise reload from disk
        data = app_state.get("data")
        if data is None:
            data = load_data()

        # Re-score tasks (criticality may have changed due to the event)
        scored = compute_criticality_scores(data["all_tasks"])

        # Re-cluster
        blocks_df, tasks_clustered = cluster_tasks(scored)

        # Modify corridor windows (COA) based on the event:
        # - For WEATHER_ALERT: reduce available windows on affected sections
        # - For TRAIN_DELAYED: shrink windows around the delayed train's path
        coa_df = data["coa"].copy()
        coa_df = _apply_event_constraints(coa_df, event, impact_graph)

        # Re-solve with modified constraints
        print(f"[REPLANNER] Re-invoking CP-SAT solver with modified constraints...")
        schedule_df, stats = solve_block_scheduling(
            blocks_df=blocks_df,
            coa_df=coa_df,
            crews_df=data.get("crews"),
            equipment_df=data.get("equipment"),
            trains_df=data.get("trains"),
        )

        elapsed = round(time.time() - start_time, 2)
        stats["replan_trigger_event"] = event.event_id
        stats["replan_elapsed_seconds"] = elapsed

        # 3. Save versioned plan to digital twin state
        schedule_records = []
        if len(schedule_df) > 0:
            schedule_records = json.loads(schedule_df.to_json(orient="records"))

        plan_id = digital_twin_state.save_new_plan(
            blocks=schedule_records,
            objective_val=stats.get("objective_value", 0),
            trigger_event=event.event_id
        )

        print(f"[REPLANNER] Generated {plan_id} in {elapsed}s. "
              f"Scheduled {stats['blocks_scheduled']}/{stats['total_blocks']} blocks.")

        # 4. Update API state so frontend picks up the new plan immediately
        app_state["schedule_df"] = schedule_df
        app_state["tasks_df"] = tasks_clustered
        app_state["blocks_df"] = blocks_df
        app_state["stats"] = stats

        # 5. Broadcast the new plan to all connected WebSocket clients
        await manager.broadcast(json.dumps({
            "event": "PLAN_UPDATED",
            "data": {
                "plan_id": plan_id,
                "event_id": event.event_id,
                "stats": stats,
                "elapsed_seconds": elapsed,
                "changes": f"Rescheduled {stats['blocks_scheduled']} blocks due to {event.event_type}."
            }
        }))

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        print(f"[REPLANNER] Error during re-optimization ({elapsed}s): {e}")

        # Broadcast failure so the UI can alert the controller
        await manager.broadcast(json.dumps({
            "event": "REPLAN_FAILED",
            "data": {
                "event_id": event.event_id,
                "error": str(e),
                "elapsed_seconds": elapsed,
            }
        }))


def _apply_event_constraints(coa_df, event: RailwayEvent, impact_graph: Dict) -> "pd.DataFrame":
    """
    Modify corridor windows (COA) based on a disruption event.

    - WEATHER_ALERT: Remove or shrink windows on affected sections for the current day.
    - TRAIN_DELAYED: Reduce window capacity on sections where delayed trains operate.
    - Other events: Reduce durations by a safety factor on affected sections.
    """
    import pandas as pd

    affected_sections = set()

    # Extract affected section names from the impact graph nodes
    for node in impact_graph.get("nodes", []):
        if node.get("type") == "section":
            affected_sections.add(node.get("label", ""))

    if event.event_type == "WEATHER_ALERT":
        # Weather events: reduce available hours on affected sections by 30%
        # (simulating safety restrictions during adverse conditions)
        if affected_sections:
            mask = coa_df["section"].isin(affected_sections)
            coa_df.loc[mask, "duration_hours"] = (
                coa_df.loc[mask, "duration_hours"] * 0.7
            ).round(2)
        else:
            # If no specific section info, apply a small global reduction
            today = time.strftime("%A")
            day_mask = coa_df["day_of_week"] == today
            coa_df.loc[day_mask, "duration_hours"] = (
                coa_df.loc[day_mask, "duration_hours"] * 0.85
            ).round(2)

    elif event.event_type == "TRAIN_DELAYED":
        # Delayed trains may create cascading conflicts; reduce window
        # capacity on the corridor by a modest amount to provide buffer
        if affected_sections:
            mask = coa_df["section"].isin(affected_sections)
            coa_df.loc[mask, "duration_hours"] = (
                coa_df.loc[mask, "duration_hours"] * 0.8
            ).round(2)

    else:
        # Generic event: apply a conservative 10% reduction
        if affected_sections:
            mask = coa_df["section"].isin(affected_sections)
            coa_df.loc[mask, "duration_hours"] = (
                coa_df.loc[mask, "duration_hours"] * 0.9
            ).round(2)

    return coa_df
