"""
Independent Schedule Validator for Indian Railways Block Planning.
===================================================================
CRITICAL SAFETY RULE:
This module contains ZERO imports from OR-Tools or any constraint solver.
It acts as an independent adversarial auditor that re-evaluates the final
schedule DataFrame from first principles against Indian Railways hard constraints.

A plan CANNOT be approved, and no Sanction Order may be dispatched, unless
this validator passes with zero violations.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


class ScheduleValidationReport:
    """Detailed audit report produced by the Independent Validator."""
    def __init__(self):
        self.is_valid: bool = True
        self.total_blocks_checked: int = 0
        self.total_constraints_checked: int = 0
        self.violations: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}

    def add_violation(self, rule_name: str, block_id: str, section: str, details: str):
        self.is_valid = False
        self.violations.append({
            "rule": rule_name,
            "block_id": str(block_id),
            "section": str(section),
            "severity": "CRITICAL",
            "details": details
        })

    def add_warning(self, rule_name: str, block_id: str, section: str, details: str):
        self.warnings.append({
            "rule": rule_name,
            "block_id": str(block_id),
            "section": str(section),
            "severity": "WARNING",
            "details": details
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_blocks_checked": self.total_blocks_checked,
            "total_constraints_checked": self.total_constraints_checked,
            "violation_count": len(self.violations),
            "warning_count": len(self.warnings),
            "violations": self.violations,
            "warnings": self.warnings,
            "metrics": self.metrics
        }


def validate_schedule(
    schedule_df: pd.DataFrame,
    coa_df: pd.DataFrame,
    equipment_df: Optional[pd.DataFrame] = None,
    crews_df: Optional[pd.DataFrame] = None,
    all_tasks_df: Optional[pd.DataFrame] = None,
    safety_buffer_hours: float = 0.5,
    max_block_hours: float = 4.0
) -> ScheduleValidationReport:
    """
    Adversarially validates every block assignment against physical and operational rules.
    
    Args:
        schedule_df: The output schedule from the optimizer
        coa_df: Master corridor window availability
        equipment_df: Heavy machinery fleet limits
        crews_df: Work gang availability
        all_tasks_df: Original defect task pool
        safety_buffer_hours: Minimum temporal buffer required between operations
        max_block_hours: Maximum allowable continuous block length
    
    Returns:
        ScheduleValidationReport containing is_valid, violations, and metrics.
    """
    report = ScheduleValidationReport()
    report.total_blocks_checked = len(schedule_df)

    if schedule_df.empty:
        report.add_warning("EMPTY_SCHEDULE", "NONE", "ALL", "Schedule is empty. Zero blocks allocated.")
        return report

    # -------------------------------------------------------------
    # Constraint 1: Temporal Exclusivity (No Overlapping Track Blocks)
    # Why: Two maintenance gangs cannot occupy the same physical track simultaneously.
    # -------------------------------------------------------------
    report.total_constraints_checked += 1
    for (corridor, section, day), group in schedule_df.groupby(["corridor", "section", "day_of_week"]):
        sorted_blocks = group.sort_values("block_start_hour").reset_index(drop=True)
        for i in range(len(sorted_blocks) - 1):
            curr_b = sorted_blocks.iloc[i]
            next_b = sorted_blocks.iloc[i + 1]
            
            # Allow floating-point precision tolerance of 0.01 hours (~36 seconds)
            if curr_b["block_end_hour"] > next_b["block_start_hour"] + 0.01:
                report.add_violation(
                    rule_name="TRACK_EXCLUSIVITY_COLLISION",
                    block_id=f"{curr_b['block_id']} & {next_b['block_id']}",
                    section=f"{corridor}/{section} ({day})",
                    details=(
                        f"Block {curr_b['block_id']} (ends {curr_b['block_end_hour']:.2f}h) overlaps with "
                        f"Block {next_b['block_id']} (starts {next_b['block_start_hour']:.2f}h)"
                    )
                )

    # -------------------------------------------------------------
    # Constraint 2: Window Boundary & Duration Containment
    # Why: Blocks must stay strictly inside sanctioned corridor traffic windows.
    # -------------------------------------------------------------
    report.total_constraints_checked += 1
    window_map = coa_df.set_index("window_id").to_dict(orient="index") if not coa_df.empty else {}

    for _, b in schedule_df.iterrows():
        b_id = b["block_id"]
        w_id = b.get("window_id")
        start = float(b["block_start_hour"])
        end = float(b["block_end_hour"])
        duration = float(b.get("total_hours", end - start))
        section = b.get("section", "UNKNOWN")

        # Duration sanity
        if duration <= 0:
            report.add_violation("INVALID_DURATION", b_id, section, f"Duration is non-positive: {duration}h")
        if duration > max_block_hours + 0.05:
            report.add_violation("EXCEEDS_MAX_BLOCK_LENGTH", b_id, section, f"Duration {duration:.2f}h exceeds max allowable {max_block_hours}h")

        # Window alignment
        if w_id and w_id in window_map:
            w_info = window_map[w_id]
            w_start = float(w_info["window_start_hour"])
            w_end = float(w_info["window_end_hour"])
            w_density = str(w_info.get("train_density", "")).lower()

            # Window containment check (with 0.05h buffer tolerance)
            if start < w_start - 0.05 or end > w_end + 0.05:
                report.add_violation(
                    "WINDOW_OUT_OF_BOUNDS",
                    b_id,
                    section,
                    f"Block [{start:.2f}-{end:.2f}] breaches window {w_id} boundaries [{w_start:.2f}-{w_end:.2f}]"
                )

            # Suburban Peak-Hour Rule
            # Why: Railway Board prohibits blocking suburban trunk lines during commuter rush hours.
            if w_density == "peak":
                report.add_violation(
                    "PEAK_HOUR_PROHIBITION_BREACH",
                    b_id,
                    section,
                    f"Block scheduled in peak-density window {w_id} ({w_density})"
                )

    # -------------------------------------------------------------
    # Constraint 3: Heavy Machinery & Equipment Double-Booking
    # Why: A physical tamping machine or tower wagon cannot be in two places at once.
    # -------------------------------------------------------------
    report.total_constraints_checked += 1
    if "required_equipment" in schedule_df.columns:
        # Determine available count per machine type
        eq_counts = {}
        if equipment_df is not None and not equipment_df.empty and "equipment_type" in equipment_df.columns:
            eq_counts = equipment_df["equipment_type"].value_counts().to_dict()

        for (day, w_id), group in schedule_df.groupby(["day_of_week", "window_id"]):
            eq_used_in_window: Dict[str, int] = {}
            for _, b in group.iterrows():
                eq = str(b.get("required_equipment", "")).strip()
                if eq and eq != "None" and eq != "nan":
                    eq_used_in_window[eq] = eq_used_in_window.get(eq, 0) + 1

            for eq, count in eq_used_in_window.items():
                max_avail = eq_counts.get(eq, 2)  # Default fleet cap of 2 if unspecified
                if count > max_avail:
                    report.add_violation(
                        "EQUIPMENT_FLEET_OVERCOMMITTED",
                        f"Window {w_id}",
                        group["section"].iloc[0],
                        f"Machine '{eq}' requested {count} times in same window, but only {max_avail} exist"
                    )

    # -------------------------------------------------------------
    # Constraint 4: Emergency / P1 Safety Completeness
    # Why: Life-critical track fractures or severe geometry faults must never be omitted.
    # -------------------------------------------------------------
    report.total_constraints_checked += 1
    if all_tasks_df is not None and not all_tasks_df.empty:
        # Check emergency tasks
        p1_tasks = all_tasks_df[
            (all_tasks_df.get("emergency", False) == True) | 
            (all_tasks_df.get("severity", 0) >= 5) |
            (all_tasks_df.get("criticality_index", 0) >= 80)
        ]
        
        scheduled_task_ids = set()
        for _, b in schedule_df.iterrows():
            t_ids = b.get("task_ids")
            if isinstance(t_ids, list):
                scheduled_task_ids.update(str(tid) for tid in t_ids)
            elif isinstance(t_ids, str):
                for tid in t_ids.split(";"):
                    scheduled_task_ids.add(tid.strip())

        for _, task in p1_tasks.iterrows():
            tid = str(task["task_id"])
            if tid not in scheduled_task_ids:
                report.add_violation(
                    "P1_SAFETY_TASK_OMISSION",
                    tid,
                    task.get("section", "UNKNOWN"),
                    f"P1 Critical/Emergency task {tid} (Sev: {task.get('severity')}, CI: {task.get('criticality_index', 0):.1f}) was omitted from schedule"
                )

    # Compute high-level validation metrics
    report.metrics = {
        "blocks_scheduled": len(schedule_df),
        "total_track_hours": float(schedule_df["total_hours"].sum()) if "total_hours" in schedule_df.columns else 0.0,
        "violations_found": len(report.violations),
        "warnings_found": len(report.warnings),
        "status": "PASSED" if report.is_valid else "FAILED"
    }

    return report
