"""
📝 Daily Reports — PE report submission with timing restrictions
Access: Project Engineer, Admin
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import (
    require_role, get_current_user, init_session, add_notification,
    can_submit_report, get_current_report_window, REPORT_WINDOWS,
)
from queries import get_all_projects

st.set_page_config(page_title="Daily Reports", page_icon="📝", layout="wide")

init_session()
require_role("Project Engineer", "Admin", "Project Manager")
user = get_current_user()

st.markdown("""
<div style="text-align:center; padding:10px 0 20px 0;">
    <h1 style="color:#1e293b; font-weight:300;">📝 Daily Report Submission</h1>
    <p style="color:#64748b; letter-spacing:1.5px; text-transform:uppercase;">
        Morning • Afternoon • Evening
    </p>
</div>
""", unsafe_allow_html=True)

# Show current window
current_window = get_current_report_window()
if current_window:
    st.info(f"🕐 Current Window: **{REPORT_WINDOWS[current_window]['label']}**")
else:
    st.warning("⏰ No report window is currently active (6 AM – 8 PM). You may still fill the form but may need PM approval to submit.")

# ── Tab Layout ──
tab_submit, tab_history = st.tabs(["📝 Submit Report", "📋 Report History"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: SUBMIT REPORT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_submit:
    projects_df = get_all_projects()

    # Defensive: find the ID column name
    id_col = "id" if "id" in projects_df.columns else projects_df.columns[0] if not projects_df.empty else "id"

    my_project_ids = user.get("projects", [])
    if id_col in projects_df.columns:
        my_projects = [p for p in my_project_ids if p in projects_df[id_col].values]
        my_proj_df = projects_df[projects_df[id_col].isin(my_projects)] if my_projects else projects_df
    else:
        my_proj_df = projects_df

    proj_options = []
    for _, p in my_proj_df.iterrows():
        pid = p.get(id_col, p.name) if id_col in p.index else p.name
        pname = p.get("project_name", "Project #" + str(pid))
        proj_options.append(pname + " (#" + str(pid) + ")")
    sel_proj = st.selectbox("🏗️ Select Project", options=proj_options)
    if not my_proj_df.empty and id_col in my_proj_df.columns:
        sel_proj_id = my_proj_df.iloc[0][id_col]
    else:
        sel_proj_id = 1

    col_dt, col_timing = st.columns(2)
    with col_dt:
        report_date = st.date_input("📅 Report Date", value=date.today())
    with col_timing:
        report_timing = st.selectbox("🕐 Report Timing", ["MORNING", "AFTERNOON", "EVENING"],
                                      index=["MORNING", "AFTERNOON", "EVENING"].index(current_window) if current_window else 0)

    # Check submission rules
    can_submit, reason = can_submit_report(user["role"], report_date, report_timing)
    if not can_submit:
        st.warning(f"⚠️ {reason}")

    st.divider()

    # ── MANPOWER Section ──
    st.markdown("### 👷 Manpower")
    mp_types = ["Skilled Workers", "Unskilled Workers", "Supervisors", "Helpers", "Safety Officers"]
    manpower_data = {}
    mp_cols = st.columns(len(mp_types))
    for i, mp_type in enumerate(mp_types):
        with mp_cols[i]:
            manpower_data[mp_type] = st.number_input(mp_type, min_value=0, value=0, key=f"mp_{i}")

    # ── MACHINERY Section ──
    st.markdown("### 🚜 Machinery")
    col_m1, col_m2, col_m3 = st.columns(3)
    machinery_entries = []
    with col_m1:
        mach_type = st.selectbox("Type", ["Excavator", "Crane", "Mixer", "Truck", "Compactor", "Loader", "Other"])
    with col_m2:
        mach_hours = st.number_input("Hours Used", min_value=0.0, value=0.0, step=0.5)
    with col_m3:
        mach_count = st.number_input("Count", min_value=0, value=1)

    # ── EXPENSES Section ──
    st.markdown("### 💰 Expenses")
    expense_categories = ["Labour", "Material", "Equipment", "Overhead", "Transport", "Other"]
    exp_cols = st.columns(3)
    expenses_data = {}
    for i, cat in enumerate(expense_categories):
        with exp_cols[i % 3]:
            expenses_data[cat] = st.number_input(f"{cat} (₹)", min_value=0.0, value=0.0, step=1000.0, key=f"exp_{i}")

    # ── MATERIALS Section ──
    st.markdown("### 📦 Materials Used")
    col_mat1, col_mat2, col_mat3 = st.columns(3)
    with col_mat1:
        mat_name = st.selectbox("Material", [
            "OPC Cement 53 Grade", "TMT Steel 12mm", "River Sand (Fine)",
            "M20 Ready Mix Concrete", "Red Bricks", "CPVC Pipes", "Other"
        ])
    with col_mat2:
        mat_qty = st.number_input("Quantity Used", min_value=0.0, value=0.0, step=1.0)
    with col_mat3:
        mat_unit = st.selectbox("Unit", ["Bags", "Tonnes", "Cu.M", "Nos", "Metres", "Litres"])

    # ── TARGET vs ACHIEVED Section ──
    st.markdown("### 🎯 Target vs Achieved (Metric Tonnes)")
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        target_mt = st.number_input("Target (MT)", min_value=0.0, value=0.0, step=0.5)
    with col_t2:
        achieved_mt = st.number_input("Achieved (MT)", min_value=0.0, value=0.0, step=0.5)
    with col_t3:
        if target_mt > 0:
            achievement_pct = round((achieved_mt / target_mt) * 100, 1)
            color = "#10b981" if achievement_pct >= 80 else "#f59e0b" if achievement_pct >= 50 else "#ef4444"
            st.markdown(f"""<div style="padding:20px; text-align:center;">
                <p style="font-size:2rem; font-weight:300; color:{color}; margin:0;">{achievement_pct}%</p>
                <p style="font-size:0.75rem; color:#64748b; text-transform:uppercase; letter-spacing:1.5px;">Achievement</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.caption("Enter target to see achievement %")

    # ── GPS & Remarks ──
    st.markdown("### 📍 Location & Remarks")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        gps_location = st.text_input("📍 GPS Location", placeholder="e.g. 17.4435° N, 78.3772° E")
    with col_g2:
        remark = st.text_area("📝 Remarks", placeholder="Brief summary of today's work progress...")

    # ── SUBMIT Button ──
    st.divider()
    if st.button("📤 Submit Daily Report", use_container_width=True, type="primary", disabled=(not can_submit)):
        total_manpower = sum(manpower_data.values())
        total_expenses = sum(expenses_data.values())

        report = {
            "id": len(st.session_state.get("submitted_reports", [])) + 1,
            "project_id": sel_proj_id,
            "project_name": sel_proj.split("(")[0].strip(),
            "submitted_by": user["full_name"],
            "date": report_date.isoformat(),
            "timing": report_timing,
            "status": "PENDING",
            "manpower": total_manpower,
            "manpower_detail": manpower_data,
            "machinery": {"type": mach_type, "hours": mach_hours, "count": mach_count},
            "expenses": total_expenses,
            "expenses_detail": expenses_data,
            "materials": {"name": mat_name, "quantity": mat_qty, "unit": mat_unit},
            "target_mt": target_mt,
            "achieved_mt": achieved_mt,
            "achievement_pct": round((achieved_mt / target_mt * 100), 1) if target_mt > 0 else 0,
            "gps": gps_location,
            "remark": remark,
            "submitted_at": datetime.now().isoformat(),
        }
        st.session_state.setdefault("submitted_reports", []).append(report)
        add_notification(
            f"New report submitted: {sel_proj.split('(')[0].strip()} ({report_timing}) by {user['full_name']}",
            "INFO", ["Project Manager"]
        )
        st.success(f"✅ {report_timing} report submitted successfully! Pending PM approval.")
        st.balloons()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: REPORT HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_history:
    st.markdown('<p style="font-size:1.1rem; color:#475569;">📋 Your Submitted Reports</p>', unsafe_allow_html=True)

    my_reports = [r for r in st.session_state.get("submitted_reports", [])
                  if r.get("submitted_by") == user["full_name"] or user["role"] in ("Admin", "Project Manager")]

    if my_reports:
        for report in reversed(my_reports):
            status_icon = "✅" if report["status"] == "APPROVED" else "⏳" if report["status"] == "PENDING" else "❌"
            locked = report["status"] == "APPROVED"

            with st.expander(
                f"{status_icon} {report.get('date', '')} — {report.get('timing', '')} | {report.get('project_name', '')} [{report['status']}]",
                expanded=False,
            ):
                if locked:
                    st.info("🔒 This report has been approved and cannot be edited.")

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Manpower", report.get("manpower", 0))
                with c2:
                    st.metric("Expenses", f"₹{report.get('expenses', 0):,.0f}")
                with c3:
                    st.metric("Target (MT)", report.get("target_mt", 0))
                with c4:
                    st.metric("Achievement", f"{report.get('achievement_pct', 0)}%")

                st.caption(f"📝 {report.get('remark', 'No remarks')}")
                if report.get("gps"):
                    st.caption(f"📍 {report['gps']}")
    else:
        st.caption("No reports submitted yet. Use the 'Submit Report' tab to create one.")
