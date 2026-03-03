"""
🏗️ Agentic AI Construction POC — Streamlit Dashboard
Connects to the live Nikitha Build Tech PostgreSQL database.
All data is real. All queries are read-only.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import test_connection, is_demo_mode
from queries import (
    get_all_projects,
    get_project_by_id,
    get_project_expenses,
    get_total_expenses_by_project,
    get_project_manpower,
    get_project_materials,
    get_project_machinery,
    get_project_boq_scope,
    get_daily_report_approvals,
    get_mrs_status,
    get_project_users,
)
from agents.progress_agent import analyze_progress
from agents.risk_agent import assess_risk
from agents.decision_agent import generate_recommendations
from ml.delay_model import build_delay_features, predict_delay
from ml.risk_model import classify_risk
from rag.retriever import ProjectRAG, get_quick_questions
from services.alert_store import add_alert, get_alerts, clear_alerts, get_severity_badge
from services.notification_service import (
    send_email_alert, generate_whatsapp_link,
    format_alert_email, format_whatsapp_message,
)
from services.report_service import generate_pdf_report

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.set_page_config(
    page_title="Agentic AI — Construction POC",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CUSTOM CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f4e 50%, #0d1230 100%);
    }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, rgba(30, 136, 229, 0.15), rgba(30, 136, 229, 0.05));
        border: 1px solid rgba(30, 136, 229, 0.3);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(30, 136, 229, 0.2);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #64B5F6;
        margin: 0;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #90A4AE;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 5px;
    }

    /* Risk Badge */
    .risk-badge {
        display: inline-block;
        padding: 8px 24px;
        border-radius: 25px;
        font-weight: 700;
        font-size: 1.1rem;
        letter-spacing: 1px;
    }
    .risk-low { background: rgba(0, 230, 118, 0.2); color: #00E676; border: 1px solid #00E676; }
    .risk-medium { background: rgba(255, 214, 0, 0.2); color: #FFD600; border: 1px solid #FFD600; }
    .risk-high { background: rgba(255, 109, 0, 0.2); color: #FF6D00; border: 1px solid #FF6D00; }
    .risk-critical { background: rgba(255, 23, 68, 0.2); color: #FF1744; border: 1px solid #FF1744; }

    /* Section headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #E3F2FD;
        margin-bottom: 10px;
        padding-bottom: 5px;
        border-bottom: 2px solid rgba(30, 136, 229, 0.3);
    }

    /* Alert rows */
    .alert-row {
        background: rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 4px;
        font-size: 0.85rem;
        border-left: 3px solid #1E88E5;
    }

    /* Recommendation cards */
    .rec-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #FF6D00;
    }

    /* Chat */
    .chat-answer {
        background: rgba(30, 136, 229, 0.1);
        border-radius: 12px;
        padding: 15px;
        border: 1px solid rgba(30, 136, 229, 0.2);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown("## 🏗️ Agentic AI POC")
    st.caption("Nikitha Build Tech Pvt Ltd")
    st.divider()

    # DB Status
    _demo = is_demo_mode()
    if _demo:
        st.info("🎯 **Demo Mode** — Using sample data")
    else:
        db_ok = test_connection()
        if db_ok:
            st.success("🟢 Database Connected")
        else:
            st.warning("⚠️ DB offline — switching to Demo Mode")
            _demo = True

    # Project Selector
    projects_df = get_all_projects()
    if projects_df.empty:
        st.warning("No projects found in database.")
        st.stop()

    project_options = {}
    for _, row in projects_df.iterrows():
        name = row.get("project_name") or f"Project #{row['id']}"
        code = row.get("project_code") or "N/A"
        label = f"{name} ({code})"
        project_options[label] = row["id"]

    if not project_options:
        st.warning("No valid projects found.")
        st.stop()

    selected_label = st.selectbox(
        "📌 Select Project",
        options=list(project_options.keys()),
        index=0,
    )
    selected_project_id = project_options[selected_label]

    st.divider()

    # Notification Config
    st.markdown("### 📨 Notifications")
    notify_email = st.text_input("Recipient Email", value="", placeholder="name@example.com")
    notify_phone = st.text_input("WhatsApp Phone", value="", placeholder="919876543210")

    st.divider()

    # Approval Mode
    approval_mode = st.radio("⚙️ Approval Mode", ["AUTO", "MANUAL"], index=1)
    if st.button("🗑️ Clear Alerts"):
        clear_alerts()
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOAD ALL PROJECT DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

project_df = get_project_by_id(selected_project_id)
if project_df.empty:
    st.error("Could not load project details.")
    st.stop()

project = project_df.iloc[0]
expenses_df = get_project_expenses(selected_project_id)
manpower_df = get_project_manpower(selected_project_id)
materials_df = get_project_materials(selected_project_id)
machinery_df = get_project_machinery(selected_project_id)
boq_df = get_project_boq_scope(selected_project_id)
approvals_df = get_daily_report_approvals(selected_project_id)
mrs_df = get_mrs_status(selected_project_id)
users_df = get_project_users(selected_project_id)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RUN AI AGENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

progress = analyze_progress(project, expenses_df)
risk = assess_risk(project, expenses_df, manpower_df, approvals_df, materials_df)
recommendations = generate_recommendations(progress, risk)

# Delay prediction
delay_features = build_delay_features(project, expenses_df, manpower_df)
delay_prediction = predict_delay(delay_features) if delay_features else None

# Risk classification
risk_classification = classify_risk(
    cost_overrun_pct=progress.get("cost_overrun_pct", 0),
    days_remaining=progress.get("days_remaining"),
    manpower_drop_pct=0,  # Will be computed if manpower data exists
    report_gap_days=0,
    material_overuse_count=0,
    total_budget=progress.get("total_budget", 0),
    total_spent=progress.get("total_spent", 0),
)

# Auto-alert in AUTO mode
if approval_mode == "AUTO" and risk["risk_level"] in ("HIGH", "CRITICAL"):
    add_alert(
        "AUTO",
        f"Risk level: {risk['risk_level']}. {risk['factors'][0] if risk['factors'] else ''}",
        risk["risk_level"],
        project.get("project_name", ""),
    )

# Build RAG
rag = ProjectRAG()
rag.build_corpus(
    project=project,
    expenses_df=expenses_df,
    manpower_df=manpower_df,
    materials_df=materials_df,
    machinery_df=machinery_df,
    approvals_df=approvals_df,
    boq_df=boq_df,
    users_df=users_df,
    progress=progress,
    risk=risk,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown(f"""
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <h1 style="color: #E3F2FD; margin-bottom: 5px;">
            🏗️ {project.get('project_name', 'Project')}
        </h1>
        <p style="color: #90A4AE; font-size: 1rem;">
            📍 {project.get('location', 'N/A')} &nbsp;|&nbsp;
            📋 {project.get('project_code', 'N/A')} &nbsp;|&nbsp;
            📊 Status: <b>{project.get('status', 'N/A')}</b>
        </p>
    </div>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KPI CARDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-value">₹{progress['total_budget']:,.0f}</p>
            <p class="kpi-label">Total Budget</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-value">₹{progress['total_spent']:,.0f}</p>
            <p class="kpi-label">Total Spent</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    days_rem = progress['days_remaining']
    days_display = f"{days_rem}" if days_rem is not None else "N/A"
    color = "#FF1744" if days_rem is not None and days_rem < 0 else "#64B5F6"
    st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-value" style="color:{color}">{days_display}</p>
            <p class="kpi-label">Days Remaining</p>
        </div>
    """, unsafe_allow_html=True)

with col4:
    mp_total = int(manpower_df["man_count"].sum()) if not manpower_df.empty else 0
    st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-value">{mp_total}</p>
            <p class="kpi-label">Total Manpower Logs</p>
        </div>
    """, unsafe_allow_html=True)

with col5:
    mat_total = len(materials_df) if not materials_df.empty else 0
    st.markdown(f"""
        <div class="kpi-card">
            <p class="kpi-value">{mat_total}</p>
            <p class="kpi-label">Material Records</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI RISK MONITOR + DECISION AGENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

risk_col, rec_col = st.columns([1, 1])

with risk_col:
    st.markdown('<p class="section-header">⚠️ AI Risk Monitor</p>', unsafe_allow_html=True)

    risk_level = risk["risk_level"]
    risk_css = f"risk-{risk_level.lower()}"
    st.markdown(f"""
        <div style="text-align: center; margin: 10px 0;">
            <span class="risk-badge {risk_css}">{risk_classification['emoji']} {risk_level}</span>
        </div>
    """, unsafe_allow_html=True)

    # Risk score gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk["risk_score"],
        title={"text": "Risk Score", "font": {"color": "#90A4AE", "size": 14}},
        gauge={
            "axis": {"range": [0, 10], "tickcolor": "#555"},
            "bar": {"color": risk_classification["color"]},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [
                {"range": [0, 3], "color": "rgba(0,230,118,0.1)"},
                {"range": [3, 5.5], "color": "rgba(255,214,0,0.1)"},
                {"range": [5.5, 7.5], "color": "rgba(255,109,0,0.1)"},
                {"range": [7.5, 10], "color": "rgba(255,23,68,0.1)"},
            ],
        },
        number={"font": {"color": "#E3F2FD"}},
    ))
    fig_gauge.update_layout(
        height=200,
        margin=dict(l=30, r=30, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Risk factors
    for factor in risk["factors"]:
        st.markdown(f"<div class='alert-row'>{factor}</div>", unsafe_allow_html=True)

    # Delay prediction
    if delay_prediction:
        st.markdown(f"""
            <div style="margin-top:10px; padding:10px; background:rgba(255,255,255,0.04); border-radius:10px;">
                <b>🔮 Delay Prediction:</b> {delay_prediction['predicted_delay_days']} days
                (Probability: {delay_prediction['delay_probability']}%)
            </div>
        """, unsafe_allow_html=True)


with rec_col:
    st.markdown('<p class="section-header">🤖 Decision Agent — Recommendations</p>', unsafe_allow_html=True)

    for rec in recommendations:
        st.markdown(f"""
            <div class="rec-card" style="border-left-color:
                {'#FF1744' if 'CRITICAL' in rec['priority'] else
                 '#FF6D00' if 'HIGH' in rec['priority'] else
                 '#FFD600' if 'MEDIUM' in rec['priority'] else '#00E676'};">
                <b>{rec['priority']}</b> — <i>{rec['category']}</i><br>
                {rec['action']}<br>
                <span style="color: #78909C; font-size: 0.8rem;">{rec['reason']}</span>
            </div>
        """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHARTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.divider()
chart_col1, chart_col2 = st.columns(2)

# ── Cost Trend Chart ──
with chart_col1:
    st.markdown('<p class="section-header">💰 Cost Trend</p>', unsafe_allow_html=True)

    if not expenses_df.empty:
        try:
            exp_chart = expenses_df.copy()
            exp_chart["reporting_date"] = pd.to_datetime(exp_chart["reporting_date"], errors="coerce")
            exp_chart = exp_chart.dropna(subset=["reporting_date"])

            if not exp_chart.empty:
                daily_cost = exp_chart.groupby("reporting_date")["amount"].sum().reset_index()
                daily_cost = daily_cost.sort_values("reporting_date")
                daily_cost["cumulative"] = daily_cost["amount"].cumsum()

                fig_cost = go.Figure()
                fig_cost.add_trace(go.Scatter(
                    x=daily_cost["reporting_date"],
                    y=daily_cost["cumulative"],
                    mode="lines",
                    name="Cumulative Cost",
                    fill="tozeroy",
                    line=dict(color="#1E88E5", width=2),
                    fillcolor="rgba(30,136,229,0.1)",
                ))

                # Budget line
                if progress["total_budget"] > 0:
                    fig_cost.add_hline(
                        y=progress["total_budget"],
                        line_dash="dash",
                        line_color="#FF6D00",
                        annotation_text=f"Budget: ₹{progress['total_budget']:,.0f}",
                        annotation_font_color="#FF6D00",
                    )

                fig_cost.update_layout(
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#90A4AE",
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Amount (₹)"),
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=False,
                )
                st.plotly_chart(fig_cost, use_container_width=True)
            else:
                st.info("No valid expense dates to chart.")
        except Exception as e:
            st.warning(f"Could not render cost chart: {e}")
    else:
        st.info("No expense data available for this project.")


# ── Manpower Chart ──
with chart_col2:
    st.markdown('<p class="section-header">👷 Manpower Trend</p>', unsafe_allow_html=True)

    if not manpower_df.empty:
        try:
            mp_chart = manpower_df.copy()
            mp_chart["reported_date"] = pd.to_datetime(mp_chart["reported_date"], errors="coerce")
            mp_chart = mp_chart.dropna(subset=["reported_date"])

            if not mp_chart.empty:
                mp_grouped = mp_chart.groupby(
                    [mp_chart["reported_date"].dt.date, "man_power_type"]
                )["man_count"].sum().reset_index()
                mp_grouped.columns = ["Date", "Type", "Count"]

                fig_mp = px.bar(
                    mp_grouped,
                    x="Date",
                    y="Count",
                    color="Type",
                    barmode="stack",
                    color_discrete_sequence=["#1E88E5", "#00E676", "#FF6D00", "#AB47BC", "#FF1744"],
                )
                fig_mp.update_layout(
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#90A4AE",
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Workers"),
                    margin=dict(l=20, r=20, t=20, b=20),
                    legend=dict(orientation="h", y=-0.15),
                )
                st.plotly_chart(fig_mp, use_container_width=True)
            else:
                st.info("No valid manpower dates to chart.")
        except Exception as e:
            st.warning(f"Could not render manpower chart: {e}")
    else:
        st.info("No manpower data available for this project.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPENSE BREAKDOWN + MACHINERY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.divider()
breakdown_col1, breakdown_col2 = st.columns(2)

with breakdown_col1:
    st.markdown('<p class="section-header">📊 Expense Breakdown by Category</p>', unsafe_allow_html=True)
    if not expenses_df.empty and "parent_type" in expenses_df.columns:
        exp_by_type = expenses_df.groupby("parent_type")["amount"].sum().reset_index()
        exp_by_type.columns = ["Category", "Amount"]
        exp_by_type = exp_by_type.sort_values("Amount", ascending=False)

        fig_pie = px.pie(
            exp_by_type,
            values="Amount",
            names="Category",
            color_discrete_sequence=["#1E88E5", "#00E676", "#FF6D00", "#AB47BC", "#FF1744", "#FFD600"],
            hole=0.4,
        )
        fig_pie.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#90A4AE",
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expense category data available.")

with breakdown_col2:
    st.markdown('<p class="section-header">🚜 Machinery Usage</p>', unsafe_allow_html=True)
    if not machinery_df.empty:
        mach_summary = machinery_df.groupby("parent_type").size().reset_index(name="Count")
        mach_summary = mach_summary.sort_values("Count", ascending=True)

        fig_mach = px.bar(
            mach_summary,
            x="Count",
            y="parent_type",
            orientation="h",
            color_discrete_sequence=["#AB47BC"],
        )
        fig_mach.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#90A4AE",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Records"),
            yaxis=dict(title=""),
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
        )
        st.plotly_chart(fig_mach, use_container_width=True)
    else:
        st.info("No machinery data available.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI CHAT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.divider()
st.markdown('<p class="section-header">💬 AI Chat — Ask About This Project</p>', unsafe_allow_html=True)

# Quick question buttons
quick_qs = get_quick_questions()
q_cols = st.columns(4)
selected_quick = None
for i, q in enumerate(quick_qs):
    with q_cols[i % 4]:
        if st.button(q, key=f"qq_{i}", use_container_width=True):
            selected_quick = q

# Text input
user_question = st.text_input(
    "Type your question:",
    value=selected_quick or "",
    placeholder="e.g., What is the total expense for this project?",
    key="user_q",
)

if user_question:
    answer = rag.answer_question(user_question)
    st.markdown(f'<div class="chat-answer">{answer}</div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NOTIFICATIONS + PDF
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.divider()
notif_col1, notif_col2, notif_col3 = st.columns(3)

with notif_col1:
    st.markdown('<p class="section-header">📧 Email Alert</p>', unsafe_allow_html=True)
    if st.button("📧 Send Email Alert", use_container_width=True):
        if notify_email:
            subject = f"🏗️ Project Alert — {project.get('project_name', 'Project')}"
            body = format_alert_email(
                project.get("project_name", ""), risk["risk_level"], progress, recommendations,
            )
            ok, msg = send_email_alert(notify_email, subject, body)
            if ok:
                st.success(msg)
                add_alert("EMAIL", f"Sent to {notify_email}", "INFO", project.get("project_name", ""))
            else:
                st.error(msg)
        else:
            st.warning("Enter recipient email in sidebar.")

with notif_col2:
    st.markdown('<p class="section-header">📲 WhatsApp Alert</p>', unsafe_allow_html=True)
    if st.button("📲 Send WhatsApp", use_container_width=True):
        if notify_phone:
            wa_msg = format_whatsapp_message(
                project.get("project_name", ""), risk["risk_level"], progress,
            )
            wa_link = generate_whatsapp_link(notify_phone, wa_msg)
            st.markdown(f"[🔗 Click to send via WhatsApp]({wa_link})")
            add_alert("WHATSAPP", f"Link generated for {notify_phone}", "INFO",
                       project.get("project_name", ""))
        else:
            st.warning("Enter phone number in sidebar.")

with notif_col3:
    st.markdown('<p class="section-header">📄 PDF Report</p>', unsafe_allow_html=True)

    # Build summary strings
    exp_summary = ""
    if not expenses_df.empty:
        exp_by_cat = expenses_df.groupby("parent_type")["amount"].sum()
        exp_summary = ", ".join([f"{k}: ₹{v:,.0f}" for k, v in exp_by_cat.items()])

    mp_summary = ""
    if not manpower_df.empty:
        mp_by_type = manpower_df.groupby("man_power_type")["man_count"].sum()
        mp_summary = ", ".join([f"{k}: {v}" for k, v in mp_by_type.items()])

    pdf_bytes = generate_pdf_report(
        project_name=project.get("project_name", "Project"),
        progress=progress,
        risk=risk,
        recommendations=recommendations,
        expenses_summary=exp_summary,
        manpower_summary=mp_summary,
    )
    st.download_button(
        label="⬇️ Download PDF Report",
        data=pdf_bytes,
        file_name=f"project_report_{selected_project_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALERT LOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.divider()
st.markdown('<p class="section-header">📜 Alert History</p>', unsafe_allow_html=True)

alerts = get_alerts()
if alerts:
    for alert in alerts[:20]:
        badge = get_severity_badge(alert["severity"])
        st.markdown(f"""
            <div class="alert-row">
                {badge} <b>[{alert['type']}]</b> {alert['message']}
                <span style="float:right; color:#78909C; font-size:0.75rem;">
                    {alert['timestamp']}
                </span>
            </div>
        """, unsafe_allow_html=True)
else:
    st.caption("No alerts yet. Alerts will appear here when triggered by the AI agents.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA EXPLORER (Expandable)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.divider()
with st.expander("🔍 Raw Data Explorer", expanded=False):
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Expenses", "Manpower", "Materials", "Machinery", "BOQ Scope", "Team"
    ])

    with tab1:
        st.dataframe(expenses_df, use_container_width=True, height=300)
    with tab2:
        st.dataframe(manpower_df, use_container_width=True, height=300)
    with tab3:
        st.dataframe(materials_df, use_container_width=True, height=300)
    with tab4:
        st.dataframe(machinery_df, use_container_width=True, height=300)
    with tab5:
        st.dataframe(boq_df, use_container_width=True, height=300)
    with tab6:
        st.dataframe(users_df, use_container_width=True, height=300)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
    <div style="text-align:center; padding:20px 0; color:#546E7A; font-size:0.8rem;">
        🏗️ Agentic AI Construction POC — Nikitha Build Tech Pvt Ltd<br>
        Powered by real-time PostgreSQL data | Built with Streamlit
    </div>
""", unsafe_allow_html=True)
