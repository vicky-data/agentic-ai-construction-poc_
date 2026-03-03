"""
Database connection layer for the Agentic AI Construction POC.
Connects to the Nikitha Build Tech PostgreSQL database on AWS RDS.
All queries are READ-ONLY.
Gracefully falls back to demo mode when DB is unavailable.
"""

import streamlit as st
import pandas as pd

# Module-level flag: set to True when connection attempt fails
_force_demo = False


def is_demo_mode() -> bool:
    """Check if the app should run in demo mode (no credentials, or connection failed)."""
    global _force_demo
    if _force_demo:
        return True
    try:
        cfg = st.secrets.get("postgres", None)
        if cfg is None or not cfg.get("host"):
            return True
        return False
    except Exception:
        return True


def _activate_demo_mode():
    """Force demo mode on for the rest of this session."""
    global _force_demo
    _force_demo = True


def _get_psycopg2():
    """Lazily import psycopg2 to avoid ImportError when not installed or not needed."""
    try:
        import psycopg2
        import psycopg2.extras
        return psycopg2
    except ImportError:
        return None


@st.cache_resource
def get_connection():
    """
    Returns a psycopg2 connection using credentials from Streamlit secrets.
    Connection is cached across reruns via @st.cache_resource.
    """
    if _force_demo:
        return None

    psycopg2 = _get_psycopg2()
    if psycopg2 is None:
        _activate_demo_mode()
        return None

    try:
        cfg = st.secrets.get("postgres")
        if not cfg:
            _activate_demo_mode()
            return None
            
        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["dbname"],
            user=cfg["user"],
            password=cfg["password"],
            sslmode="require",
            connect_timeout=10,
            options="-c statement_timeout=30000",
        )
        conn.set_session(readonly=True, autocommit=True)
        return conn
    except Exception:
        _activate_demo_mode()
        return None


def run_query(sql: str, params: tuple = None) -> pd.DataFrame:
    """
    Execute a read-only SQL query and return results as a pandas DataFrame.
    """
    # If we are in demo mode, we should never reach this function 
    # (queries.py intercepts it). But just in case:
    if is_demo_mode():
        return pd.DataFrame()

    conn = get_connection()
    if conn is None:
        return pd.DataFrame()

    try:
        conn.isolation_level
    except Exception:
        get_connection.clear()
        conn = get_connection()
        if conn is None:
            return pd.DataFrame()

    try:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            get_connection.clear()
        return pd.DataFrame()


def test_connection() -> bool:
    """Quick health check — attempts connection once and falls back instantly if it fails."""
    if is_demo_mode():
        return False
        
    conn = get_connection()
    if conn is None:
        return False
        
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            return True
    except Exception:
        _activate_demo_mode()
        get_connection.clear()
        return False
