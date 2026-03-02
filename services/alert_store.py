"""
Alert Store — In-memory alert log using Streamlit session state.
"""

import streamlit as st
from datetime import datetime


def _ensure_store():
    """Initialize alert store in session state if not present."""
    if "alerts" not in st.session_state:
        st.session_state.alerts = []


def add_alert(alert_type: str, message: str, severity: str = "INFO", project_name: str = ""):
    """Add an alert to the session store."""
    _ensure_store()
    st.session_state.alerts.insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": alert_type,
        "message": message,
        "severity": severity,
        "project": project_name,
    })
    # Keep max 100 alerts
    st.session_state.alerts = st.session_state.alerts[:100]


def get_alerts() -> list[dict]:
    """Return all alerts, newest first."""
    _ensure_store()
    return st.session_state.alerts


def clear_alerts():
    """Clear all alerts."""
    st.session_state.alerts = []


def get_severity_badge(severity: str) -> str:
    """Return an emoji badge for the severity level."""
    badges = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
        "INFO": "🔵",
    }
    return badges.get(severity, "⚪")
