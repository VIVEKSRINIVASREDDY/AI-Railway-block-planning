"""
Data Ingestion & Schema Validation Module.

Loads synthetic CSV data from the generated directory, validates it using
Pydantic models, and produces a unified MaintenanceTask dataframe for
downstream scoring and optimization.
"""

import os
from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field, field_validator


# ─── Pydantic Schema Models ──────────────────────────────────────────────────

class TMSTask(BaseModel):
    """Schema for Track Management System defect records."""
    task_id: str
    department: str = "Engineering"
    corridor: str
    section: str
    chainage_km: float = Field(ge=0)
    defect_type: str
    severity: int = Field(ge=1, le=5)
    speed_class: str
    days_overdue: int = Field(ge=0)
    required_hours: float = Field(gt=0)
    reported_date: str
    last_maintenance_days: int = Field(ge=0)


class SMMSTask(BaseModel):
    """Schema for Signal Maintenance Management System records."""
    task_id: str
    department: str = "S&T"
    corridor: str
    section: str
    chainage_km: float = Field(ge=0)
    defect_type: str
    severity: int = Field(ge=1, le=5)
    speed_class: str
    days_overdue: int = Field(ge=0)
    required_hours: float = Field(gt=0)
    reported_date: str
    last_maintenance_days: int = Field(ge=0)


class TDMSTask(BaseModel):
    """Schema for Traction Distribution Management System records."""
    task_id: str
    department: str = "Electrical"
    corridor: str
    section: str
    chainage_km: float = Field(ge=0)
    defect_type: str
    severity: int = Field(ge=1, le=5)
    speed_class: str
    days_overdue: int = Field(ge=0)
    required_hours: float = Field(gt=0)
    reported_date: str
    last_maintenance_days: int = Field(ge=0)


class COAWindow(BaseModel):
    """Schema for Control Office Application corridor windows."""
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

    @field_validator("train_density")
    @classmethod
    def validate_density(cls, v):
        if v not in ("peak", "off-peak", "night"):
            raise ValueError(f"Invalid train_density: {v}")
        return v


# ─── Schema-to-Model Mapping ─────────────────────────────────────────────────

SCHEMA_MAP = {
    "tms": TMSTask,
    "smms": SMMSTask,
    "tdms": TDMSTask,
    "coa": COAWindow,
}


def _validate_dataframe(df: pd.DataFrame, schema_class, dataset_name: str) -> pd.DataFrame:
    """
    Validate each row of a DataFrame against a Pydantic schema.
    Returns the cleaned DataFrame with only valid rows.
    """
    valid_rows = []
    errors = []

    for idx, row in df.iterrows():
        try:
            obj = schema_class(**row.to_dict())
            valid_rows.append(obj.model_dump())
        except Exception as e:
            errors.append({"row": idx, "error": str(e)})

    if errors:
        print(f"  [WARN] {dataset_name}: {len(errors)} validation errors (dropped)")

    validated_df = pd.DataFrame(valid_rows)
    print(f"  [OK] {dataset_name}: {len(validated_df)}/{len(df)} rows validated")
    return validated_df


def load_data(data_dir: Optional[str] = None) -> dict:
    """
    Load and validate all synthetic datasets.

    Args:
        data_dir: Path to directory containing generated CSVs.
                  Defaults to data/generated/ relative to project root.

    Returns:
        Dictionary with keys: tms, smms, tdms, coa, all_tasks
        - tms/smms/tdms: validated department DataFrames
        - coa: validated corridor window DataFrame
        - all_tasks: unified maintenance task DataFrame (all departments merged)
    """
    if data_dir is None:
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "generated"
        )

    print("=" * 60)
    print("  AI Block Planning — Data Ingestion & Validation")
    print("=" * 60)
    print(f"\n  Source: {os.path.abspath(data_dir)}\n")

    # File mapping
    files = {
        "tms": "tms_defects.csv",
        "smms": "smms_defects.csv",
        "tdms": "tdms_defects.csv",
        "coa": "coa_windows.csv",
    }

    # Load and validate each dataset
    datasets = {}
    for key, filename in files.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"Missing dataset: {filepath}. Run data generator first."
            )
        df = pd.read_csv(filepath)
        datasets[key] = _validate_dataframe(df, SCHEMA_MAP[key], key.upper())

    # Merge all maintenance tasks into unified DataFrame
    task_dfs = [datasets["tms"], datasets["smms"], datasets["tdms"]]
    all_tasks = pd.concat(task_dfs, ignore_index=True)
    all_tasks = all_tasks.sort_values("chainage_km").reset_index(drop=True)

    datasets["all_tasks"] = all_tasks

    print(f"\n{'─' * 60}")
    print(f"  Unified task pool: {len(all_tasks)} tasks across 3 departments")
    print(f"  Corridor windows:  {len(datasets['coa'])} entries")
    print(f"{'─' * 60}\n")

    return datasets


if __name__ == "__main__":
    data = load_data()
    print("Sample unified tasks:")
    print(data["all_tasks"].head(10).to_string())
