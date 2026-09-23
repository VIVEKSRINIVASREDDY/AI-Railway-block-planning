"""
Synthetic Data Generator for AI Block Planning System.

Generates realistic maintenance defect data for:
- TMS (Track Management System) — rail/track defects
- SMMS (Signal Maintenance Management System) — signalling equipment
- TDMS (Traction Distribution Management System) — OHE/electrical
- COA (Control Office Application) — corridor windows & trains
- Assets, Resources (Crews, Equipment, Materials)
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

# ─── Defect Types ────────────────────────────────────────────────────────

TMS_DEFECT_TYPES = [
    {"type": "Rail Fracture", "severity_range": (4, 5), "hours_range": (4, 8), "safety_impact": "High", "operational_impact": "High"},
    {"type": "Weld Defect", "severity_range": (3, 5), "hours_range": (3, 6), "safety_impact": "High", "operational_impact": "Medium"},
    {"type": "Gauge Error", "severity_range": (2, 4), "hours_range": (2, 4), "safety_impact": "Medium", "operational_impact": "Medium"},
    {"type": "Rail Wear (Head)", "severity_range": (2, 4), "hours_range": (3, 5), "safety_impact": "Medium", "operational_impact": "Low"},
    {"type": "Sleeper Damage", "severity_range": (1, 3), "hours_range": (2, 4), "safety_impact": "Low", "operational_impact": "Low"},
    {"type": "Ballast Deficiency", "severity_range": (1, 3), "hours_range": (2, 3), "safety_impact": "Medium", "operational_impact": "Low"},
    {"type": "Track Buckling Risk", "severity_range": (4, 5), "hours_range": (4, 8), "safety_impact": "High", "operational_impact": "High"},
    {"type": "Fishplate Crack", "severity_range": (3, 5), "hours_range": (2, 4), "safety_impact": "High", "operational_impact": "Medium"},
    {"type": "Formation Issue", "severity_range": (2, 4), "hours_range": (3, 6), "safety_impact": "Medium", "operational_impact": "Low"},
    {"type": "Level Crossing Defect", "severity_range": (3, 5), "hours_range": (3, 5), "safety_impact": "High", "operational_impact": "High"},
]

SMMS_EQUIPMENT_TYPES = [
    {"type": "Point Machine Failure", "severity_range": (3, 5), "hours_range": (2, 5), "safety_impact": "High", "operational_impact": "High"},
    {"type": "Track Circuit Fault", "severity_range": (3, 5), "hours_range": (2, 4), "safety_impact": "High", "operational_impact": "High"},
    {"type": "Signal Relay Defect", "severity_range": (2, 4), "hours_range": (1, 3), "safety_impact": "Medium", "operational_impact": "Medium"},
    {"type": "Cable Insulation Failure", "severity_range": (2, 4), "hours_range": (3, 6), "safety_impact": "Medium", "operational_impact": "Low"},
    {"type": "Axle Counter Fault", "severity_range": (3, 5), "hours_range": (2, 4), "safety_impact": "High", "operational_impact": "Medium"},
    {"type": "Interlocking Logic Error", "severity_range": (4, 5), "hours_range": (3, 6), "safety_impact": "High", "operational_impact": "High"},
    {"type": "LED Signal Lamp Failure", "severity_range": (1, 3), "hours_range": (1, 2), "safety_impact": "Low", "operational_impact": "Low"},
    {"type": "Route Relay Degradation", "severity_range": (2, 4), "hours_range": (2, 4), "safety_impact": "Medium", "operational_impact": "Low"},
]

TDMS_COMPONENT_TYPES = [
    {"type": "OHE Mast Tilt", "severity_range": (3, 5), "hours_range": (3, 6), "safety_impact": "High", "operational_impact": "High"},
    {"type": "Catenary Wire Wear", "severity_range": (3, 5), "hours_range": (4, 8), "safety_impact": "High", "operational_impact": "Medium"},
    {"type": "Transformer Inspection", "severity_range": (2, 4), "hours_range": (3, 5), "safety_impact": "Medium", "operational_impact": "Low"},
    {"type": "Insulator Flashover", "severity_range": (4, 5), "hours_range": (2, 4), "safety_impact": "High", "operational_impact": "High"},
    {"type": "Contact Wire Height", "severity_range": (2, 4), "hours_range": (2, 4), "safety_impact": "Medium", "operational_impact": "Medium"},
    {"type": "Return Conductor Defect", "severity_range": (2, 3), "hours_range": (2, 3), "safety_impact": "Low", "operational_impact": "Low"},
    {"type": "Dropper Replacement", "severity_range": (1, 3), "hours_range": (1, 3), "safety_impact": "Low", "operational_impact": "Low"},
    {"type": "ATD/OHE Span Inspection", "severity_range": (1, 3), "hours_range": (2, 4), "safety_impact": "Medium", "operational_impact": "Low"},
]

def _pick_section():
    """Pick a random corridor and section, return metadata."""
    corridor_name = random.choice(list(CORRIDORS.keys()))
    corridor = CORRIDORS[corridor_name]
    section = random.choice(corridor["sections"])
    chainage = round(random.uniform(section["start_km"], section["end_km"]), 1)
    
    # Fake lat/lon based on chainage just for visual variance
    base_lat, base_lon = 20.0, 78.0 
    lat = base_lat + (chainage * 0.01) * random.choice([1, -1])
    lon = base_lon + (chainage * 0.01) * random.choice([1, -1])
    
    return {
        "corridor": corridor_name,
        "section": section["name"],
        "start_km": section["start_km"],
        "end_km": section["end_km"],
        "chainage_km": chainage,
        "speed_class": corridor["speed_class"],
        "latitude": round(lat, 4),
        "longitude": round(lon, 4)
    }

def _random_date(start_days_ago=90, end_days_ago=1):
    """Random date in the recent past."""
    days_ago = random.randint(end_days_ago, start_days_ago)
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

def generate_assets(n=500) -> pd.DataFrame:
    records = []
    types = ["Track", "Signal", "OHE", "Transformer", "Point Machine", "Bridge", "Level Crossing", "Communication"]
    for i in range(n):
        loc = _pick_section()
        dept = "Engineering" if types[i%8] in ["Track", "Bridge", "Level Crossing"] else ("S&T" if types[i%8] in ["Signal", "Point Machine", "Communication"] else "Electrical")
        records.append({
            "asset_id": f"AST-{i+1:05d}",
            "asset_type": types[i%8],
            "department": dept,
            "corridor": loc["corridor"],
            "section": loc["section"],
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "kilometer": loc["chainage_km"],
            "installation_date": _random_date(3650, 100),
            "condition_score": round(random.uniform(30, 100), 1),
            "operational_status": random.choice(["Active", "Active", "Active", "Under Maintenance"])
        })
    return pd.DataFrame(records)

def generate_tms(n=120) -> pd.DataFrame:
    records = []
    for i in range(n):
        defect = random.choice(TMS_DEFECT_TYPES)
        loc = _pick_section()
        severity = random.randint(*defect["severity_range"])
        days_overdue = max(0, random.randint(-10, 60))
        required_hours = round(random.uniform(*defect["hours_range"]), 1)
        records.append({
            "task_id": f"TMS-{i+1:04d}",
            "asset_id": f"AST-{random.randint(1,500):05d}",
            "department": "Engineering",
            "corridor": loc["corridor"],
            "section": loc["section"],
            "chainage_km": loc["chainage_km"],
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "defect_type": defect["type"],
            "description": f"Maintenance required for {defect['type']}",
            "severity": severity,
            "safety_impact": defect["safety_impact"],
            "operational_impact": defect["operational_impact"],
            "speed_class": loc["speed_class"],
            "days_overdue": days_overdue,
            "required_hours": required_hours,
            "estimated_duration": required_hours,
            "reported_date": _random_date(),
            "last_maintenance_days": random.randint(30, 365),
            "required_crew": random.randint(3, 10),
            "required_equipment": random.choice(["Track Tamper", "Ballast Regulator", "None"]),
            "mandatory": severity >= 4,
            "emergency": severity == 5 and days_overdue > 10,
            "status": "OPEN",
            "dependency": ""
        })
    return pd.DataFrame(records)

def generate_smms(n=80) -> pd.DataFrame:
    records = []
    for i in range(n):
        equip = random.choice(SMMS_EQUIPMENT_TYPES)
        loc = _pick_section()
        severity = random.randint(*equip["severity_range"])
        days_overdue = max(0, random.randint(-10, 45))
        required_hours = round(random.uniform(*equip["hours_range"]), 1)
        records.append({
            "task_id": f"SMMS-{i+1:04d}",
            "asset_id": f"AST-{random.randint(1,500):05d}",
            "department": "S&T",
            "corridor": loc["corridor"],
            "section": loc["section"],
            "chainage_km": loc["chainage_km"],
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "defect_type": equip["type"],
            "description": f"Maintenance required for {equip['type']}",
            "severity": severity,
            "safety_impact": equip["safety_impact"],
            "operational_impact": equip["operational_impact"],
            "speed_class": loc["speed_class"],
            "days_overdue": days_overdue,
            "required_hours": required_hours,
            "estimated_duration": required_hours,
            "reported_date": _random_date(),
            "last_maintenance_days": random.randint(15, 270),
            "required_crew": random.randint(2, 5),
            "required_equipment": random.choice(["Signal Testing Unit", "None"]),
            "mandatory": severity >= 4,
            "emergency": severity == 5 and days_overdue > 5,
            "status": "OPEN",
            "dependency": ""
        })
    return pd.DataFrame(records)

def generate_tdms(n=60) -> pd.DataFrame:
    records = []
    for i in range(n):
        comp = random.choice(TDMS_COMPONENT_TYPES)
        loc = _pick_section()
        severity = random.randint(*comp["severity_range"])
        days_overdue = max(0, random.randint(-5, 40))
        required_hours = round(random.uniform(*comp["hours_range"]), 1)
        records.append({
            "task_id": f"TDMS-{i+1:04d}",
            "asset_id": f"AST-{random.randint(1,500):05d}",
            "department": "Electrical",
            "corridor": loc["corridor"],
            "section": loc["section"],
            "chainage_km": loc["chainage_km"],
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "defect_type": comp["type"],
            "description": f"Maintenance required for {comp['type']}",
            "severity": severity,
            "safety_impact": comp["safety_impact"],
            "operational_impact": comp["operational_impact"],
            "speed_class": loc["speed_class"],
            "days_overdue": days_overdue,
            "required_hours": required_hours,
            "estimated_duration": required_hours,
            "reported_date": _random_date(),
            "last_maintenance_days": random.randint(20, 300),
            "required_crew": random.randint(3, 8),
            "required_equipment": random.choice(["Tower Wagon", "None"]),
            "mandatory": severity >= 4,
            "emergency": severity == 5 and days_overdue > 5,
            "status": "OPEN",
            "dependency": ""
        })
    return pd.DataFrame(records)

def generate_windows() -> pd.DataFrame:
    records = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    window_templates = [
        (0.0, 4.5, "night"),       
        (10.0, 12.5, "off-peak"),  
        (14.0, 16.0, "off-peak"),  
    ]
    peak_templates = [
        (5.0, 9.5, "peak"),   
        (16.5, 21.0, "peak"), 
    ]
    record_id = 0
    for corridor_name, corridor in CORRIDORS.items():
        for section in corridor["sections"]:
            for day in days:
                for start_h, end_h, density in window_templates:
                    adj_start = round(start_h + random.uniform(-0.25, 0.25), 2)
                    adj_end = round(end_h + random.uniform(-0.25, 0.25), 2)
                    duration_hours = round(adj_end - adj_start, 2)
                    if day in ("Saturday", "Sunday"):
                        adj_end = round(adj_end + random.uniform(0.5, 1.5), 2)
                        duration_hours = round(adj_end - adj_start, 2)
                    record_id += 1
                    records.append({
                        "window_id": f"WIN-{record_id:04d}",
                        "corridor": corridor_name,
                        "section": section["name"],
                        "start_km": section["start_km"],
                        "end_km": section["end_km"],
                        "day_of_week": day,
                        "window_start_hour": max(0, adj_start),
                        "window_end_hour": min(24, adj_end),
                        "duration_hours": max(0.5, duration_hours),
                        "train_density": density,
                        "freight_density": random.choice(["low", "medium", "high"]),
                        "allowed_departments": "All",
                        "safety_buffer_hours": 0.5
                    })
                for start_h, end_h, density in peak_templates:
                    record_id += 1
                    records.append({
                        "window_id": f"WIN-{record_id:04d}",
                        "corridor": corridor_name,
                        "section": section["name"],
                        "start_km": section["start_km"],
                        "end_km": section["end_km"],
                        "day_of_week": day,
                        "window_start_hour": start_h,
                        "window_end_hour": end_h,
                        "duration_hours": round(end_h - start_h, 2),
                        "train_density": density,
                        "freight_density": random.choice(["medium", "high"]),
                        "allowed_departments": "None",
                        "safety_buffer_hours": 0.0
                    })
    return pd.DataFrame(records)

def generate_trains(n=200) -> pd.DataFrame:
    records = []
    types = ["Express", "Passenger", "Freight", "Rajdhani", "Shatabdi"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i in range(n):
        loc = _pick_section()
        records.append({
            "train_id": f"TRN-{i+1:04d}",
            "train_number": f"{random.randint(10000, 99999)}",
            "train_type": random.choice(types),
            "corridor": loc["corridor"],
            "section": loc["section"],
            "arrival_hour": round(random.uniform(0, 23), 2),
            "departure_hour": round(random.uniform(0, 23), 2),
            "direction": random.choice(["UP", "DOWN"]),
            "priority": random.choice(["High", "Medium", "Low"]),
            "operating_day": random.choice(days)
        })
    return pd.DataFrame(records)

def generate_resources() -> dict:
    crews = []
    depts = ["Engineering", "S&T", "Electrical"]
    for i in range(30):
        crews.append({
            "crew_id": f"CRW-{i+1:03d}",
            "department": random.choice(depts),
            "skill": random.choice(["Basic", "Advanced", "Expert"]),
            "capacity": random.randint(5, 15),
            "availability": "Available"
        })
    
    equipment = []
    eq_types = ["Track Tamper", "Ballast Regulator", "Tower Wagon", "Signal Testing Unit"]
    for i in range(20):
        equipment.append({
            "equipment_id": f"EQP-{i+1:03d}",
            "equipment_type": random.choice(eq_types),
            "availability": "Available",
            "location": random.choice(list(CORRIDORS.keys()))
        })
        
    materials = []
    mat_types = ["Rails", "Sleepers", "Ballast", "Cables", "Relays"]
    for i in range(50):
        materials.append({
            "material_id": f"MAT-{i+1:03d}",
            "material_type": random.choice(mat_types),
            "quantity": random.randint(10, 1000),
            "location": random.choice(list(CORRIDORS.keys()))
        })
        
    return {
        "crews": pd.DataFrame(crews),
        "equipment": pd.DataFrame(equipment),
        "materials": pd.DataFrame(materials)
    }

def generate_all(output_dir: str = None) -> dict:
    """Generate all synthetic datasets and save to CSV."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "generated")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  AI Block Planning - Synthetic Data Generator")
    print("=" * 60)

    assets = generate_assets()
    assets.to_csv(os.path.join(output_dir, "assets.csv"), index=False)
    print(f"       [OK] {len(assets)} records -> assets.csv")

    tms = generate_tms(120)
    tms.to_csv(os.path.join(output_dir, "tms_defects.csv"), index=False)
    print(f"       [OK] {len(tms)} records -> tms_defects.csv")

    smms = generate_smms(80)
    smms.to_csv(os.path.join(output_dir, "smms_defects.csv"), index=False)
    print(f"       [OK] {len(smms)} records -> smms_defects.csv")

    tdms = generate_tdms(60)
    tdms.to_csv(os.path.join(output_dir, "tdms_defects.csv"), index=False)
    print(f"       [OK] {len(tdms)} records -> tdms_defects.csv")

    windows = generate_windows()
    windows.to_csv(os.path.join(output_dir, "coa_windows.csv"), index=False)
    print(f"       [OK] {len(windows)} records -> coa_windows.csv (Windows)")
    
    trains = generate_trains()
    trains.to_csv(os.path.join(output_dir, "trains.csv"), index=False)
    print(f"       [OK] {len(trains)} records -> trains.csv")

    res = generate_resources()
    res["crews"].to_csv(os.path.join(output_dir, "crews.csv"), index=False)
    res["equipment"].to_csv(os.path.join(output_dir, "equipment.csv"), index=False)
    res["materials"].to_csv(os.path.join(output_dir, "materials.csv"), index=False)
    print(f"       [OK] Resources generated -> crews.csv, equipment.csv, materials.csv")

    total = len(tms) + len(smms) + len(tdms) + len(windows) + len(assets) + len(trains) + len(res["crews"]) + len(res["equipment"]) + len(res["materials"])
    print(f"\n{'-' * 60}")
    print(f"  Total: {total} records across datasets")
    print(f"  Output: {os.path.abspath(output_dir)}")
    print(f"{'-' * 60}\n")

    return {
        "assets": assets,
        "tms": tms, "smms": smms, "tdms": tdms,
        "coa": windows, "trains": trains,
        "crews": res["crews"], "equipment": res["equipment"], "materials": res["materials"]
    }

if __name__ == "__main__":
    generate_all()
