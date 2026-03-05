"""
📊 PM Dashboard — Multi-project management and report approvals
Access: Project Manager, Admin
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import require_role, get_current_user, init_session, add_notification
from queries import (
    get_all_projects, get_project_expenses, get_project_manpower,
    get_project_materials, get_daily_report_approvals, get_project_users,
)
from agents.progress_agent import analyze_progress
from agents.risk_agent import assess_risk
from agents.decision_agent import generate_recommendations
from services.report_service import generate_pdf_report

st.set_page_config(page_title="PM Dashboard", page_icon="📊", layout="wide")

init_session()
require_role("Project Manager", "Admin")
user = get_current_user()

st.markdown("""
<div style="text-align:center; padding:10px 0 20px 0;">
    <h1 style="color:#1e293b; font-weight:300;">📊 Project Manager Dashboard</h1>
    <p style="color:#64748b; letter-spacing:1.5px; text-transform:uppercase;">
        Multi-Project View & Approvals
    </p>
</div>
""", unsafe_allow_html=True)

# Load projects assigned to this PM
projects_df = get_all_projects()
if projects_df.empty:
    st.warning("No projects found.")
    st.stop()

# Filter to PM's assigned projects
id_col = "id" if "id" in projects_df.columns else projects_df.columns[0] if not projects_df.empty else "id"
if id_col in projects_df.columns:
    my_projects = [p for p in user.get("projects", []) if p in projects_df[id_col].values]
    pm_projects = projects_df[projects_df[id_col].isin(my_projects)]
else:
    my_projects = user.get("projects", [])
    pm_projects = projects_df

if pm_projects.empty:
    pm_projects = projects_df  # Admin sees all

# ── Tab layout ──
tab_overview, tab_approvals, tab_absent = st.tabs(["📋 My Projects", "✅ Approvals", "📝 Absent PE Reports"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: MY PROJECTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_overview:
    for _, proj in pm_projects.iterrows():
        pid = proj["id"]
        expenses = get_project_expenses(pid)
        manpower = get_project_manpower(pid)
        materials = get_project_materials(pid)
        approvals = get_daily_report_approvals(pid)

        progress = analyze_progress(proj, expenses)
        risk = assess_risk(proj, expenses, manpower, approvals, materials)
        recs = generate_recommendations(progress, risk)

        health_colors = {
            "ON_TRACK": "#10b981", "WARNING": "#f59e0b",
            "AT_RISK": "#ef4444", "CRITICAL": "#dc2626", "OVERDUE": "#991b1b",
        }
        h_color = health_colors.get(progress["health"], "#6b7280")

        with st.expander(f"🏗️ {proj.get('project_name', f'Project #{pid}')} — {progress['health']}", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Budget", f"₹{progress['total_budget']/1e7:.1f}Cr")
            with c2:
                st.metric("Spent", f"₹{progress['total_spent']/1e7:.1f}Cr")
            with c3:
                st.metric("Time Progress", f"{progress['time_progress_pct']:.0f}%")
            with c4:
                days = progress['days_remaining']
                st.metric("Days Left", str(days) if days is not None else "N/A")

            # Risk & Recommendations
            st.markdown(f"**Risk Level:** <span style='color:{h_color}'>{risk['risk_level']}</span> (Score: {risk['risk_score']}/10)", unsafe_allow_html=True)

            if recs:
                st.markdown("**Top Recommendations:**")
                for rec in recs[:3]:
                    st.markdown(f"- {rec['priority']} **{rec['category']}**: {rec['action']}")

            # PDF Export per project
            pdf_data = generate_pdf_report(
                proj.get("project_name", "Project"), progress, risk, recs,
            )
            st.download_button(
                f"📄 Download Report", data=pdf_data,
                file_name=f"report_{pid}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf", key=f"pdf_{pid}",
            )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: APPROVALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_approvals:
    st.markdown('<p style="font-size:1.1rem; color:#475569;">Pending PE Daily Reports for Approval</p>', unsafe_allow_html=True)

    # Get submitted reports from session state
    submitted = st.session_state.get("submitted_reports", [])
    pending = [r for r in submitted if r.get("status") == "PENDING"
               and r.get("project_id") in my_projects]

    if not pending:
        # Show demo pending reports
        pending = [
            {"id": 1, "project_id": 1, "project_name": "Gachibowli Sky Tower", "submitted_by": "Rajesh Kumar",
             "date": datetime.now().strftime("%Y-%m-%d"), "timing": "MORNING", "status": "PENDING",
             "manpower": 45, "expenses": 125000, "remark": "Foundation work in progress"},
            {"id": 2, "project_id": 2, "project_name": "Jubilee Hills Villa", "submitted_by": "Srinivas Reddy",
             "date": datetime.now().strftime("%Y-%m-%d"), "timing": "MORNING", "status": "PENDING",
             "manpower": 18, "expenses": 78000, "remark": "Plumbing installation ongoing"},
        ]

    for i, report in enumerate(pending):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"""
                **{report.get('project_name', 'Project')}** — {report.get('timing', '')} Report  
                📅 {report.get('date', '')} | 👤 {report.get('submitted_by', 'PE')}  
                👷 Manpower: {report.get('manpower', 'N/A')} | 💰 Expenses: ₹{report.get('expenses', 0):,}  
                📝 {report.get('remark', '')}
                """)
            with col2:
                if st.button("✅ Approve", key=f"approve_{i}", use_container_width=True):
                    report["status"] = "APPROVED"
                    report["approved_by"] = user["full_name"]
                    report["approval_time"] = datetime.now().isoformat()
                    add_notification(
                        f"Report approved: {report.get('project_name', '')} ({report.get('timing', '')})",
                        "INFO", ["Project Engineer"]
                    )
                    st.success("✅ Approved!")
                    st.rerun()
            with col3:
                if st.button("❌ Reject", key=f"reject_{i}", use_container_width=True):
                    report["status"] = "REJECTED"
                    report["rejected_by"] = user["full_name"]
                    add_notification(
                        f"Report rejected: {report.get('project_name', '')}. Please resubmit.",
                        "WARNING", ["Project Engineer"]
                    )
                    st.warning("❌ Rejected")
                    st.rerun()
            st.divider()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: SUBMIT FOR ABSENT PE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_absent:
    st.markdown('<p style="font-size:1.1rem; color:#475569;">Submit Daily Report on Behalf of Absent PE</p>', unsafe_allow_html=True)

    proj_options = []
    for _, p in pm_projects.iterrows():
        pname = p.get("project_name", "Project #" + str(p["id"]))
        proj_options.append(pname + " (#" + str(p["id"]) + ")")
    sel_project = st.selectbox("Select Project", options=proj_options)
    absent_pe = st.text_input("Absent PE Name", placeholder="e.g. Rajesh Kumar")
    timing = st.selectbox("Report Timing", ["MORNING", "AFTERNOON", "EVENING"])

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        manpower_count = st.number_input("Total Manpower on Site", min_value=0, value=20)
        machinery_count = st.number_input("Machinery Units", min_value=0, value=3)
    with col_f2:
        total_expenses = st.number_input("Total Expenses (₹)", min_value=0.0, value=50000.0, step=1000.0)
        materials_used = st.text_input("Key Materials Used", placeholder="Cement: 50 bags, Steel: 2T")

    remark = st.text_area("Remarks", placeholder="Brief description of today's work...")

    if st.button("📤 Submit Report (as PM)", use_container_width=True, type="primary"):
        if absent_pe:
            report = {
                "id": len(st.session_state.get("submitted_reports", [])) + 100,
                "project_id": my_projects[0] if my_projects else 1,
                "project_name": sel_project.split("(")[0].strip(),
                "submitted_by": f"{absent_pe} (via PM: {user['full_name']})",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timing": timing,
                "status": "APPROVED",
                "manpower": manpower_count,
                "machinery": machinery_count,
                "expenses": total_expenses,
                "materials": materials_used,
                "remark": remark,
                "approved_by": user["full_name"],
            }
            st.session_state.setdefault("submitted_reports", []).append(report)
            add_notification(
                f"PM submitted report for absent PE: {absent_pe} ({timing})",
                "INFO", ["Director"]
            )
            st.success(f"✅ Report submitted on behalf of {absent_pe}")
        else:
            st.warning("Please enter the absent PE's name.")
