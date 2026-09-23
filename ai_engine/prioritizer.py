"""
AI Task Prioritization Module.

Computes a Criticality Index (0–100) for each maintenance task using:
1. A weighted heuristic formula combining safety impact, operational impact, overdue days, speed, and failure risk
2. An XGBoost classifier as a secondary urgency signal
3. A blended final score combining both approaches
4. Clear explanations for the score generated for explainability.
"""

import numpy as np
import pandas as pd
import json
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


# ─── Heuristic Scoring ───────────────────────────────────────────────────────

# Weights for the Criticality Index formula
WEIGHTS = {
    "safety_impact": 0.30,
    "operational_impact": 0.20,
    "days_overdue": 0.20,
    "speed_class": 0.15,
    "failure_probability": 0.15,
}

SPEED_CLASS_SCORES = {
    "A": 100,  # 130 km/h Rajdhani corridors — highest priority
    "B": 75,   # 110 km/h main line
    "C": 50,   # 90 km/h branch
    "D": 25,   # 75 km/h secondary
}

IMPACT_SCORES = {
    "High": 100,
    "Medium": 50,
    "Low": 25,
}

def compute_impact_score(impact_str: str) -> float:
    """Map impact (High, Medium, Low) to score (0-100)."""
    return IMPACT_SCORES.get(impact_str, 25)

def compute_overdue_score(days_overdue: int, max_days: int = 90) -> float:
    """Normalize days overdue to 0-100 scale. Capped at max_days."""
    return min(days_overdue / max_days, 1.0) * 100

def compute_speed_class_score(speed_class: str) -> float:
    """Score based on track speed classification."""
    return SPEED_CLASS_SCORES.get(speed_class, 25)

def compute_failure_probability(last_maintenance_days: int, halflife: int = 180) -> float:
    """
    Exponential failure probability based on days since last maintenance.
    Uses half-life decay: P(failure) = 1 - e^(-λt), scaled to 0-100.
    """
    lam = np.log(2) / halflife
    prob = 1 - np.exp(-lam * last_maintenance_days)
    return prob * 100

def heuristic_criticality_index(row: pd.Series) -> pd.Series:
    """
    Compute the Criticality Index (0-100) and generate an explanation.
    """
    # Emergency overrides
    if row.get("emergency", False):
        explanation = {"reason": "Emergency task.", "safety": 100, "operational": 100, "overdue": 100, "speed": 100, "failure": 100}
        return pd.Series([100.0, json.dumps(explanation)])

    safety = compute_impact_score(row.get("safety_impact", "Low"))
    operational = compute_impact_score(row.get("operational_impact", "Low"))
    overdue = compute_overdue_score(row["days_overdue"])
    speed = compute_speed_class_score(row["speed_class"])
    failure = compute_failure_probability(row["last_maintenance_days"])

    ci = (
        WEIGHTS["safety_impact"] * safety
        + WEIGHTS["operational_impact"] * operational
        + WEIGHTS["days_overdue"] * overdue
        + WEIGHTS["speed_class"] * speed
        + WEIGHTS["failure_probability"] * failure
    )
    
    ci = round(min(max(ci, 0), 100), 2)
    
    # Generate explanation
    explanation = {
        "safety_impact": f"{safety} ({row.get('safety_impact')})",
        "operational_impact": f"{operational} ({row.get('operational_impact')})",
        "overdue_score": f"{round(overdue, 1)} ({row['days_overdue']} days)",
        "speed_score": f"{speed} ({row['speed_class']})",
        "failure_risk": f"{round(failure, 1)} ({row['last_maintenance_days']} days since maint)"
    }
    
    return pd.Series([ci, json.dumps(explanation)])


# ─── XGBoost Urgency Classifier ──────────────────────────────────────────────

def _create_training_labels(df: pd.DataFrame) -> pd.Series:
    """
    Generate synthetic 'urgent' labels for training.
    """
    urgent = (
        ((df["severity"] >= 4) & (df["days_overdue"] > 15))
        | (df["severity"] == 5)
        | ((df["days_overdue"] > 45) & (df["severity"] >= 3))
        | df.get("emergency", False)
    )
    return urgent.astype(int)


def train_urgency_model(df: pd.DataFrame) -> tuple:
    """
    Train an XGBoost classifier to predict task urgency.
    Returns: (model, label_encoders, accuracy)
    """
    feature_df = df[["severity", "days_overdue", "required_hours",
                     "last_maintenance_days"]].copy()

    le_speed = LabelEncoder()
    feature_df["speed_class_enc"] = le_speed.fit_transform(df["speed_class"])

    le_dept = LabelEncoder()
    feature_df["department_enc"] = le_dept.fit_transform(df["department"])

    labels = _create_training_labels(df)

    # Avoid crash if all labels are 0 or 1
    if len(labels.unique()) < 2:
        return None, {"speed": le_speed, "department": le_dept}, 1.0

    X_train, X_test, y_train, y_test = train_test_split(
        feature_df, labels, test_size=0.2, random_state=42, stratify=labels
    )

    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
        verbosity=0,
    )
    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)

    return model, {"speed": le_speed, "department": le_dept}, accuracy


def predict_urgency_probability(model, encoders, df: pd.DataFrame) -> np.ndarray:
    """Predict urgency probability for each task using XGBoost."""
    if model is None:
        return np.zeros(len(df))
        
    feature_df = df[["severity", "days_overdue", "required_hours",
                     "last_maintenance_days"]].copy()
    feature_df["speed_class_enc"] = encoders["speed"].transform(df["speed_class"])
    feature_df["department_enc"] = encoders["department"].transform(df["department"])

    probas = model.predict_proba(feature_df)[:, 1]
    return probas


# ─── Combined Scoring Pipeline ───────────────────────────────────────────────

def compute_criticality_scores(df: pd.DataFrame, xgb_blend_weight: float = 0.2) -> pd.DataFrame:
    """
    Compute Criticality Index for all tasks using both heuristic and XGBoost.
    """
    print("=" * 60)
    print("  AI Block Planning - Task Prioritization")
    print("=" * 60)

    result = df.copy()

    # Step 1: Heuristic scoring
    print("\n  [1/3] Computing heuristic Criticality Index...")
    heuristics = result.apply(heuristic_criticality_index, axis=1)
    result["heuristic_ci"] = heuristics[0]
    result["score_explanation"] = heuristics[1]

    # Step 2: XGBoost urgency
    print("  [2/3] Training XGBoost urgency classifier...")
    model, encoders, accuracy = train_urgency_model(result)
    print(f"         Model accuracy: {accuracy:.1%}")

    urgency_probs = predict_urgency_probability(model, encoders, result)
    result["xgb_urgency_prob"] = np.round(urgency_probs, 4)

    # Step 3: Blend scores
    print("  [3/3] Blending heuristic + XGBoost scores...")
    heuristic_weight = 1.0 - xgb_blend_weight
    
    # Overwrite blend if emergency
    is_emergency = result.get("emergency", pd.Series([False]*len(result)))
    
    result["criticality_index"] = np.where(
        is_emergency,
        100.0,
        np.round(
            heuristic_weight * result["heuristic_ci"] + xgb_blend_weight * (result["xgb_urgency_prob"] * 100),
            2
        )
    )

    result["criticality_index"] = result["criticality_index"].clip(0, 100)

    # Priority tiers
    result["priority_tier"] = pd.cut(
        result["criticality_index"],
        bins=[0, 25, 50, 75, 100],
        labels=["Low", "Medium", "High", "Critical"],
        include_lowest=True,
    )

    tier_counts = result["priority_tier"].value_counts()
    print(f"\n  Priority Distribution:")
    for tier in ["Critical", "High", "Medium", "Low"]:
        count = tier_counts.get(tier, 0)
        print(f"    {tier:10s}: {count:3d} tasks")

    avg_ci = result["criticality_index"].mean()
    print(f"\n  Average Criticality Index: {avg_ci:.1f}")
    print(f"{'-' * 60}\n")

    return result


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database.loader import load_data

    data = load_data()
    scored = compute_criticality_scores(data["all_tasks"])
    print(scored[["task_id", "department", "defect_type", "severity", "safety_impact", "operational_impact",
                   "criticality_index", "priority_tier"]].head(20).to_string())
