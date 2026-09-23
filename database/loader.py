"""
Data Ingestion & Schema Validation Module.

Loads synthetic CSV data from the generated directory, validates it using
Pydantic models, and produces unified DataFrames for downstream operations.
"""

import os
from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field, field_validator


# ─── Pydantic Schema Models ──────────────────────────────────────────────────

class Asset(BaseModel):
    asset_id: str
    asset_type: str
    department: str
    corridor: str
    section: str
    latitude: float
    longitude: float
    kilometer: float
    installation_date: str
    condition_score: float
    operational_status: str

class MaintenanceTask(BaseModel):
    task_id: str
    asset_id: str
    department: str
    corridor: str
    section: str
    chainage_km: float = Field(ge=0)
    latitude: float
    longitude: float
    defect_type: str
    description: str
    severity: int = Field(ge=1, le=5)
    safety_impact: str
    operational_impact: str
    speed_class: str
    days_overdue: int = Field(ge=0)
    required_hours: float = Field(gt=0)
    estimated_duration: float = Field(gt=0)
    reported_date: str
    last_maintenance_days: int = Field(ge=0)
    required_crew: int = Field(ge=0)
    required_equipment: str
    mandatory: bool
    emergency: bool
    status: str
    dependency: str = ""

class COAWindow(BaseModel):
    window_id: str
    corridor: str
    section: str
    start_km: float = Field(ge=0)
    end_km: float = Field(gt=0)
    day_of_week: str
    window_start_hour: float = Field(ge=0, le=24)
    window_end_hour: float = Field(ge=0, le=24)
    duration_hours: float = Field(gt=0)
    train_density: str
    freight_density: str
    allowed_departments: str
    safety_buffer_hours: float = Field(ge=0)

class Train(BaseModel):
    train_id: str
    train_number: str
    train_type: str
    corridor: str
    section: str
    arrival_hour: float = Field(ge=0, le=24)
    departure_hour: float = Field(ge=0, le=24)
    direction: str
    priority: str
    operating_day: str

class Crew(BaseModel):
    crew_id: str
    department: str
    skill: str
    capacity: int = Field(gt=0)
    availability: str

class Equipment(BaseModel):
    equipment_id: str
    equipment_type: str
    availability: str
    location: str

class Material(BaseModel):
    material_id: str
    material_type: str
    quantity: int = Field(ge=0)
    location: str


# ─── Schema-to-Model Mapping ─────────────────────────────────────────────────

SCHEMA_MAP = {
    "assets": Asset,
    "tms": MaintenanceTask,
    "smms": MaintenanceTask,
    "tdms": MaintenanceTask,
    "coa": COAWindow,
    "trains": Train,
    "crews": Crew,
    "equipment": Equipment,
    "materials": Material
}


def _validate_dataframe(df: pd.DataFrame, schema_class, dataset_name: str) -> pd.DataFrame:
    valid_rows = []
    errors = []

    for idx, row in df.iterrows():
        try:
            # Handle NaN values for strings
            d = row.to_dict()
            for k, v in d.items():
                if pd.isna(v):
                    if schema_class.model_fields[k].annotation == str:
                        d[k] = ""
                else:
                    # Coerce ints to strings if pydantic expects a string
                    if schema_class.model_fields[k].annotation == str:
                        d[k] = str(v)
            
            obj = schema_class(**d)
            valid_rows.append(obj.model_dump())
        except Exception as e:
            errors.append({"row": idx, "error": str(e)})

    if errors:
        print(f"  [WARN] {dataset_name}: {len(errors)} validation errors (dropped)")
        print(f"  [DEBUG] First error: {errors[0]}")

    validated_df = pd.DataFrame(valid_rows)
    print(f"  [OK] {dataset_name}: {len(validated_df)}/{len(df)} rows validated")
    return validated_df


def load_data(data_dir: Optional[str] = None) -> dict:
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "generated")

    print("=" * 60)
    print("  AI Block Planning — Data Ingestion & Validation")
    print("=" * 60)
    print(f"\n  Source: {os.path.abspath(data_dir)}\n")

    files = {
        "assets": "assets.csv",
        "tms": "tms_defects.csv",
        "smms": "smms_defects.csv",
        "tdms": "tdms_defects.csv",
        "coa": "coa_windows.csv",
        "trains": "trains.csv",
        "crews": "crews.csv",
        "equipment": "equipment.csv",
        "materials": "materials.csv"
    }

    datasets = {}
    for key, filename in files.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Missing dataset: {filepath}. Run data generator first.")
        df = pd.read_csv(filepath)
        datasets[key] = _validate_dataframe(df, SCHEMA_MAP[key], key.upper())

    # Merge all maintenance tasks into unified DataFrame
    task_dfs = [datasets["tms"], datasets["smms"], datasets["tdms"]]
    all_tasks = pd.concat(task_dfs, ignore_index=True)
    all_tasks = all_tasks.sort_values("chainage_km").reset_index(drop=True)

    datasets["all_tasks"] = all_tasks

    print(f"\n{'-' * 60}")
    print(f"  Unified task pool: {len(all_tasks)} tasks across 3 departments")
    print(f"  Corridor windows:  {len(datasets['coa'])} entries")
    print(f"{'-' * 60}\n")

    return datasets


if __name__ == "__main__":
    data = load_data()
    print("Sample unified tasks:")
    print(data["all_tasks"].head(5).to_string())
