"""
Resilience Analytics Engine.

Calculates the resilience score of the railway maintenance system.
Resilience is a mathematical combination of:
1. Recovery Time (how fast a new schedule is formulated)
2. Conflict Resolution Rate
3. Plan Stability (how many blocks were NOT moved)
"""

from typing import Dict
from realtime.state_manager import digital_twin_state

def compute_resilience_score() -> Dict[str, float]:
    """
    Computes a 0-100 score of how resilient the current operating plan is.
    """
    if len(digital_twin_state.plan_history) < 2:
        return {
            "overall_score": None,
            "stability": None,
            "recovery_efficiency": None,
            "has_incident": False,
            "message": "N/A — Baseline schedule active. Awaiting disruption injection."
        }
        
    latest_plan = digital_twin_state.plan_history[-1]
    prev_plan = digital_twin_state.plan_history[-2]
    
    # 1. Stability: % of blocks that didn't change duration/time
    prev_blocks = {b["id"]: b for b in prev_plan.schedule_snapshot if "id" in b}
    latest_blocks = {b["id"]: b for b in latest_plan.schedule_snapshot if "id" in b}
    
    if not prev_blocks:
        stability = 100.0
    else:
        unchanged = 0
        for b_id, b_data in latest_blocks.items():
            if b_id in prev_blocks:
                p_data = prev_blocks[b_id]
                if b_data.get("start_time") == p_data.get("start_time"):
                    unchanged += 1
        stability = (unchanged / len(prev_blocks)) * 100
        
    # 2. Recovery Efficiency: Did we drop blocks?
    if prev_plan.blocks_scheduled == 0:
        recovery = 100.0
    else:
        recovery = (latest_plan.blocks_scheduled / prev_plan.blocks_scheduled) * 100
        recovery = min(100.0, recovery)
        
    # 3. Overall Resilience
    # Weighting: 60% recovery (ability to schedule), 40% stability (lack of chaos)
    overall = (recovery * 0.6) + (stability * 0.4)
    
    return {
        "overall_score": round(overall, 1),
        "stability": round(stability, 1),
        "recovery_efficiency": round(recovery, 1),
        "message": f"Recovered {latest_plan.blocks_scheduled} blocks with {round(stability, 1)}% plan stability."
    }
