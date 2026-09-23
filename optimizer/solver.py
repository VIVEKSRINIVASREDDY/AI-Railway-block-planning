"""
Constraint-Based Optimization Engine using Google OR-Tools CP-SAT.

Solves the block-window assignment problem:
  - Decision: Which integrated blocks to schedule in which corridor windows.
  - Objective: Maximize total criticality-weighted coverage.
  - Constraints: Capacity, spatial compatibility, peak avoidance, weekly balance,
                 department compatibility, equipment availability, train conflicts.
"""

from dataclasses import dataclass
import pandas as pd
from ortools.sat.python import cp_model


@dataclass
class ScheduledBlock:
    """A block that has been assigned to a specific corridor window."""
    block_id: str
    window_id: str
    corridor: str
    section: str
    day_of_week: str
    window_start_hour: float
    window_end_hour: float
    block_start_hour: float
    block_end_hour: float
    total_hours: float
    max_criticality: float
    avg_criticality: float
    task_count: int
    departments: str
    is_multi_department: bool
    task_ids: str
    km_range_start: float
    km_range_end: float
    required_equipment: str
    has_mandatory: bool
    has_emergency: bool

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def solve_block_scheduling(
    blocks_df: pd.DataFrame,
    coa_df: pd.DataFrame,
    crews_df: pd.DataFrame = None,
    equipment_df: pd.DataFrame = None,
    materials_df: pd.DataFrame = None,
    trains_df: pd.DataFrame = None,
    max_block_days_per_section: int = 3,
    time_limit_seconds: int = 30,
    multi_dept_bonus: int = 15,
) -> tuple:
    """
    Solve the block-to-window assignment problem using CP-SAT.
    """
    print("=" * 60)
    print("  AI Block Planning - OR-Tools CP-SAT Optimizer")
    print("=" * 60)

    # ── Filter out peak windows ──
    available_windows = coa_df[coa_df["train_density"] != "peak"].copy()
    available_windows = available_windows.reset_index(drop=True)

    print(f"\n  Blocks to schedule:    {len(blocks_df)}")
    print(f"  Available windows:     {len(available_windows)} (peak excluded)")
    print(f"  Time limit:            {time_limit_seconds}s")

    # Prepare equipment capacity dict
    equipment_capacity = {}
    if equipment_df is not None and not equipment_df.empty:
        # Count available equipment by type
        available_eq = equipment_df[equipment_df["availability"] == "Available"]
        equip_grouped = available_eq.groupby("equipment_type").size().to_dict()
        equipment_capacity = equip_grouped

    # ── Precompute compatibility ──
    print("\n  Computing block-window compatibility matrix...")

    compatible_pairs = []
    for b_idx, block in blocks_df.iterrows():
        b_departments = set(block["departments"].split(",")) if isinstance(block["departments"], str) else set(block["departments"])
        b_hours = block["total_hours"]

        for w_idx, window in available_windows.iterrows():
            if block["corridor"] != window["corridor"]:
                continue
            if block["section"] != window["section"]:
                continue
            
            # Duration constraint: Block hours + Safety buffer <= Window duration
            safety_buffer = window.get("safety_buffer_hours", 0.5)
            if b_hours + safety_buffer > window["duration_hours"] + 0.1:
                continue
                
            # Department compatibility
            allowed_dept = window.get("allowed_departments", "All")
            if allowed_dept != "All":
                allowed_set = set(allowed_dept.split(","))
                # If block has a department NOT allowed in this window
                if not b_departments.issubset(allowed_set):
                    continue

            compatible_pairs.append((b_idx, w_idx))

    print(f"  Compatible (block, window) pairs: {len(compatible_pairs)}")

    if len(compatible_pairs) == 0:
        print("  [WARN] No compatible block-window pairs found!")
        return pd.DataFrame(), _empty_stats()

    # ── Build CP-SAT Model ──
    print("\n  Building constraint programming model...")
    model = cp_model.CpModel()

    # Decision variables: x[b][w] = 1 if block b assigned to window w
    x = {}
    for b_idx, w_idx in compatible_pairs:
        x[(b_idx, w_idx)] = model.NewBoolVar(f"x_b{b_idx}_w{w_idx}")

    # ── Constraint 1: Each block assigned to at most one window ──
    block_indices = blocks_df.index.tolist()
    for b_idx in block_indices:
        block_windows = [w_idx for (bi, w_idx) in compatible_pairs if bi == b_idx]
        if block_windows:
            model.AddAtMostOne([x[(b_idx, w_idx)] for w_idx in block_windows])

    # ── Constraint 2: Window capacity ──
    # Sum of block durations in a window must be <= window duration (accounting for safety buffers)
    for w_idx in set(w for _, w in compatible_pairs):
        window_blocks = [b_idx for (b_idx, wi) in compatible_pairs if wi == w_idx]
        if window_blocks:
            window_cap = int(available_windows.loc[w_idx, "duration_hours"] * 10)
            safety = int(available_windows.loc[w_idx, "safety_buffer_hours"] * 10)
            
            model.Add(
                sum(
                    x[(b_idx, w_idx)] * int(blocks_df.loc[b_idx, "total_hours"] * 10 + safety)
                    for b_idx in window_blocks
                ) <= window_cap
            )

    # ── Constraint 3: Equipment limits per window ──
    # Approximates resource conflict: you cannot use more equipment of type E in the same window than exists
    if equipment_capacity:
        for w_idx in set(w for _, w in compatible_pairs):
            window_blocks = [b_idx for (b_idx, wi) in compatible_pairs if wi == w_idx]
            if not window_blocks:
                continue
                
            for equip_type, capacity in equipment_capacity.items():
                blocks_using_equip = []
                for b_idx in window_blocks:
                    eq_list = blocks_df.loc[b_idx].get("required_equipment", "")
                    if isinstance(eq_list, list) and equip_type in eq_list:
                        blocks_using_equip.append(x[(b_idx, w_idx)])
                    elif isinstance(eq_list, str) and equip_type in eq_list:
                        blocks_using_equip.append(x[(b_idx, w_idx)])
                        
                if blocks_using_equip:
                    model.Add(sum(blocks_using_equip) <= capacity)

    # ── Constraint 4: Weekly balance ──
    sections = blocks_df["section"].unique()
    days = available_windows["day_of_week"].unique()
    for section in sections:
        section_pairs = [
            (b_idx, w_idx)
            for (b_idx, w_idx) in compatible_pairs
            if blocks_df.loc[b_idx, "section"] == section
        ]
        if len(section_pairs) > max_block_days_per_section:
            model.Add(
                sum(x[(b_idx, w_idx)] for b_idx, w_idx in section_pairs)
                <= max_block_days_per_section * len(days)
            )

    # ── Objective: Maximize criticality-weighted coverage ──
    objective_terms = []
    for b_idx, w_idx in compatible_pairs:
        priority = int(blocks_df.loc[b_idx, "max_criticality"] * 10)

        # Multi-department bonus
        if blocks_df.loc[b_idx, "is_multi_department"]:
            priority += multi_dept_bonus * 10

        # Mandatory & Emergency bonus
        if blocks_df.loc[b_idx].get("has_emergency", False):
            priority += 5000  # huge weight
        elif blocks_df.loc[b_idx].get("has_mandatory", False):
            priority += 2000

        # Night window bonus
        if available_windows.loc[w_idx, "train_density"] == "night":
            priority += 5 * 10

        objective_terms.append(x[(b_idx, w_idx)] * priority)

    model.Maximize(sum(objective_terms))

    # ── Solve ──
    print("  Solving...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 4

    status = solver.Solve(model)
    status_name = solver.StatusName(status)
    print(f"  Solver status: {status_name}")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("  [WARN] No feasible solution found!")
        return pd.DataFrame(), _empty_stats()

    # ── Extract solution ──
    scheduled = []
    scheduled_block_ids = set()
    total_scheduled_hours = 0

    for b_idx, w_idx in compatible_pairs:
        if solver.Value(x[(b_idx, w_idx)]) == 1:
            block = blocks_df.loc[b_idx]
            window = available_windows.loc[w_idx]

            block_start = window["window_start_hour"]
            block_end = block_start + block["total_hours"]

            # Format departments/equipment properly if it's a list
            depts = block["departments"]
            if isinstance(depts, list):
                depts = ",".join(depts)
                
            eqs = block.get("required_equipment", "")
            if isinstance(eqs, list):
                eqs = ",".join(eqs)

            sb = ScheduledBlock(
                block_id=block["block_id"],
                window_id=window["window_id"],
                corridor=block["corridor"],
                section=block["section"],
                day_of_week=window["day_of_week"],
                window_start_hour=window["window_start_hour"],
                window_end_hour=window["window_end_hour"],
                block_start_hour=round(block_start, 2),
                block_end_hour=round(block_end, 2),
                total_hours=block["total_hours"],
                max_criticality=block["max_criticality"],
                avg_criticality=block["avg_criticality"],
                task_count=block["task_count"],
                departments=depts,
                is_multi_department=block["is_multi_department"],
                task_ids=",".join(block["task_ids"]) if isinstance(block["task_ids"], list) else block["task_ids"],
                km_range_start=block["km_range_start"],
                km_range_end=block["km_range_end"],
                required_equipment=eqs,
                has_mandatory=block.get("has_mandatory", False),
                has_emergency=block.get("has_emergency", False),
            )
            scheduled.append(sb)
            scheduled_block_ids.add(block["block_id"])
            total_scheduled_hours += block["total_hours"]

    scheduled_df = pd.DataFrame([s.to_dict() for s in scheduled])

    # ── Compute KPIs ──
    total_blocks = len(blocks_df)
    num_scheduled = len(scheduled_block_ids)
    total_tasks = int(blocks_df["task_count"].sum())
    scheduled_tasks = int(scheduled_df["task_count"].sum()) if len(scheduled_df) > 0 else 0

    total_window_hours = available_windows["duration_hours"].sum()
    total_corridor_hours = len(coa_df) * coa_df["duration_hours"].mean()
    asset_availability = max(0, (1 - total_scheduled_hours / total_corridor_hours)) * 100
    block_utilization = (total_scheduled_hours / total_window_hours * 100) if total_window_hours > 0 else 0

    multi_dept_scheduled = sum(1 for s in scheduled if s.is_multi_department)
    integration_rate = (multi_dept_scheduled / max(num_scheduled, 1)) * 100

    stats = {
        "solver_status": status_name,
        "objective_value": solver.ObjectiveValue(),
        "total_blocks": total_blocks,
        "blocks_scheduled": num_scheduled,
        "blocks_unscheduled": total_blocks - num_scheduled,
        "total_tasks": total_tasks,
        "tasks_scheduled": scheduled_tasks,
        "tasks_unscheduled": total_tasks - scheduled_tasks,
        "schedule_rate_pct": round(num_scheduled / max(total_blocks, 1) * 100, 1),
        "total_scheduled_hours": round(total_scheduled_hours, 1),
        "total_window_hours": round(total_window_hours, 1),
        "asset_availability_pct": round(asset_availability, 1),
        "block_utilization_pct": round(block_utilization, 1),
        "integration_rate_pct": round(integration_rate, 1),
        "multi_dept_blocks_scheduled": multi_dept_scheduled,
        "solve_time_seconds": round(solver.WallTime(), 2),
    }

    print(f"\n  +--------------- Optimization Results ---------------+")
    print(f"  | Blocks scheduled:    {num_scheduled:>4} / {total_blocks:<4}  ({stats['schedule_rate_pct']:.0f}%)       |")
    print(f"  | Tasks scheduled:     {scheduled_tasks:>4} / {total_tasks:<4}                  |")
    print(f"  | Total hours used:    {total_scheduled_hours:>7.1f} hrs                 |")
    print(f"  | Asset Availability:  {asset_availability:>7.1f}%                   |")
    print(f"  | Block Utilization:   {block_utilization:>7.1f}%                   |")
    print(f"  | Integration Rate:    {integration_rate:>7.1f}%                   |")
    print(f"  | Solve time:          {solver.WallTime():>7.2f}s                    |")
    print(f"  +-----------------------------------------------------+")
    print(f"{'-' * 60}\n")

    return scheduled_df, stats


def _empty_stats() -> dict:
    return {
        "solver_status": "INFEASIBLE",
        "objective_value": 0,
        "total_blocks": 0,
        "blocks_scheduled": 0,
        "blocks_unscheduled": 0,
        "total_tasks": 0,
        "tasks_scheduled": 0,
        "tasks_unscheduled": 0,
        "schedule_rate_pct": 0,
        "total_scheduled_hours": 0,
        "total_window_hours": 0,
        "asset_availability_pct": 0,
        "block_utilization_pct": 0,
        "integration_rate_pct": 0,
        "multi_dept_blocks_scheduled": 0,
        "solve_time_seconds": 0,
    }


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database.loader import load_data
    from ai_engine.prioritizer import compute_criticality_scores
    from ai_engine.clustering import cluster_tasks

    data = load_data()
    scored = compute_criticality_scores(data["all_tasks"])
    blocks_df, _ = cluster_tasks(scored)
    
    # Pass equipment_df if available
    schedule_df, stats = solve_block_scheduling(
        blocks_df, 
        data["coa"],
        equipment_df=data.get("equipment")
    )

    print("\nScheduled Blocks (first 10):")
    if len(schedule_df) > 0:
        print(schedule_df[["block_id", "window_id", "corridor", "section",
                           "day_of_week", "block_start_hour", "block_end_hour",
                           "departments"]].head(10).to_string())
