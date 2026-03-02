"""
Decision Agent — Generates actionable recommendations based on
progress and risk analysis from real DB data.
"""


def generate_recommendations(progress: dict, risk: dict) -> list[dict]:
    """
    Generate actionable recommendations based on progress and risk analysis.

    Args:
        progress: Output from progress_agent.analyze_progress()
        risk: Output from risk_agent.assess_risk()

    Returns:
        List of recommendation dicts with keys: priority, category, action, reason.
    """
    recommendations = []

    # ── Schedule-based recommendations ──
    health = progress.get("health", "")
    days_remaining = progress.get("days_remaining")

    if health == "OVERDUE":
        recommendations.append({
            "priority": "🔴 CRITICAL",
            "category": "Schedule",
            "action": "Escalate to Director immediately. Request deadline extension or deploy additional resources.",
            "reason": f"Project is {abs(days_remaining)} days past the planned end date.",
        })
    elif health == "CRITICAL":
        recommendations.append({
            "priority": "🔴 CRITICAL",
            "category": "Budget",
            "action": "Freeze non-essential spending. Conduct emergency budget review with finance.",
            "reason": f"Cost overrun is at {progress['cost_overrun_pct']:.1f}% which exceeds the 20% threshold.",
        })
    elif health == "AT_RISK":
        if days_remaining is not None and days_remaining < 7:
            recommendations.append({
                "priority": "🟠 HIGH",
                "category": "Schedule",
                "action": "Deploy overtime shifts or additional manpower to meet the deadline.",
                "reason": f"Only {days_remaining} days remaining with significant work pending.",
            })
        if progress.get("cost_overrun_pct", 0) > 10:
            recommendations.append({
                "priority": "🟠 HIGH",
                "category": "Budget",
                "action": "Review expense categories. Identify top 3 cost drivers and apply cost controls.",
                "reason": f"Budget overrun at {progress['cost_overrun_pct']:.1f}%.",
            })

    # ── Cost efficiency recommendation ──
    time_pct = progress.get("time_progress_pct", 0)
    cost_pct = progress.get("cost_progress_pct", 0)

    if cost_pct > 0 and time_pct > 0:
        if cost_pct > time_pct + 15:
            recommendations.append({
                "priority": "🟡 MEDIUM",
                "category": "Efficiency",
                "action": "Spending is outpacing progress. Investigate if material procurement is front-loaded or if there is waste.",
                "reason": f"Cost progress ({cost_pct:.0f}%) is ahead of time progress ({time_pct:.0f}%) by {cost_pct - time_pct:.0f} points.",
            })
        elif time_pct > cost_pct + 20:
            recommendations.append({
                "priority": "🟢 INFO",
                "category": "Efficiency",
                "action": "Project is under-budget relative to timeline. Verify that no critical procurements have been deferred.",
                "reason": f"Time progress ({time_pct:.0f}%) ahead of cost ({cost_pct:.0f}%).",
            })

    # ── Risk-factor-based recommendations ──
    for factor in risk.get("factors", []):
        factor_lower = factor.lower()

        if "manpower dropped" in factor_lower and "🔴" in factor:
            recommendations.append({
                "priority": "🔴 CRITICAL",
                "category": "Manpower",
                "action": "Investigate manpower shortage. Contact labour contractor for additional deployment within 48 hours.",
                "reason": factor,
            })
        elif "manpower dropped" in factor_lower and "🟠" in factor:
            recommendations.append({
                "priority": "🟠 HIGH",
                "category": "Manpower",
                "action": "Monitor manpower levels daily. Alert site engineer to ensure adequate workforce.",
                "reason": factor,
            })
        elif "no daily reports" in factor_lower or "report gap" in factor_lower:
            recommendations.append({
                "priority": "🟠 HIGH",
                "category": "Compliance",
                "action": "Ensure site engineer submits daily reports. Set up automated reminders.",
                "reason": factor,
            })
        elif "material" in factor_lower and "exceeding" in factor_lower:
            recommendations.append({
                "priority": "🟡 MEDIUM",
                "category": "Materials",
                "action": "Review material consumption rates. Check for wastage or scope changes requiring BOQ revision.",
                "reason": factor,
            })

    # ── Ensure at least one recommendation ──
    if not recommendations:
        risk_level = risk.get("risk_level", "LOW")
        if risk_level == "LOW":
            recommendations.append({
                "priority": "🟢 INFO",
                "category": "General",
                "action": "Project is progressing well. Continue monitoring daily reports and expenses.",
                "reason": "All risk indicators are within acceptable thresholds.",
            })
        else:
            recommendations.append({
                "priority": "🟡 MEDIUM",
                "category": "General",
                "action": "Review project status in detail. Minor concerns detected across multiple areas.",
                "reason": f"Overall risk level: {risk_level}.",
            })

    # Sort by priority
    priority_order = {"🔴 CRITICAL": 0, "🟠 HIGH": 1, "🟡 MEDIUM": 2, "🟢 INFO": 3}
    recommendations.sort(key=lambda r: priority_order.get(r["priority"], 99))

    return recommendations
