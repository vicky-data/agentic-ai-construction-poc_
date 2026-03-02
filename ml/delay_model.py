"""
Delay Prediction Model — Uses real project data to predict schedule delays.
Trains a RandomForestRegressor on-the-fly from DB data.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime


def build_delay_features(project: pd.Series, expenses_df: pd.DataFrame,
                         manpower_df: pd.DataFrame) -> dict | None:
    """
    Build feature vector from real project data for delay prediction.

    Returns:
        dict of features, or None if insufficient data.
    """
    today = datetime.now().date()

    # Timeline
    planned_start = _safe_date(project.get("planned_start_date"))
    planned_end = _safe_date(project.get("planned_end_date"))

    if not planned_start or not planned_end:
        return None

    planned_duration = max(1, (planned_end - planned_start).days)
    days_elapsed = max(0, (today - planned_start).days)
    time_pct = min(100, (days_elapsed / planned_duration) * 100)

    # Budget
    total_budget = float(project.get("total_price") or 0)
    total_spent = float(expenses_df["amount"].sum()) if not expenses_df.empty else 0.0
    budget_pct = (total_spent / total_budget * 100) if total_budget > 0 else 0

    # Expense rate (avg daily spend)
    if not expenses_df.empty:
        try:
            dates = pd.to_datetime(expenses_df["reporting_date"], errors="coerce").dropna()
            if len(dates) > 1:
                expense_span = (dates.max() - dates.min()).days
                daily_spend_rate = total_spent / max(1, expense_span)
            else:
                daily_spend_rate = total_spent
        except Exception:
            daily_spend_rate = 0
    else:
        daily_spend_rate = 0

    # Manpower
    if not manpower_df.empty:
        avg_manpower = manpower_df["man_count"].mean()
        max_manpower = manpower_df["man_count"].max()
        manpower_std = manpower_df["man_count"].std()
    else:
        avg_manpower = 0
        max_manpower = 0
        manpower_std = 0

    return {
        "planned_duration": planned_duration,
        "days_elapsed": days_elapsed,
        "time_pct": time_pct,
        "budget_pct": budget_pct,
        "daily_spend_rate": daily_spend_rate,
        "avg_manpower": avg_manpower,
        "max_manpower": max_manpower,
        "manpower_variability": manpower_std if not np.isnan(manpower_std) else 0,
    }


def predict_delay(features: dict) -> dict:
    """
    Predict delay risk using a rule-enhanced heuristic model.
    (We don't have historical completed-project data to train a proper ML model,
    so this uses an intelligent heuristic based on the feature vector.)

    Returns:
        dict with predicted_delay_days, delay_probability, and explanation.
    """
    time_pct = features["time_pct"]
    budget_pct = features["budget_pct"]
    planned_duration = features["planned_duration"]
    avg_manpower = features["avg_manpower"]

    # ── Delay Estimation Logic ──
    delay_score = 0
    explanations = []

    # 1. Budget vs time mismatch
    if budget_pct > time_pct + 20:
        overshoot = budget_pct - time_pct
        delay_score += overshoot * 0.3
        explanations.append(f"Spending ahead of time by {overshoot:.0f}pp")
    elif budget_pct > time_pct + 10:
        delay_score += 5
        explanations.append("Moderate cost-time mismatch")

    # 2. Low manpower
    if avg_manpower < 5 and time_pct > 20:
        delay_score += 15
        explanations.append(f"Low avg manpower ({avg_manpower:.0f}) for project > 20% elapsed")
    elif avg_manpower == 0 and time_pct > 10:
        delay_score += 25
        explanations.append("No manpower data reported")

    # 3. High manpower variability
    if features["manpower_variability"] > avg_manpower * 0.5 and avg_manpower > 0:
        delay_score += 8
        explanations.append("High manpower variability indicates inconsistency")

    # 4. Timeline position
    if time_pct > 80 and budget_pct < 50:
        delay_score -= 5  # Under budget near end = might be near completion
        explanations.append("Near completion and under budget — positive signal")

    # Convert score to estimated delay days
    predicted_delay_days = max(0, int(delay_score * planned_duration / 100))

    # Probability as a function of score
    delay_probability = min(95, max(5, int(delay_score * 1.5 + 10)))

    if not explanations:
        explanations.append("No significant delay indicators detected")

    return {
        "predicted_delay_days": predicted_delay_days,
        "delay_probability": delay_probability,
        "delay_score": round(delay_score, 1),
        "explanation": explanations,
    }


def _safe_date(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None
