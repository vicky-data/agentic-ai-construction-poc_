"""
Authentication module for the Agentic AI Construction POC.
Provides role-based access control with demo credentials.
"""

import streamlit as st
from datetime import datetime, timedelta

# ──────────────────────────────────────────────
# DEMO USERS (In production, these come from the DB)
# ──────────────────────────────────────────────

DEMO_USERS = {
    "admin": {
        "password": "admin123",
        "full_name": "System Administrator",
        "role": "Admin",
        "email": "admin@nikithabuildtech.com",
        "projects": [1, 2, 3],
    },
    "director": {
        "password": "dir123",
        "full_name": "Vikram Sharma",
        "role": "Director",
        "email": "vikram@nikithabuildtech.com",
        "projects": [1, 2, 3],
    },
    "pm1": {
        "password": "pm123",
        "full_name": "Priya Reddy",
        "role": "Project Manager",
        "email": "priya@nikithabuildtech.com",
        "projects": [1, 2],
    },
    "pm2": {
        "password": "pm123",
        "full_name": "Suresh Babu",
        "role": "Project Manager",
        "email": "suresh@nikithabuildtech.com",
        "projects": [3],
    },
    "pe1": {
        "password": "pe123",
        "full_name": "Rajesh Kumar",
        "role": "Project Engineer",
        "email": "rajesh@nikithabuildtech.com",
        "projects": [1],
    },
    "pe2": {
        "password": "pe123",
        "full_name": "Srinivas Reddy",
        "role": "Project Engineer",
        "email": "srinivas@nikithabuildtech.com",
        "projects": [2],
    },
    "pe3": {
        "password": "pe123",
        "full_name": "Arjun Singh",
        "role": "Project Engineer",
        "email": "arjun@nikithabuildtech.com",
        "projects": [3],
    },
}

# Role hierarchy for dropdowns
ROLE_HIERARCHY = ["Director", "Project Manager", "Project Engineer"]

# Report time windows
REPORT_WINDOWS = {
    "MORNING":   {"start": 6,  "end": 12, "label": "Morning (6 AM – 12 PM)"},
    "AFTERNOON": {"start": 12, "end": 16, "label": "Afternoon (12 PM – 4 PM)"},
    "EVENING":   {"start": 16, "end": 20, "label": "Evening (4 PM – 8 PM)"},
}

# ──────────────────────────────────────────────
# AUTH FUNCTIONS
# ──────────────────────────────────────────────

def authenticate(user_id: str, password: str) -> dict | None:
    """Validate credentials and return user dict or None."""
    user = DEMO_USERS.get(user_id.lower().strip())
    if user and user["password"] == password:
        return {
            "user_id": user_id.lower().strip(),
            "full_name": user["full_name"],
            "role": user["role"],
            "email": user["email"],
            "projects": user["projects"],
            "login_time": datetime.now().isoformat(),
        }
    return None


def init_session():
    """Initialize session state keys if not present."""
    defaults = {
        "authenticated": False,
        "user": None,
        "last_activity": datetime.now(),
        "submitted_reports": [],
        "pending_approvals": [],
        "mrs_records": [],
        "boq_data": None,
        "budget_data": None,
        "notifications": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def is_authenticated() -> bool:
    """Check if user is logged in."""
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict | None:
    """Return current user dict."""
    return st.session_state.get("user", None)


def get_user_role() -> str:
    """Return role string of current user."""
    user = get_current_user()
    return user["role"] if user else ""


def require_role(*allowed_roles):
    """Block access if user's role is not in allowed_roles. Returns True if blocked."""
    if not is_authenticated():
        st.warning("🔒 Please log in from the Home page.")
        st.stop()
        return True
    role = get_user_role()
    if role not in allowed_roles:
        st.error(f"⛔ Access denied. This page requires: {', '.join(allowed_roles)}")
        st.stop()
        return True
    # Update last activity
    st.session_state["last_activity"] = datetime.now()
    return False


def check_idle_timeout(minutes: int = 10) -> bool:
    """Return True if user has been idle longer than `minutes`."""
    last = st.session_state.get("last_activity")
    if last and (datetime.now() - last) > timedelta(minutes=minutes):
        logout()
        return True
    return False


def logout():
    """Clear session and log out."""
    st.session_state["authenticated"] = False
    st.session_state["user"] = None


def get_current_report_window() -> str | None:
    """Return which report window is currently active, or None if outside all windows."""
    hour = datetime.now().hour
    for key, window in REPORT_WINDOWS.items():
        if window["start"] <= hour < window["end"]:
            return key
    return None


def can_submit_report(role: str, report_date, report_timing: str) -> tuple[bool, str]:
    """
    Check if a report can be submitted based on role and timing rules.
    Returns (allowed, reason).
    """
    today = datetime.now().date()

    # PEs cannot submit for previous days
    if role == "Project Engineer" and report_date < today:
        return False, "Project Engineers cannot submit reports for previous days."

    # Admin can submit yesterday's or today's
    if role == "Admin":
        yesterday = today - timedelta(days=1)
        if report_date < yesterday:
            return False, "Admin can only submit for yesterday or today."
        return True, "OK"

    # Check timing window for PEs
    if role == "Project Engineer":
        current_window = get_current_report_window()
        if current_window is None:
            return False, "No report submission window is currently active (6AM–8PM)."
        if report_timing != current_window:
            return False, f"Current window is {REPORT_WINDOWS[current_window]['label']}. Request PM approval to submit for a different slot."

    return True, "OK"


def add_notification(message: str, severity: str = "INFO", target_roles: list = None):
    """Add a notification to session state."""
    notif = {
        "message": message,
        "severity": severity,
        "time": datetime.now().strftime("%H:%M:%S"),
        "target_roles": target_roles or [],
    }
    if "notifications" not in st.session_state:
        st.session_state["notifications"] = []
    st.session_state["notifications"].insert(0, notif)


def get_notifications_for_role(role: str) -> list:
    """Get notifications visible to a specific role."""
    all_notifs = st.session_state.get("notifications", [])
    return [n for n in all_notifs if not n["target_roles"] or role in n["target_roles"]]
