"""
Manual Baseline Scheduling Simulation.

Simulates the traditional, decentralized scheduling process:
1. No spatial clustering (each task is scheduled individually).
2. No multi-department integration (each department schedules in isolation).
3. Greedy assignment based on priority or FIFO.
"""

import pandas as pd
from ortools.sat.python import cp_model

def simulate_manual_scheduling(
    tasks_df: pd.DataFrame,
    coa_df: pd.DataFrame,
    max_days: int = 3,
) -> tuple:
    """
    Simulates manual scheduling by assigning individual tasks to windows.
    Returns: (scheduled_df, stats)
    """
    print("=" * 60)
    print("  AI Block Planning - Manual Baseline Simulation")
    print("=" * 60)

    available_windows = coa_df[coa_df["train_density"] != "peak"].copy()
    available_windows = available_windows.reset_index(drop=True)

    # Sort tasks by criticality (manual planners prioritize critical tasks)
    sorted_tasks = tasks_df.sort_values(by="criticality_index", ascending=False).reset_index(drop=True)

    scheduled = []
    window_usage = {w_idx: 0.0 for w_idx in available_windows.index}
    
    # We also have to respect department compatibility for windows, though in manual 
    # it's usually 1 dept per window.
    window_depts = {w_idx: None for w_idx in available_windows.index}

    scheduled_tasks_count = 0
    total_hours_used = 0.0

    for _, task in sorted_tasks.iterrows():
        t_hours = task["required_hours"]
        t_dept = task["department"]
        t_corr = task["corridor"]
        t_sec = task["section"]

        # Find first compatible window that fits
        for w_idx, window in available_windows.iterrows():
            if window["corridor"] != t_corr or window["section"] != t_sec:
                continue

            allowed_dept = window.get("allowed_departments", "All")
            if allowed_dept != "All" and t_dept not in allowed_dept:
                continue

            # In manual scheduling, if a window is used by a department, others usually don't share it
            if window_depts[w_idx] is not None and window_depts[w_idx] != t_dept:
                continue

            # Check capacity with safety buffer
            safety = window.get("safety_buffer_hours", 0.5)
            if window_usage[w_idx] + t_hours + safety <= window["duration_hours"]:
                # Schedule it
                window_usage[w_idx] += t_hours + safety
                window_depts[w_idx] = t_dept
                
                scheduled.append({
                    "task_id": task["task_id"],
                    "window_id": window["window_id"],
                    "corridor": t_corr,
                    "section": t_sec,
                    "department": t_dept,
                    "day_of_week": window["day_of_week"],
                    "task_hours": t_hours,
                    "criticality_index": task["criticality_index"]
                })
                
                scheduled_tasks_count += 1
                total_hours_used += t_hours
                break

    scheduled_df = pd.DataFrame(scheduled)

    total_tasks = len(tasks_df)
    total_window_hours = available_windows["duration_hours"].sum()
    total_corridor_hours = len(coa_df) * coa_df["duration_hours"].mean()
    asset_availability = max(0, (1 - total_hours_used / total_corridor_hours)) * 100
    block_utilization = (total_hours_used / total_window_hours * 100) if total_window_hours > 0 else 0

    stats = {
        "solver_status": "MANUAL",
        "total_tasks": total_tasks,
        "tasks_scheduled": scheduled_tasks_count,
        "tasks_unscheduled": total_tasks - scheduled_tasks_count,
        "schedule_rate_pct": round(scheduled_tasks_count / max(total_tasks, 1) * 100, 1),
        "total_scheduled_hours": round(total_hours_used, 1),
        "total_window_hours": round(total_window_hours, 1),
        "asset_availability_pct": round(asset_availability, 1),
        "block_utilization_pct": round(block_utilization, 1),
        "integration_rate_pct": 0.0,  # 0% integration in manual
        "multi_dept_blocks_scheduled": 0,
        "solve_time_seconds": 0.0,
    }

    print(f"\n  +------------- Manual Baseline Results -------------+")
    print(f"  | Tasks scheduled:     {scheduled_tasks_count:>4} / {total_tasks:<4}  ({stats['schedule_rate_pct']:.0f}%)       |")
    print(f"  | Total hours used:    {total_hours_used:>7.1f} hrs                 |")
    print(f"  | Asset Availability:  {asset_availability:>7.1f}%                   |")
    print(f"  | Block Utilization:   {block_utilization:>7.1f}%                   |")
    print(f"  | Integration Rate:        0.0%                   |")
    print(f"  +-----------------------------------------------------+")
    print(f"{'-' * 60}\n")

    return scheduled_df, stats

if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database.loader import load_data
    from ai_engine.prioritizer import compute_criticality_scores

    data = load_data()
    scored = compute_criticality_scores(data["all_tasks"])
    
    schedule_df, stats = simulate_manual_scheduling(scored, data["coa"])
