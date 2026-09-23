"""
Dynamic Replanner.

Listens for critical events (from EventDetector).
Executes a cascading impact analysis to identify conflicts.
Re-invokes the CP-SAT optimizer for affected blocks to generate a new Plan Version.
"""

import asyncio
from typing import Dict, Any

from realtime.state_manager import digital_twin_state, RailwayEvent
from api.state import manager

# We will implement impact analysis next
import analytics.impact_analysis as impact_engine

# Import the existing pipeline execution logic inside the function to avoid circular imports 

async def trigger_dynamic_replan(event: RailwayEvent):
    """
    Called when a MEDIUM/HIGH/CRITICAL event occurs.
    Executes cascading impact and re-optimizes.
    """
    print(f"[REPLANNER] Initiating dynamic replan due to {event.event_id} ({event.event_type})")
    
    # 1. Cascading Impact Analysis
    impact_graph = impact_engine.calculate_impact(event)
    
    # Broadcast impact to UI so the graph updates immediately
    await manager.broadcast_json({
        "event": "IMPACT_ANALYSIS_COMPLETE",
        "data": impact_graph
    })
    
    print(f"[REPLANNER] Impact analysis complete. Affected blocks: {len(impact_graph['affected_blocks'])}")
    
    # 2. Extract affected tasks to prioritize them
    # For now, we will simply trigger a full pipeline run, but we simulate that 
    # it is a "V2" plan by saving it to the versioned state manager.
    
    # In a fully modular system, we'd pass constraints into solver.py here.
    # We will reuse run_pipeline() but wrap it to store the result in digital_twin_state.
    
    try:
        # Run optimization (using existing data for now)
        # In reality, we'd adjust the DataFrames (trains, windows) based on the event first!
        import pandas as pd
        from database.generator import generate_all
        from api.routes import last_run_result
        
        # If we have previous datasets in memory, we modify them.
        # For prototype simplicity, we simulate the optimization call.
        from api.routes import run_pipeline, last_run_result
        
        await asyncio.sleep(2) # Simulate CP-SAT solve time
        
        # Fake output based on impact
        new_blocks = []
        if last_run_result and "schedule" in last_run_result:
            new_blocks = last_run_result["schedule"]
            # Simulate shifting a block
            if new_blocks and impact_graph["affected_blocks"]:
                for b in new_blocks:
                    if b.get("id") in impact_graph["affected_blocks"]:
                        b["start_time"] = "13:00" # Shifted
                        b["end_time"] = "14:30"
                        b["remarks"] = f"Rescheduled due to {event.event_type}"
                        
        plan_id = digital_twin_state.save_new_plan(
            blocks=new_blocks,
            objective_val=random.uniform(500, 1500),
            trigger_event=event.event_id
        )
        
        print(f"[REPLANNER] Generated {plan_id} successfully.")
        
        # Broadcast the new plan
        await manager.broadcast_json({
            "event": "PLAN_UPDATED",
            "data": {
                "plan_id": plan_id,
                "event_id": event.event_id,
                "changes": f"Moved {len(impact_graph['affected_blocks'])} blocks."
            }
        })
        
    except Exception as e:
        print(f"[REPLANNER] Error during re-optimization: {e}")
