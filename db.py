"""
Database connection layer for the Agentic AI Construction POC.
Connects to the Nikitha Build Tech PostgreSQL database on AWS RDS.
All queries are READ-ONLY.
"""

import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor


@st.cache_resource
def get_connection():
    """
    Returns a psycopg2 connection using credentials from Streamlit secrets.
    Connection is cached across reruns via @st.cache_resource.
    """
    try:
        cfg = st.secrets["postgres"]
        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["dbname"],
            user=cfg["user"],
            password=cfg["password"],
            sslmode="require",
            connect_timeout=15,
            options="-c statement_timeout=30000",  # 30s timeout for safety
        )
        conn.set_session(readonly=True, autocommit=True)
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.info("💡 If running on Streamlit Cloud, ensure your AWS RDS instance has 'Publicly Accessible' set to **Yes** and the security group allows inbound connections on port 5432 from 0.0.0.0/0.")
        return None


def run_query(sql: str, params: tuple = None) -> pd.DataFrame:
    """
    Execute a read-only SQL query and return results as a pandas DataFrame.
    Automatically reconnects if the connection was lost.
    """
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()

    try:
        # Check if connection is still alive
        conn.isolation_level
    except Exception:
        # Connection lost — clear cache and reconnect
        get_connection.clear()
        conn = get_connection()
        if conn is None:
            return pd.DataFrame()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Query failed: {e}")
        # Reset connection on error
        try:
            conn.rollback()
        except Exception:
            get_connection.clear()
        return pd.DataFrame()


def test_connection() -> bool:
    """Quick health check — returns True if DB is reachable."""
    conn = get_connection()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            return True
    except Exception:
        get_connection.clear()
        return False
