"""
🎯 Director Dashboard — Organization-level analytics
Access: Director, Admin
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import require_role, get_current_user, init_session
from db import is_demo_mode
from queries import (
    get_all_projects, get_project_expenses, get_total_expenses_by_project,
    get_project_manpower, get_project_materials, get_project_machinery,
    get_project_boq_scope, get_daily_report_approvals, get_mrs_status, get_project_users,
)
from agents.progress_agent import analyze_progress
from agents.risk_agent import assess_risk
from agents.decision_agent import generate_recommendations
from services.report_service import generate_pdf_report

st.set_page_config(page_title="Director Dashboard", page_icon="🎯", layout="wide")

init_session()
require_role("Director", "Admin")
user = get_current_user()

# ── Header ──
st.markdown("""
<div style="text-align:center; padding:10px 0 20px 0;">
    <h1 style="color:#f8f9fa; font-weight:300;">🎯 Director Dashboard</h1>
    <p style="color:#8c9097; letter-spacing:1.5px; text-transform:uppercase;">
        Organization-Level Analytics
    </p>
</div>
""", unsafe_allow_html=True)

# ── Load All Projects ──
projects_df = get_all_projects()
if projects_df.empty:
    st.warning("No projects found.")
    st.stop()

# Date Range Filter
st.sidebar.markdown("### 📅 Date Filter")
date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime.now().date() - timedelta(days=90), datetime.now().date()),
    key="dir_date_range",
)

# ── Org-Level KPIs ──
total_budget = 0
total_spent = 0
at_risk_count = 0
all_progress = []

for _, proj in projects_df.iterrows():
    pid = proj["id"]
    expenses = get_project_expenses(pid)
    manpower = get_project_manpower(pid)
    materials = get_project_materials(pid)
    approvals = get_daily_report_approvals(pid)

    progress = analyze_progress(proj, expenses)
    risk = assess_risk(proj, expenses, manpower, approvals, materials)

    total_budget += progress["total_budget"]
    total_spent += progress["total_spent"]
    if risk["risk_level"] in ("HIGH", "CRITICAL"):
        at_risk_count += 1

    all_progress.append({
        "Project": proj.get("project_name", f"#{pid}"),
        "Status": proj.get("status", "N/A"),
        "Health": progress["health"],
        "Budget": progress["total_budget"],
        "Spent": progress["total_spent"],
        "Time %": progress["time_progress_pct"],
        "Cost %": progress["cost_progress_pct"],
        "Days Left": progress["days_remaining"],
        "Risk": risk["risk_level"],
    })

# KPI Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:24px; text-align:center;">
        <p style="font-size:2.2rem; font-weight:300; color:#f8f9fa; margin:0;">{len(projects_df)}</p>
        <p style="font-size:0.75rem; color:#8c9097; text-transform:uppercase; letter-spacing:1.5px; margin-top:10px;">Total Projects</p>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:24px; text-align:center;">
        <p style="font-size:2.2rem; font-weight:300; color:#f8f9fa; margin:0;">₹{total_budget/1e7:.1f}Cr</p>
        <p style="font-size:0.75rem; color:#8c9097; text-transform:uppercase; letter-spacing:1.5px; margin-top:10px;">Total Budget</p>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:24px; text-align:center;">
        <p style="font-size:2.2rem; font-weight:300; color:#f8f9fa; margin:0;">₹{total_spent/1e7:.1f}Cr</p>
        <p style="font-size:0.75rem; color:#8c9097; text-transform:uppercase; letter-spacing:1.5px; margin-top:10px;">Total Spent</p>
    </div>""", unsafe_allow_html=True)
with c4:
    risk_color = "#ef4444" if at_risk_count > 0 else "#10b981"
    st.markdown(f"""<div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:24px; text-align:center;">
        <p style="font-size:2.2rem; font-weight:300; color:{risk_color}; margin:0;">{at_risk_count}</p>
        <p style="font-size:0.75rem; color:#8c9097; text-transform:uppercase; letter-spacing:1.5px; margin-top:10px;">At Risk</p>
    </div>""", unsafe_allow_html=True)

# ── Projects Table ──
st.divider()
st.markdown('<p style="font-size:1.2rem; color:#e5e7eb; font-weight:400;">📋 All Projects Overview</p>', unsafe_allow_html=True)

progress_table = pd.DataFrame(all_progress)
st.dataframe(progress_table, use_container_width=True, height=250)

# ── S-Curve: Planned vs Actual Progress ──
st.divider()
col_s, col_pie = st.columns(2)

with col_s:
    st.markdown('<p style="font-size:1.2rem; color:#e5e7eb; font-weight:400;">📈 S-Curve — Planned vs Actual Spend</p>', unsafe_allow_html=True)

    # Aggregate expenses across all projects
    all_expenses = []
    for _, proj in projects_df.iterrows():
        exp = get_project_expenses(proj["id"])
        if not exp.empty:
            all_expenses.append(exp)

    if all_expenses:
        combined = pd.concat(all_expenses, ignore_index=True)
        combined["reporting_date"] = pd.to_datetime(combined["reporting_date"], errors="coerce")
        combined = combined.dropna(subset=["reporting_date"]).sort_values("reporting_date")

        daily = combined.groupby("reporting_date")["amount"].sum().reset_index()
        daily["Actual Cumulative"] = daily["amount"].cumsum()

        # Planned: linear distribution of total budget
        total_days = (daily["reporting_date"].max() - daily["reporting_date"].min()).days or 1
        daily["Planned Cumulative"] = [(total_budget / total_days) * (i + 1) for i in range(len(daily))]

        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(
            x=daily["reporting_date"], y=daily["Planned Cumulative"],
            name="Planned", line=dict(color="#6b7280", dash="dash", width=2),
        ))
        fig_s.add_trace(go.Scatter(
            x=daily["reporting_date"], y=daily["Actual Cumulative"],
            name="Actual", line=dict(color="#d4af37", width=3),
            fill="tozeroy", fillcolor="rgba(212,175,55,0.08)",
        ))
        fig_s.update_layout(
            height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#8c9097", margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Amount (₹)"),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_s, use_container_width=True)
    else:
        st.info("No expense data to plot S-Curve.")

# Expense Pie chart
with col_pie:
    st.markdown('<p style="font-size:1.2rem; color:#e5e7eb; font-weight:400;">💰 Expense Distribution</p>', unsafe_allow_html=True)
    if all_expenses:
        combined_cat = pd.concat(all_expenses)
        cat_totals = combined_cat.groupby("parent_type")["amount"].sum().reset_index()
        fig_pie = px.pie(cat_totals, values="amount", names="parent_type", hole=0.45,
                         color_discrete_sequence=["#d4af37", "#10b981", "#ef4444", "#6366f1", "#f59e0b"])
        fig_pie.update_layout(
            height=350, paper_bgcolor="rgba(0,0,0,0)", font_color="#8c9097",
            margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expense data available.")

# ── PDF Export ──
st.divider()
if st.button("📄 Download Organization Report (PDF)", use_container_width=True):
    org_progress = {
        "health": "AT_RISK" if at_risk_count > 0 else "ON_TRACK",
        "total_budget": total_budget, "total_spent": total_spent,
        "time_progress_pct": 0, "days_remaining": None,
        "cost_progress_pct": round(total_spent / total_budget * 100, 1) if total_budget > 0 else 0,
        "cost_overrun": max(0, total_spent - total_budget),
        "cost_overrun_pct": 0, "planned_start": None, "planned_end": None,
    }
    org_risk = {"risk_level": "HIGH" if at_risk_count > 0 else "LOW", "risk_score": 5, "confidence": 80, "factors": []}
    pdf = generate_pdf_report("All Projects — Organization Report", org_progress, org_risk, [])
    st.download_button("⬇️ Download PDF", data=pdf,
                        file_name=f"org_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf", use_container_width=True)

# Footer
st.markdown("""<div style="text-align:center; padding:20px 0; color:#4b5563; font-size:0.8rem;">
    🏗️ ConstructIQ — Director View
</div>""", unsafe_allow_html=True)
