"""
Progress Agent — Analyzes project timeline and cost progress using real DB data.
Compares planned vs actual dates and budgets to determine progress health.
"""

import pandas as pd
from datetime import datetime, date


def analyze_progress(project: pd.Series, expenses_df: pd.DataFrame) -> dict:
    """
    Analyze project progress by comparing planned vs actual timeline and costs.

    Args:
        project: A single row from the project table.
        expenses_df: DataFrame of daily expenses for this project.

    Returns:
        dict with progress metrics and health status.
    """
    today = datetime.now().date()

    # ── Timeline Analysis ──
    planned_start = _to_date(project.get("planned_start_date"))
    planned_end = _to_date(project.get("planned_end_date"))
    actual_start = _to_date(project.get("actual_start_date"))
    actual_end = _to_date(project.get("actual_end_date"))
    exec_start = _to_date(project.get("execution_start_date"))
    exec_end = _to_date(project.get("execution_end_date"))

    # Use execution dates if available, otherwise planned
    effective_start = exec_start or actual_start or planned_start
    effective_end = exec_end or actual_end or planned_end

    # Total planned duration
    if planned_start and planned_end:
        planned_duration = (planned_end - planned_start).days
    else:
        planned_duration = 0

    # Days elapsed
    if effective_start:
        days_elapsed = (today - effective_start).days
        days_elapsed = max(0, days_elapsed)
    else:
        days_elapsed = 0

    # Days remaining
    if planned_end:
        days_remaining = (planned_end - today).days
    else:
        days_remaining = None

    # Time progress percentage
    if planned_duration > 0:
        time_progress_pct = min(100.0, round((days_elapsed / planned_duration) * 100, 1))
    else:
        time_progress_pct = 0.0

    # ── Cost Analysis ──
    total_budget = float(project.get("total_price") or 0)
    total_spent = float(expenses_df["amount"].sum()) if not expenses_df.empty else 0.0
    budget_remaining = total_budget - total_spent if total_budget > 0 else 0.0

    if total_budget > 0:
        cost_progress_pct = round((total_spent / total_budget) * 100, 1)
        cost_overrun = max(0, total_spent - total_budget)
        cost_overrun_pct = round((cost_overrun / total_budget) * 100, 1)
    else:
        cost_progress_pct = 0.0
        cost_overrun = 0.0
        cost_overrun_pct = 0.0

    # ── Schedule Variance ──
    # If we've used more time % than budget %, project may be behind
    schedule_variance = time_progress_pct - cost_progress_pct

    # ── Health Status ──
    if days_remaining is not None and days_remaining < 0:
        health = "OVERDUE"
    elif cost_overrun_pct > 20:
        health = "CRITICAL"
    elif cost_overrun_pct > 10 or (days_remaining is not None and days_remaining < 7):
        health = "AT_RISK"
    elif abs(schedule_variance) > 20:
        health = "WARNING"
    else:
        health = "ON_TRACK"

    return {
        "planned_start": planned_start,
        "planned_end": planned_end,
        "actual_start": actual_start,
        "actual_end": actual_end,
        "effective_start": effective_start,
        "effective_end": effective_end,
        "planned_duration_days": planned_duration,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "time_progress_pct": time_progress_pct,
        "total_budget": total_budget,
        "total_spent": total_spent,
        "budget_remaining": budget_remaining,
        "cost_progress_pct": cost_progress_pct,
        "cost_overrun": cost_overrun,
        "cost_overrun_pct": cost_overrun_pct,
        "schedule_variance": schedule_variance,
        "health": health,
        "status": project.get("status", "Unknown"),
    }


def _to_date(val) -> date | None:
    """Safely convert various date formats to a Python date."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, pd.Timestamp):
        return val.date()
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None
