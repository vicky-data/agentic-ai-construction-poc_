"""
👤 Admin — User, project, and labour category management
Access: Admin only
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import (
    require_role, get_current_user, init_session, add_notification,
    DEMO_USERS, ROLE_HIERARCHY,
)
from queries import get_all_projects

st.set_page_config(page_title="Admin Panel", page_icon="👤", layout="wide")

init_session()
require_role("Admin")
user = get_current_user()

st.markdown("""
<div style="text-align:center; padding:10px 0 20px 0;">
    <h1 style="color:#f8f9fa; font-weight:300;">👤 Admin Panel</h1>
    <p style="color:#8c9097; letter-spacing:1.5px; text-transform:uppercase;">
        User Management • Project Setup • Labour Categories
    </p>
</div>
""", unsafe_allow_html=True)

tab_users, tab_projects, tab_labour, tab_data, tab_archive = st.tabs([
    "👤 User Management", "🏗️ Project Management", "⛏️ Labour Categories",
    "📝 Data Modification", "📦 Archival"
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: USER MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_users:
    st.markdown("### 👤 Registered Users")

    # Show current users
    users_table = []
    for uid, u in DEMO_USERS.items():
        users_table.append({
            "User ID": uid,
            "Full Name": u["full_name"],
            "Role": u["role"],
            "Email": u["email"],
            "Projects": ", ".join(str(p) for p in u["projects"]),
        })

    # Add session-created users
    for u in st.session_state.get("custom_users", []):
        users_table.append(u)

    st.dataframe(pd.DataFrame(users_table), use_container_width=True, hide_index=True)

    # Add new user
    st.divider()
    st.markdown("### ➕ Add New User")
    col1, col2 = st.columns(2)
    with col1:
        new_uid = st.text_input("User ID", placeholder="e.g. pe4")
        new_name = st.text_input("Full Name", placeholder="e.g. Venkat Reddy")
        new_email = st.text_input("Email", placeholder="e.g. venkat@nikithabuildtech.com")
    with col2:
        new_role = st.selectbox("Designation (Role)", ROLE_HIERARCHY,
                                help="Hierarchy: Director → Project Manager → Project Engineer")
        new_password = st.text_input("Password", type="password", value="user123")
        projects_df = get_all_projects()
        proj_ids = projects_df["id"].tolist() if not projects_df.empty else [1, 2, 3]
        new_projects = st.multiselect("Assign Projects", proj_ids)

    if st.button("➕ Create User", use_container_width=True, type="primary"):
        if new_uid and new_name:
            new_user = {
                "User ID": new_uid,
                "Full Name": new_name,
                "Role": new_role,
                "Email": new_email,
                "Projects": ", ".join(str(p) for p in new_projects),
            }
            st.session_state.setdefault("custom_users", []).append(new_user)
            add_notification(f"New user created: {new_name} ({new_role})", "INFO", ["Director"])
            st.success(f"✅ User '{new_uid}' created successfully!")
            st.rerun()
        else:
            st.warning("Please fill in User ID and Full Name.")

    # Delete user
    st.divider()
    st.markdown("### 🗑️ Remove User")
    custom_users = st.session_state.get("custom_users", [])
    if custom_users:
        del_uid = st.selectbox("Select user to remove", [u["User ID"] for u in custom_users])
        if st.button("🗑️ Delete", use_container_width=True):
            st.session_state["custom_users"] = [u for u in custom_users if u["User ID"] != del_uid]
            st.success(f"User '{del_uid}' removed.")
            st.rerun()
    else:
        st.caption("No custom users to remove. Default demo users cannot be deleted.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: PROJECT MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_projects:
    st.markdown("### 🏗️ All Projects")

    projects_df = get_all_projects()
    if not projects_df.empty:
        display = projects_df.copy()
        # Map status labels
        if "status" in display.columns:
            display["status"] = display["status"].apply(
                lambda x: "Yet to Start" if x and "not" in str(x).lower() else x
            )
        st.dataframe(display, use_container_width=True, hide_index=True)

    # Add project
    st.divider()
    st.markdown("### ➕ Create New Project")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        p_name = st.text_input("Project Name", placeholder="e.g. T-Hub Phase 2")
        p_code = st.text_input("Project Code", placeholder="e.g. THUB-P2")
        p_status = st.selectbox("Status", ["Active", "Yet to Start", "On Hold", "Completed"])
    with col_p2:
        p_budget = st.number_input("Budget (₹)", min_value=0.0, value=10000000.0, step=100000.0)
        p_start = st.date_input("Planned Start Date")
        p_end = st.date_input("Planned End Date")

    if st.button("➕ Create Project", use_container_width=True, type="primary"):
        if p_name:
            add_notification(f"New project created: {p_name} (Budget: ₹{p_budget:,.0f})", "INFO", ["Director"])
            st.success(f"✅ Project '{p_name}' created!")
        else:
            st.warning("Please enter project name.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: LABOUR CATEGORIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_labour:
    st.markdown("### ⛏️ Labour Category Setup per Project")

    # Default categories
    default_categories = {
        "Skilled Workers": ["Mason", "Carpenter", "Plumber", "Electrician", "Welder", "Painter"],
        "Unskilled Workers": ["Helper", "Cleaner", "Loader"],
        "Supervisory": ["Site Supervisor", "Safety Officer", "Quality Inspector"],
    }

    projects_df = get_all_projects()
    sel_proj = st.selectbox("Select Project", options=[
        p.get("project_name", f"#{p['id']}") for _, p in projects_df.iterrows()
    ], key="labour_proj")

    for group, categories in default_categories.items():
        with st.expander(f"📂 {group}", expanded=True):
            for cat in categories:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"• {cat}")
                with col2:
                    st.checkbox("Active", value=True, key=f"lc_{group}_{cat}")

    # Add custom category
    st.markdown("### ➕ Add Custom Category")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        new_group = st.selectbox("Group", list(default_categories.keys()) + ["Other"])
    with col_c2:
        new_cat = st.text_input("Category Name", placeholder="e.g. Crane Operator")
    if st.button("➕ Add Category"):
        if new_cat:
            st.success(f"✅ Category '{new_cat}' added to {new_group}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: DATA MODIFICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_data:
    st.markdown("### 📝 Data Modification (Requires Director Approval)")
    st.warning("⚠️ All modifications require Director approval before being applied.")

    submitted_reports = st.session_state.get("submitted_reports", [])
    if submitted_reports:
        for i, report in enumerate(submitted_reports):
            with st.expander(f"📝 Report #{report.get('id', i)} — {report.get('date', '')} ({report.get('status', '')})", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    new_manpower = st.number_input("Manpower", value=report.get("manpower", 0), key=f"edit_mp_{i}")
                    new_expenses = st.number_input("Expenses (₹)", value=report.get("expenses", 0.0), key=f"edit_exp_{i}")
                with col2:
                    new_remark = st.text_input("Remark", value=report.get("remark", ""), key=f"edit_rem_{i}")
                    reason = st.text_input("Reason for modification", key=f"edit_reason_{i}")

                if st.button(f"📤 Submit Modification (Needs Director Approval)", key=f"edit_submit_{i}"):
                    add_notification(
                        f"Data modification requested for Report #{report.get('id', i)}: {reason}",
                        "WARNING", ["Director"]
                    )
                    st.info("📤 Modification request sent to Director for approval.")
    else:
        st.caption("No submitted reports to modify.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: ARCHIVAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_archive:
    st.markdown("### 📦 Data Archival")
    st.caption("Data older than 3 years can be archived for offline storage.")

    cutoff = datetime.now().year - 3
    st.info(f"All data before **January {cutoff}** is eligible for archival.")

    if st.button("📦 Archive Old Data (Simulation)", use_container_width=True):
        add_notification(f"Data archival completed for records before {cutoff}.", "INFO", ["Director"])
        st.success(f"✅ Simulated: All data before {cutoff} has been archived. (In production, this would move records to cold storage.)")

    st.divider()
    st.markdown("### 🔄 Restore Archived Data")
    st.caption("Select date range to restore archived records.")
    col1, col2 = st.columns(2)
    with col1:
        restore_year = st.number_input("Year", min_value=2020, max_value=cutoff, value=cutoff)
    with col2:
        if st.button("🔄 Restore", use_container_width=True):
            st.success(f"✅ Simulated: Data for year {restore_year} restored successfully.")
