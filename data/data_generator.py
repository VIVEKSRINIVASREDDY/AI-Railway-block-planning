"""
Synthetic Data Generator for AI Block Planning System.

Generates realistic maintenance defect data for:
- TMS (Track Management System) — rail/track defects
- SMMS (Signal Maintenance Management System) — signalling equipment
- TDMS (Traction Distribution Management System) — OHE/electrical
- COA (Control Office Application) — corridor train schedules/windows
"""

import os
import sys
import random
from datetime import datetime, timedelta

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

# Seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# ─── Indian Railways Corridor & Section Definitions ─────────────────────────

CORRIDORS = {
    "Delhi-Kanpur": {
        "sections": [
            {"name": "Delhi-Aligarh", "start_km": 0, "end_km": 126},
            {"name": "Aligarh-Tundla", "start_km": 126, "end_km": 199},
            {"name": "Tundla-Etawah", "start_km": 199, "end_km": 301},
            {"name": "Etawah-Kanpur", "start_km": 301, "end_km": 440},
        ],
        "speed_class": "A",  # 130 km/h Rajdhani corridor
    },
    "Mumbai-Pune": {
        "sections": [
            {"name": "Mumbai CST-Kalyan", "start_km": 0, "end_km": 54},
            {"name": "Kalyan-Lonavala", "start_km": 54, "end_km": 104},
            {"name": "Lonavala-Pune", "start_km": 104, "end_km": 192},
        ],
        "speed_class": "B",  # 110 km/h
    },
    "Chennai-Vijayawada": {
        "sections": [
            {"name": "Chennai-Gudur", "start_km": 0, "end_km": 167},
            {"name": "Gudur-Nellore", "start_km": 167, "end_km": 228},
            {"name": "Nellore-Ongole", "start_km": 228, "end_km": 340},
            {"name": "Ongole-Vijayawada", "start_km": 340, "end_km": 431},
        ],
        "speed_class": "A",
    },
    "Howrah-Dhanbad": {
        "sections": [
            {"name": "Howrah-Barddhaman", "start_km": 0, "end_km": 107},
            {"name": "Barddhaman-Asansol", "start_km": 107, "end_km": 200},
            {"name": "Asansol-Dhanbad", "start_km": 200, "end_km": 260},
        ],
        "speed_class": "B",
    },
}

SPEED_CLASS_MAP = {"A": 130, "B": 110, "C": 90, "D": 75}

# ─── TMS Defect Types ────────────────────────────────────────────────────────

TMS_DEFECT_TYPES = [
    {"type": "Rail Fracture", "severity_range": (4, 5), "hours_range": (4, 8)},
    {"type": "Weld Defect", "severity_range": (3, 5), "hours_range": (3, 6)},
    {"type": "Gauge Error", "severity_range": (2, 4), "hours_range": (2, 4)},
    {"type": "Rail Wear (Head)", "severity_range": (2, 4), "hours_range": (3, 5)},
    {"type": "Sleeper Damage", "severity_range": (1, 3), "hours_range": (2, 4)},
    {"type": "Ballast Deficiency", "severity_range": (1, 3), "hours_range": (2, 3)},
    {"type": "Track Buckling Risk", "severity_range": (4, 5), "hours_range": (4, 8)},
    {"type": "Fishplate Crack", "severity_range": (3, 5), "hours_range": (2, 4)},
    {"type": "Formation Issue", "severity_range": (2, 4), "hours_range": (3, 6)},
    {"type": "Level Crossing Defect", "severity_range": (3, 5), "hours_range": (3, 5)},
]

# ─── SMMS Equipment Types ────────────────────────────────────────────────────

SMMS_EQUIPMENT_TYPES = [
    {"type": "Point Machine Failure", "severity_range": (3, 5), "hours_range": (2, 5)},
    {"type": "Track Circuit Fault", "severity_range": (3, 5), "hours_range": (2, 4)},
    {"type": "Signal Relay Defect", "severity_range": (2, 4), "hours_range": (1, 3)},
    {"type": "Cable Insulation Failure", "severity_range": (2, 4), "hours_range": (3, 6)},
    {"type": "Axle Counter Fault", "severity_range": (3, 5), "hours_range": (2, 4)},
    {"type": "Interlocking Logic Error", "severity_range": (4, 5), "hours_range": (3, 6)},
    {"type": "LED Signal Lamp Failure", "severity_range": (1, 3), "hours_range": (1, 2)},
    {"type": "Route Relay Degradation", "severity_range": (2, 4), "hours_range": (2, 4)},
]

# ─── TDMS Component Types ────────────────────────────────────────────────────

TDMS_COMPONENT_TYPES = [
    {"type": "OHE Mast Tilt", "severity_range": (3, 5), "hours_range": (3, 6)},
    {"type": "Catenary Wire Wear", "severity_range": (3, 5), "hours_range": (4, 8)},
    {"type": "Transformer Inspection", "severity_range": (2, 4), "hours_range": (3, 5)},
    {"type": "Insulator Flashover", "severity_range": (4, 5), "hours_range": (2, 4)},
    {"type": "Contact Wire Height", "severity_range": (2, 4), "hours_range": (2, 4)},
    {"type": "Return Conductor Defect", "severity_range": (2, 3), "hours_range": (2, 3)},
    {"type": "Dropper Replacement", "severity_range": (1, 3), "hours_range": (1, 3)},
    {"type": "ATD/OHE Span Inspection", "severity_range": (1, 3), "hours_range": (2, 4)},
]


def _pick_section():
    """Pick a random corridor and section, return metadata."""
    corridor_name = random.choice(list(CORRIDORS.keys()))
    corridor = CORRIDORS[corridor_name]
    section = random.choice(corridor["sections"])
    chainage = round(
        random.uniform(section["start_km"], section["end_km"]), 1
    )
    return {
        "corridor": corridor_name,
        "section": section["name"],
        "start_km": section["start_km"],
        "end_km": section["end_km"],
        "chainage_km": chainage,
        "speed_class": corridor["speed_class"],
    }


def _random_date(start_days_ago=90, end_days_ago=1):
    """Random date in the recent past."""
    days_ago = random.randint(end_days_ago, start_days_ago)
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def generate_tms(n=120) -> pd.DataFrame:
    """Generate TMS (Track Management System) defect records."""
    records = []
    for i in range(n):
        defect = random.choice(TMS_DEFECT_TYPES)
        loc = _pick_section()
        severity = random.randint(*defect["severity_range"])
        records.append(
            {
                "task_id": f"TMS-{i+1:04d}",
                "department": "Engineering",
                "corridor": loc["corridor"],
                "section": loc["section"],
                "chainage_km": loc["chainage_km"],
                "defect_type": defect["type"],
                "severity": severity,
                "speed_class": loc["speed_class"],
                "days_overdue": max(0, random.randint(-10, 60)),
                "required_hours": round(
                    random.uniform(*defect["hours_range"]), 1
                ),
                "reported_date": _random_date(),
                "last_maintenance_days": random.randint(30, 365),
            }
        )
    return pd.DataFrame(records)


def generate_smms(n=80) -> pd.DataFrame:
    """Generate SMMS (Signal Maintenance Management System) records."""
    records = []
    for i in range(n):
        equip = random.choice(SMMS_EQUIPMENT_TYPES)
        loc = _pick_section()
        severity = random.randint(*equip["severity_range"])
        records.append(
            {
                "task_id": f"SMMS-{i+1:04d}",
                "department": "S&T",
                "corridor": loc["corridor"],
                "section": loc["section"],
                "chainage_km": loc["chainage_km"],
                "defect_type": equip["type"],
                "severity": severity,
                "speed_class": loc["speed_class"],
                "days_overdue": max(0, random.randint(-10, 45)),
                "required_hours": round(
                    random.uniform(*equip["hours_range"]), 1
                ),
                "reported_date": _random_date(),
                "last_maintenance_days": random.randint(15, 270),
            }
        )
    return pd.DataFrame(records)


def generate_tdms(n=60) -> pd.DataFrame:
    """Generate TDMS (Traction Distribution Management System) records."""
    records = []
    for i in range(n):
        comp = random.choice(TDMS_COMPONENT_TYPES)
        loc = _pick_section()
        severity = random.randint(*comp["severity_range"])
        records.append(
            {
                "task_id": f"TDMS-{i+1:04d}",
                "department": "Electrical",
                "corridor": loc["corridor"],
                "section": loc["section"],
                "chainage_km": loc["chainage_km"],
                "defect_type": comp["type"],
                "severity": severity,
                "speed_class": loc["speed_class"],
                "days_overdue": max(0, random.randint(-5, 40)),
                "required_hours": round(
                    random.uniform(*comp["hours_range"]), 1
                ),
                "reported_date": _random_date(),
                "last_maintenance_days": random.randint(20, 300),
            }
        )
    return pd.DataFrame(records)


def generate_coa() -> pd.DataFrame:
    """
    Generate COA (Control Office Application) corridor window data.
    
    For each section, generates available maintenance windows per day of week.
    Windows are the gaps between peak train services.
    """
    records = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Window templates: (start_hour, end_hour, density_type)
    window_templates = [
        (0.0, 4.5, "night"),       # Night maintenance window (best)
        (10.0, 12.5, "off-peak"),  # Late morning gap
        (14.0, 16.0, "off-peak"),  # Afternoon gap
    ]

    # Peak windows (NO maintenance allowed)
    peak_templates = [
        (5.0, 9.5, "peak"),   # Morning rush
        (16.5, 21.0, "peak"), # Evening rush
    ]

    record_id = 0
    for corridor_name, corridor in CORRIDORS.items():
        for section in corridor["sections"]:
            for day in days:
                # Maintenance windows
                for start_h, end_h, density in window_templates:
                    # Slight randomization of window times
                    adj_start = round(start_h + random.uniform(-0.25, 0.25), 2)
                    adj_end = round(end_h + random.uniform(-0.25, 0.25), 2)
                    duration_hours = round(adj_end - adj_start, 2)

                    # Weekend windows are slightly longer
                    if day in ("Saturday", "Sunday"):
                        adj_end = round(adj_end + random.uniform(0.5, 1.5), 2)
                        duration_hours = round(adj_end - adj_start, 2)

                    record_id += 1
                    records.append(
                        {
                            "window_id": f"COA-{record_id:04d}",
                            "corridor": corridor_name,
                            "section": section["name"],
                            "start_km": section["start_km"],
                            "end_km": section["end_km"],
                            "day_of_week": day,
                            "window_start_hour": max(0, adj_start),
                            "window_end_hour": min(24, adj_end),
                            "duration_hours": max(0.5, duration_hours),
                            "train_density": density,
                            "freight_density": random.choice(
                                ["low", "medium", "high"]
                            ),
                        }
                    )

                # Record peak windows (for reference, not for scheduling)
                for start_h, end_h, density in peak_templates:
                    record_id += 1
                    records.append(
                        {
                            "window_id": f"COA-{record_id:04d}",
                            "corridor": corridor_name,
                            "section": section["name"],
                            "start_km": section["start_km"],
                            "end_km": section["end_km"],
                            "day_of_week": day,
                            "window_start_hour": start_h,
                            "window_end_hour": end_h,
                            "duration_hours": round(end_h - start_h, 2),
                            "train_density": density,
                            "freight_density": random.choice(
                                ["medium", "high"]
                            ),
                        }
                    )

    return pd.DataFrame(records)


def generate_all(output_dir: str = None) -> dict:
    """
    Generate all synthetic datasets and save to CSV.

    Returns dict of DataFrames: {tms, smms, tdms, coa}.
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "generated")

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  AI Block Planning - Synthetic Data Generator")
    print("=" * 60)

    # Generate datasets
    print("\n[1/4] Generating TMS (Track Defects)...")
    tms = generate_tms(120)
    tms.to_csv(os.path.join(output_dir, "tms_defects.csv"), index=False)
    print(f"       [OK] {len(tms)} records -> tms_defects.csv")

    print("[2/4] Generating SMMS (Signal Equipment)...")
    smms = generate_smms(80)
    smms.to_csv(os.path.join(output_dir, "smms_defects.csv"), index=False)
    print(f"       [OK] {len(smms)} records -> smms_defects.csv")

    print("[3/4] Generating TDMS (Traction/OHE)...")
    tdms = generate_tdms(60)
    tdms.to_csv(os.path.join(output_dir, "tdms_defects.csv"), index=False)
    print(f"       [OK] {len(tdms)} records -> tdms_defects.csv")

    print("[4/4] Generating COA (Corridor Windows)...")
    coa = generate_coa()
    coa.to_csv(os.path.join(output_dir, "coa_windows.csv"), index=False)
    print(f"       [OK] {len(coa)} records -> coa_windows.csv")

    total = len(tms) + len(smms) + len(tdms) + len(coa)
    print(f"\n{'-' * 60}")
    print(f"  Total: {total} records across 4 datasets")
    print(f"  Output: {os.path.abspath(output_dir)}")
    print(f"{'-' * 60}\n")

    return {"tms": tms, "smms": smms, "tdms": tdms, "coa": coa}


if __name__ == "__main__":
    generate_all()
