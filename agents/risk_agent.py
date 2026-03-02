"""
Risk Agent — Identifies and classifies project risks from real DB data.
Analyzes daily report gaps, cost overruns, manpower drops, and approval delays.
"""

import pandas as pd
from datetime import datetime, timedelta


def assess_risk(
    project: pd.Series,
    expenses_df: pd.DataFrame,
    manpower_df: pd.DataFrame,
    approvals_df: pd.DataFrame,
    materials_df: pd.DataFrame,
) -> dict:
    """
    Assess overall risk for a project based on multiple data signals.

    Returns:
        dict with risk_level, confidence, contributing_factors[], and details.
    """
    factors = []
    risk_scores = []

    # ── 1. Cost Overrun Risk ──
    total_budget = float(project.get("total_price") or 0)
    total_spent = float(expenses_df["amount"].sum()) if not expenses_df.empty else 0.0

    if total_budget > 0:
        cost_ratio = total_spent / total_budget
        if cost_ratio > 1.2:
            factors.append(f"🔴 Cost overrun: {(cost_ratio-1)*100:.0f}% over budget")
            risk_scores.append(9)
        elif cost_ratio > 1.0:
            factors.append(f"🟠 Cost overrun: {(cost_ratio-1)*100:.0f}% over budget")
            risk_scores.append(7)
        elif cost_ratio > 0.85:
            factors.append(f"🟡 Budget utilization at {cost_ratio*100:.0f}%")
            risk_scores.append(4)
        else:
            risk_scores.append(1)

    # ── 2. Schedule Risk ──
    planned_end = _safe_date(project.get("planned_end_date"))
    if planned_end:
        days_to_deadline = (planned_end - datetime.now().date()).days
        if days_to_deadline < 0:
            factors.append(f"🔴 Project is {abs(days_to_deadline)} days overdue")
            risk_scores.append(10)
        elif days_to_deadline < 7:
            factors.append(f"🟠 Only {days_to_deadline} days to deadline")
            risk_scores.append(7)
        elif days_to_deadline < 30:
            factors.append(f"🟡 {days_to_deadline} days to deadline")
            risk_scores.append(4)
        else:
            risk_scores.append(1)

    # ── 3. Manpower Consistency Risk ──
    if not manpower_df.empty:
        mp_risk = _analyze_manpower_trend(manpower_df)
        if mp_risk["drop_pct"] > 40:
            factors.append(f"🔴 Manpower dropped {mp_risk['drop_pct']:.0f}% (last 7 days vs prior)")
            risk_scores.append(8)
        elif mp_risk["drop_pct"] > 20:
            factors.append(f"🟠 Manpower dropped {mp_risk['drop_pct']:.0f}% recently")
            risk_scores.append(5)
        elif mp_risk["drop_pct"] > 0:
            factors.append(f"🟡 Slight manpower dip: {mp_risk['drop_pct']:.0f}%")
            risk_scores.append(3)
        else:
            risk_scores.append(1)
    else:
        factors.append("⚪ No manpower data available")
        risk_scores.append(5)

    # ── 4. Daily Report Gaps ──
    if not approvals_df.empty:
        gap_days = _check_report_gaps(approvals_df)
        if gap_days > 7:
            factors.append(f"🔴 No daily reports for {gap_days} days")
            risk_scores.append(8)
        elif gap_days > 3:
            factors.append(f"🟠 Daily report gap: {gap_days} days")
            risk_scores.append(5)
        elif gap_days > 1:
            factors.append(f"🟡 Minor report gap: {gap_days} days")
            risk_scores.append(3)
        else:
            risk_scores.append(1)
    else:
        factors.append("⚪ No approval data available")
        risk_scores.append(5)

    # ── 5. Material Supply Risk ──
    if not materials_df.empty and "scope_quantity" in materials_df.columns:
        mat_risk = _analyze_material_usage(materials_df)
        if mat_risk["overused_items"] > 0:
            factors.append(f"🟠 {mat_risk['overused_items']} material(s) exceeding scope")
            risk_scores.append(6)
        else:
            risk_scores.append(1)
    else:
        risk_scores.append(2)

    # ── Aggregate Risk ──
    if risk_scores:
        avg_score = sum(risk_scores) / len(risk_scores)
        max_score = max(risk_scores)
        # Weight the max score more heavily than average
        final_score = (avg_score * 0.4) + (max_score * 0.6)
    else:
        final_score = 5.0

    risk_level = _score_to_level(final_score)
    confidence = min(95, 50 + len(risk_scores) * 8)  # More data = more confidence

    return {
        "risk_level": risk_level,
        "risk_score": round(final_score, 1),
        "confidence": confidence,
        "factors": factors,
        "total_signals_analyzed": len(risk_scores),
    }


def _analyze_manpower_trend(mp_df: pd.DataFrame) -> dict:
    """Compare recent vs prior manpower levels."""
    try:
        df = mp_df.copy()
        df["reported_date"] = pd.to_datetime(df["reported_date"], errors="coerce")
        df = df.dropna(subset=["reported_date"])

        if df.empty:
            return {"drop_pct": 0}

        today = pd.Timestamp.now()
        recent = df[df["reported_date"] >= today - timedelta(days=7)]
        prior = df[(df["reported_date"] >= today - timedelta(days=14)) &
                    (df["reported_date"] < today - timedelta(days=7))]

        recent_avg = recent["man_count"].sum() if not recent.empty else 0
        prior_avg = prior["man_count"].sum() if not prior.empty else 0

        if prior_avg > 0:
            drop_pct = ((prior_avg - recent_avg) / prior_avg) * 100
        else:
            drop_pct = 0

        return {"drop_pct": max(0, drop_pct), "recent_avg": recent_avg, "prior_avg": prior_avg}
    except Exception:
        return {"drop_pct": 0}


def _check_report_gaps(approvals_df: pd.DataFrame) -> int:
    """Check how many days since the last daily report."""
    try:
        df = approvals_df.copy()
        df["reported_date"] = pd.to_datetime(df["reported_date"], errors="coerce")
        df = df.dropna(subset=["reported_date"])

        if df.empty:
            return 30  # No data = big gap

        last_report = df["reported_date"].max()
        gap = (pd.Timestamp.now() - last_report).days
        return max(0, gap)
    except Exception:
        return 0


def _analyze_material_usage(materials_df: pd.DataFrame) -> dict:
    """Check if any material usage exceeds scoped quantity."""
    try:
        df = materials_df.copy()
        df["used_material"] = pd.to_numeric(df["used_material"], errors="coerce").fillna(0)
        df["scope_quantity"] = pd.to_numeric(df["scope_quantity"], errors="coerce").fillna(0)

        if "line_item_name" in df.columns:
            grouped = df.groupby("line_item_name").agg(
                total_used=("used_material", "sum"),
                scope=("scope_quantity", "first")
            )
            overused = grouped[grouped["total_used"] > grouped["scope"]]
            return {"overused_items": len(overused)}
        return {"overused_items": 0}
    except Exception:
        return {"overused_items": 0}


def _score_to_level(score: float) -> str:
    """Convert numeric risk score to label."""
    if score >= 8:
        return "CRITICAL"
    elif score >= 6:
        return "HIGH"
    elif score >= 4:
        return "MEDIUM"
    else:
        return "LOW"


def _safe_date(val):
    """Safely extract a date from various types."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, pd.Timestamp):
        return val.date()
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None
