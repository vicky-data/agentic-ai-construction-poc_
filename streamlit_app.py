"""
🏗️ Agentic AI Construction POC — Login & Home Page
Role-based access: Admin, Director, Project Manager, Project Engineer
"""

import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import (
    init_session, authenticate, is_authenticated, get_current_user,
    logout, check_idle_timeout, get_notifications_for_role, DEMO_USERS,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.set_page_config(
    page_title="Agentic AI — Construction POC",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session
init_session()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CUSTOM CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<style>
    .stApp {
        background: #0f1115;
    }
    .kpi-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px 20px;
        text-align: center;
        backdrop-filter: blur(12px);
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(212, 175, 55, 0.4);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 300;
        color: #f8f9fa;
        margin: 0;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 0.75rem;
        color: #8c9097;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 10px;
        font-weight: 500;
    }
    .risk-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 1.2px;
        margin-bottom: 15px;
    }
    .risk-low { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .risk-medium { background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
    .risk-high { background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    .risk-critical { background: rgba(153, 27, 27, 0.2); color: #fca5a5; border: 1px solid rgba(220, 38, 38, 0.5); }
    .section-header {
        font-size: 1.2rem;
        font-weight: 400;
        color: #e5e7eb;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        letter-spacing: 0.5px;
    }
    .alert-row {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 6px;
        font-size: 0.85rem;
        border-left: 2px solid #6b7280;
        color: #d1d5db;
    }
    .rec-card {
        background: rgba(255, 255, 255, 0.015);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-left: 3px solid rgba(212, 175, 55, 0.7);
    }
    .chat-answer {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        padding: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #e5e7eb;
        line-height: 1.6;
    }
    .login-box {
        max-width: 420px;
        margin: 60px auto;
        padding: 40px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        backdrop-filter: blur(12px);
    }
    .role-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        transition: all 0.3s;
    }
    .role-card:hover {
        border-color: rgba(212,175,55,0.5);
        transform: translateY(-2px);
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IDLE TIMEOUT CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if is_authenticated():
    if check_idle_timeout(minutes=10):
        st.warning("⏱️ Session expired due to inactivity. Please log in again.")
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown("## 🏗️ Agentic AI POC")
    st.caption("Nikitha Build Tech Pvt Ltd")
    st.divider()

    if is_authenticated():
        user = get_current_user()
        st.markdown(f"👤 **{user['full_name']}**")
        st.caption(f"Role: {user['role']}")
        st.divider()

        # Navigation hints based on role
        role = user["role"]
        if role == "Director":
            st.info("📌 Go to **Director Dashboard** for org-level analytics")
        elif role == "Project Manager":
            st.info("📌 Go to **PM Dashboard** to review & approve reports")
        elif role == "Project Engineer":
            st.info("📌 Go to **Daily Reports** to submit your report")
        elif role == "Admin":
            st.info("📌 Go to **Admin** to manage users & projects")

        # Notifications
        notifs = get_notifications_for_role(role)
        if notifs:
            st.divider()
            st.markdown(f"🔔 **Notifications** ({len(notifs)})")
            for n in notifs[:5]:
                icon = "🔴" if n["severity"] == "CRITICAL" else "🟡" if n["severity"] == "WARNING" else "🔵"
                st.caption(f"{icon} {n['message']}")

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()
    else:
        st.info("🔒 Please log in to access the system")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN CONTENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if not is_authenticated():
    # ── LOGIN PAGE ──
    st.markdown("""
        <div style="text-align:center; padding: 30px 0 10px 0;">
            <h1 style="color: #f8f9fa; font-weight: 300; font-size: 2.5rem;">
                🏗️ Agentic AI Construction
            </h1>
            <p style="color: #8c9097; font-size: 1rem; letter-spacing: 1px;">
                NIKITHA BUILD TECH PVT LTD
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Login form
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown("### Sign In")

        user_id = st.text_input("User ID", placeholder="e.g. director, pm1, pe1, admin")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        if st.button("🔑 Sign In", use_container_width=True, type="primary"):
            if user_id and password:
                user = authenticate(user_id, password)
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user
                    st.success(f"✅ Welcome, {user['full_name']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")
            else:
                st.warning("Please enter both User ID and Password.")

        # Demo credentials help
        with st.expander("🔑 Demo Credentials", expanded=False):
            st.markdown("""
            | User ID | Password | Role |
            |---------|----------|------|
            | `admin` | `admin123` | Admin |
            | `director` | `dir123` | Director |
            | `pm1` | `pm123` | Project Manager |
            | `pm2` | `pm123` | Project Manager |
            | `pe1` | `pe123` | Project Engineer |
            | `pe2` | `pe123` | Project Engineer |
            | `pe3` | `pe123` | Project Engineer |
            """)

else:
    # ── WELCOME DASHBOARD ──
    user = get_current_user()
    role = user["role"]

    st.markdown(f"""
        <div style="text-align:center; padding: 20px 0;">
            <h1 style="color: #f8f9fa; font-weight: 300;">
                Welcome, {user['full_name']}
            </h1>
            <p style="color: #8c9097; letter-spacing: 1.5px; text-transform: uppercase;">
                {role} • Agentic AI Construction POC
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Role-specific quick-access cards
    st.divider()

    if role == "Director":
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">🎯</p>
                <p class="kpi-label">Director Dashboard</p>
            </div>""", unsafe_allow_html=True)
            st.caption("Organization-level analytics, S-Curve, PDF export")
        with c2:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">💰</p>
                <p class="kpi-label">Budget & Analytics</p>
            </div>""", unsafe_allow_html=True)
            st.caption("Achievement tracking, cumulative progress")
        with c3:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">📦</p>
                <p class="kpi-label">BOQ & MRS</p>
            </div>""", unsafe_allow_html=True)
            st.caption("Bill of Quantities, Material Receipt Slips")

    elif role == "Project Manager":
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">📊</p>
                <p class="kpi-label">PM Dashboard</p>
            </div>""", unsafe_allow_html=True)
            st.caption("Review & approve reports, multi-project view")
        with c2:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">💰</p>
                <p class="kpi-label">Budget & Analytics</p>
            </div>""", unsafe_allow_html=True)
            st.caption("Project budgets, S-Curve, achievements")
        with c3:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">📦</p>
                <p class="kpi-label">BOQ & MRS</p>
            </div>""", unsafe_allow_html=True)
            st.caption("BOQ upload, MRS approval")

    elif role == "Project Engineer":
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">📝</p>
                <p class="kpi-label">Daily Reports</p>
            </div>""", unsafe_allow_html=True)
            st.caption("Submit Morning / Afternoon / Evening reports")
        with c2:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">📦</p>
                <p class="kpi-label">BOQ & MRS</p>
            </div>""", unsafe_allow_html=True)
            st.caption("Create MRS, track materials")
        with c3:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">💰</p>
                <p class="kpi-label">Budget & Analytics</p>
            </div>""", unsafe_allow_html=True)
            st.caption("View project progress and analytics")

    elif role == "Admin":
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">👤</p>
                <p class="kpi-label">Admin Panel</p>
            </div>""", unsafe_allow_html=True)
            st.caption("Manage users, projects, labour categories")
        with c2:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">🎯</p>
                <p class="kpi-label">Director Dashboard</p>
            </div>""", unsafe_allow_html=True)
            st.caption("Organization-level view (read-only)")
        with c3:
            st.markdown("""<div class="kpi-card">
                <p class="kpi-value">📝</p>
                <p class="kpi-label">Daily Reports</p>
            </div>""", unsafe_allow_html=True)
            st.caption("Submit yesterday's or today's reports")

    # Navigation instruction
    st.divider()
    st.markdown("""
        <div style="text-align:center; color: #6b7280; padding: 10px;">
            👈 Use the <b>sidebar navigation</b> to access different modules
        </div>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
        <div style="text-align:center; padding:30px 0; color:#4b5563; font-size:0.8rem;">
            🏗️ Agentic AI Construction POC — Nikitha Build Tech Pvt Ltd<br>
            Powered by AI Agents | Built with Streamlit
        </div>
    """, unsafe_allow_html=True)
