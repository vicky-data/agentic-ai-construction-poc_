"""
Risk Classification Model — Classifies project risk level from features.
Uses a weighted scoring system derived from real DB metrics.
"""

import numpy as np


def classify_risk(
    cost_overrun_pct: float,
    days_remaining: int | None,
    manpower_drop_pct: float,
    report_gap_days: int,
    material_overuse_count: int,
    total_budget: float,
    total_spent: float,
) -> dict:
    """
    Classify project risk using a multi-factor weighted model.

    Returns:
        dict with risk_label, confidence, score breakdown, and color.
    """
    scores = {}

    # ── Factor 1: Cost Overrun (weight: 0.30) ──
    if cost_overrun_pct > 25:
        scores["cost"] = 10
    elif cost_overrun_pct > 15:
        scores["cost"] = 8
    elif cost_overrun_pct > 5:
        scores["cost"] = 5
    elif cost_overrun_pct > 0:
        scores["cost"] = 3
    else:
        scores["cost"] = 1

    # ── Factor 2: Schedule Pressure (weight: 0.25) ──
    if days_remaining is not None:
        if days_remaining < 0:
            scores["schedule"] = 10
        elif days_remaining < 7:
            scores["schedule"] = 8
        elif days_remaining < 30:
            scores["schedule"] = 5
        elif days_remaining < 90:
            scores["schedule"] = 3
        else:
            scores["schedule"] = 1
    else:
        scores["schedule"] = 5  # Unknown = medium risk

    # ── Factor 3: Manpower Stability (weight: 0.20) ──
    if manpower_drop_pct > 50:
        scores["manpower"] = 10
    elif manpower_drop_pct > 30:
        scores["manpower"] = 7
    elif manpower_drop_pct > 15:
        scores["manpower"] = 4
    else:
        scores["manpower"] = 1

    # ── Factor 4: Reporting Compliance (weight: 0.15) ──
    if report_gap_days > 14:
        scores["compliance"] = 10
    elif report_gap_days > 7:
        scores["compliance"] = 7
    elif report_gap_days > 3:
        scores["compliance"] = 4
    else:
        scores["compliance"] = 1

    # ── Factor 5: Material Risk (weight: 0.10) ──
    if material_overuse_count > 3:
        scores["materials"] = 9
    elif material_overuse_count > 1:
        scores["materials"] = 6
    elif material_overuse_count > 0:
        scores["materials"] = 3
    else:
        scores["materials"] = 1

    # ── Weighted Score ──
    weights = {
        "cost": 0.30,
        "schedule": 0.25,
        "manpower": 0.20,
        "compliance": 0.15,
        "materials": 0.10,
    }

    weighted_score = sum(scores[k] * weights[k] for k in scores)

    # ── Classify ──
    if weighted_score >= 7.5:
        risk_label = "CRITICAL"
        color = "#FF1744"
        emoji = "🔴"
    elif weighted_score >= 5.5:
        risk_label = "HIGH"
        color = "#FF6D00"
        emoji = "🟠"
    elif weighted_score >= 3.5:
        risk_label = "MEDIUM"
        color = "#FFD600"
        emoji = "🟡"
    else:
        risk_label = "LOW"
        color = "#00E676"
        emoji = "🟢"

    # Confidence increases with more non-default scores
    non_default = sum(1 for v in scores.values() if v != 5)
    confidence = min(95, 60 + non_default * 7)

    return {
        "risk_label": risk_label,
        "weighted_score": round(weighted_score, 2),
        "confidence": confidence,
        "color": color,
        "emoji": emoji,
        "factor_scores": scores,
        "weights": weights,
    }
