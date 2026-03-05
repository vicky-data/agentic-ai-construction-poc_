"""
💰 Budget & Analytics — Achievement tracking, S-Curve, date range analysis
Access: Director, Project Manager, Admin
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import require_role, get_current_user, init_session
from queries import (
    get_all_projects, get_project_expenses, get_project_manpower,
    get_project_materials, get_project_boq_scope, get_project_machinery,
)
from agents.progress_agent import analyze_progress

st.set_page_config(page_title="Budget & Analytics", page_icon="💰", layout="wide")

init_session()
require_role("Director", "Project Manager", "Admin", "Project Engineer")
user = get_current_user()

st.markdown("""
<div style="text-align:center; padding:10px 0 20px 0;">
    <h1 style="color:#f8f9fa; font-weight:300;">💰 Budget & Analytics</h1>
    <p style="color:#8c9097; letter-spacing:1.5px; text-transform:uppercase;">
        Performance Tracking • S-Curve • Achievements
    </p>
</div>
""", unsafe_allow_html=True)

projects_df = get_all_projects()
if projects_df.empty:
    st.warning("No projects found.")
    st.stop()

# Sidebar project selector & date range
def _fmt_proj(i):
    row = projects_df.iloc[i]
    pname = row.get("project_name", "Project #" + str(row["id"]))
    return pname + " (#" + str(row["id"]) + ")"

sel_idx = st.selectbox("🏗️ Select Project", range(len(projects_df)), format_func=_fmt_proj)
project = projects_df.iloc[sel_idx]
pid = project["id"]

date_range = st.date_input("📅 Date Range", value=(
    datetime.now().date() - timedelta(days=90), datetime.now().date()
))

# Load data
expenses_df = get_project_expenses(pid)
manpower_df = get_project_manpower(pid)
materials_df = get_project_materials(pid)
machinery_df = get_project_machinery(pid)
boq_df = get_project_boq_scope(pid)
progress = analyze_progress(project, expenses_df)

# ── Tabs ──
tab_budget, tab_scurve, tab_achieve, tab_charts = st.tabs([
    "📊 Budget Overview", "📈 S-Curve", "🎯 Achievements", "📉 Charts & Analytics"
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: BUDGET OVERVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_budget:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Budget", f"₹{progress['total_budget']/1e7:.2f}Cr")
    with c2:
        st.metric("Total Spent", f"₹{progress['total_spent']/1e7:.2f}Cr")
    with c3:
        st.metric("Budget Used", f"{progress['cost_progress_pct']:.1f}%")
    with c4:
        overrun = progress.get("cost_overrun", 0)
        st.metric("Cost Overrun", f"₹{overrun/1e5:.1f}L",
                  delta=f"{overrun/progress['total_budget']*100:.1f}%" if progress["total_budget"] > 0 else "0%",
                  delta_color="inverse")

    # Budget upload
    st.divider()
    st.markdown("### 📤 Upload Budget (CSV)")
    st.caption("CSV Format: category, allocated_amount, description")
    budget_file = st.file_uploader("Upload Budget CSV", type=["csv"], key="budget_upload")
    if budget_file:
        try:
            budget_df = pd.read_csv(budget_file)
            st.success(f"✅ Uploaded {len(budget_df)} budget line items")
            st.dataframe(budget_df, use_container_width=True)
            if st.button("💾 Save Budget"):
                st.session_state["budget_data"] = budget_df
                st.success("Budget saved!")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    # Existing budget from session
    if st.session_state.get("budget_data") is not None:
        st.markdown("### 📋 Current Budget Allocation")
        st.dataframe(st.session_state["budget_data"], use_container_width=True)

    # Expense breakdown by category
    if not expenses_df.empty and "parent_type" in expenses_df.columns:
        st.divider()
        st.markdown("### 💰 Expense Breakdown by Category")
        cat_data = expenses_df.groupby("parent_type")["amount"].sum().reset_index()
        cat_data.columns = ["Category", "Amount"]
        cat_data["% of Total"] = (cat_data["Amount"] / cat_data["Amount"].sum() * 100).round(1)
        st.dataframe(cat_data.sort_values("Amount", ascending=False), use_container_width=True, hide_index=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: S-CURVE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_scurve:
    st.markdown("### 📈 S-Curve — Planned vs Actual Progress")

    if not expenses_df.empty:
        exp = expenses_df.copy()
        exp["reporting_date"] = pd.to_datetime(exp["reporting_date"], errors="coerce")
        exp = exp.dropna(subset=["reporting_date"]).sort_values("reporting_date")

        daily = exp.groupby("reporting_date")["amount"].sum().reset_index()
        daily["Actual"] = daily["amount"].cumsum()

        budget = progress["total_budget"]
        n = len(daily)
        daily["Planned"] = [budget / n * (i + 1) for i in range(n)] if n > 0 else []

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily["reporting_date"], y=daily["Planned"],
            name="📐 Planned", line=dict(color="#6b7280", dash="dash", width=2)))
        fig.add_trace(go.Scatter(x=daily["reporting_date"], y=daily["Actual"],
            name="📊 Actual", line=dict(color="#d4af37", width=3),
            fill="tozeroy", fillcolor="rgba(212,175,55,0.08)"))

        # Budget line
        if budget > 0:
            fig.add_hline(y=budget, line_dash="dot", line_color="#ef4444",
                          annotation_text=f"Budget: ₹{budget:,.0f}", annotation_font_color="#ef4444")

        fig.update_layout(
            height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#8c9097",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Date"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Amount (₹)"),
            legend=dict(orientation="h", y=-0.15),
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expense data available for S-Curve.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: ACHIEVEMENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_achieve:
    st.markdown("### 🎯 Achievement Tracking (Target vs Achieved)")

    # Get submitted reports for this project
    reports = [r for r in st.session_state.get("submitted_reports", [])
               if r.get("project_id") == pid and r.get("target_mt", 0) > 0]

    if reports:
        achieve_data = pd.DataFrame([{
            "Date": r["date"],
            "Timing": r["timing"],
            "Target (MT)": r["target_mt"],
            "Achieved (MT)": r["achieved_mt"],
            "Achievement %": r.get("achievement_pct", 0),
            "Submitted By": r["submitted_by"],
        } for r in reports])

        st.dataframe(achieve_data, use_container_width=True, hide_index=True)

        # Summary
        total_target = achieve_data["Target (MT)"].sum()
        total_achieved = achieve_data["Achieved (MT)"].sum()
        overall_pct = round(total_achieved / total_target * 100, 1) if total_target > 0 else 0

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Target (MT)", f"{total_target:.1f}")
        with c2:
            st.metric("Total Achieved (MT)", f"{total_achieved:.1f}")
        with c3:
            color = "#10b981" if overall_pct >= 80 else "#f59e0b" if overall_pct >= 50 else "#ef4444"
            st.markdown(f"""<div style="padding:10px; text-align:center;">
                <p style="font-size:2.5rem; font-weight:300; color:{color}; margin:0;">{overall_pct}%</p>
                <p style="font-size:0.75rem; color:#8c9097; text-transform:uppercase;">Overall Achievement</p>
            </div>""", unsafe_allow_html=True)
    else:
        # Show demo achievement data
        demo_achieve = pd.DataFrame({
            "Week": ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7", "Week 8"],
            "Target (MT)": [50, 55, 60, 55, 65, 70, 60, 65],
            "Achieved (MT)": [45, 52, 58, 50, 55, 68, 62, 60],
        })
        demo_achieve["Achievement %"] = (demo_achieve["Achieved (MT)"] / demo_achieve["Target (MT)"] * 100).round(1)
        demo_achieve["Cumulative Target"] = demo_achieve["Target (MT)"].cumsum()
        demo_achieve["Cumulative Achieved"] = demo_achieve["Achieved (MT)"].cumsum()
        demo_achieve["Cumulative %"] = (demo_achieve["Cumulative Achieved"] / demo_achieve["Cumulative Target"] * 100).round(1)

        st.markdown("**Weekly Achievement (Demo Data):**")
        st.dataframe(demo_achieve, use_container_width=True, hide_index=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Cumulative Target", f"{demo_achieve['Target (MT)'].sum():.0f} MT")
        with c2:
            st.metric("Cumulative Achieved", f"{demo_achieve['Achieved (MT)'].sum():.0f} MT")
        with c3:
            overall = (demo_achieve["Achieved (MT)"].sum() / demo_achieve["Target (MT)"].sum() * 100)
            st.metric("Overall Achievement", f"{overall:.1f}%")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: CHARTS & ANALYTICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_charts:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💰 Expense Category Breakdown")
        if not expenses_df.empty and "parent_type" in expenses_df.columns:
            exp_cats = expenses_df.groupby("parent_type")["amount"].sum().reset_index()
            fig_exp = px.pie(exp_cats, values="amount", names="parent_type", hole=0.4,
                             color_discrete_sequence=["#d4af37", "#10b981", "#ef4444", "#6366f1", "#f59e0b"])
            fig_exp.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font_color="#8c9097")
            st.plotly_chart(fig_exp, use_container_width=True)
        else:
            st.info("No expense data.")

    with col2:
        st.markdown("### 👷 Manpower Distribution")
        if not manpower_df.empty and "man_power_type" in manpower_df.columns:
            mp_types = manpower_df.groupby("man_power_type")["man_count"].sum().reset_index()
            fig_mp = px.bar(mp_types, x="man_power_type", y="man_count",
                            color_discrete_sequence=["#d4af37"])
            fig_mp.update_layout(
                height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#8c9097", xaxis_title="", yaxis_title="Count",
            )
            st.plotly_chart(fig_mp, use_container_width=True)
        else:
            st.info("No manpower data.")

    # Cost Trend
    st.divider()
    st.markdown("### 📊 Daily Cost Trend")
    if not expenses_df.empty:
        exp_c = expenses_df.copy()
        exp_c["reporting_date"] = pd.to_datetime(exp_c["reporting_date"], errors="coerce")
        exp_c = exp_c.dropna(subset=["reporting_date"])
        daily_c = exp_c.groupby("reporting_date")["amount"].sum().reset_index().sort_values("reporting_date")
        daily_c["cumulative"] = daily_c["amount"].cumsum()

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(x=daily_c["reporting_date"], y=daily_c["amount"],
            name="Daily", marker_color="rgba(212,175,55,0.5)"))
        fig_trend.add_trace(go.Scatter(x=daily_c["reporting_date"], y=daily_c["cumulative"],
            name="Cumulative", line=dict(color="#d4af37", width=2), yaxis="y2"))

        fig_trend.update_layout(
            height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#8c9097",
            yaxis=dict(title="Daily (₹)", gridcolor="rgba(255,255,255,0.05)"),
            yaxis2=dict(title="Cumulative (₹)", overlaying="y", side="right"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            legend=dict(orientation="h", y=-0.15),
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No expense data for trend.")

    # Machinery usage
    if not machinery_df.empty:
        st.divider()
        st.markdown("### 🚜 Machinery Usage")
        mach = machinery_df.groupby("parent_type").size().reset_index(name="Records")
        fig_mach = px.bar(mach, x="Records", y="parent_type", orientation="h",
                          color_discrete_sequence=["#6366f1"])
        fig_mach.update_layout(
            height=250, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#8c9097", xaxis_title="Records", yaxis_title="",
        )
        st.plotly_chart(fig_mach, use_container_width=True)
