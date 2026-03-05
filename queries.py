"""
SQL queries for the ConstructIQ POC.
All queries are SELECT-only (read-only) against the Nikitha Build Tech database.
ALWAYS falls back to demo data when the database returns empty results.
"""

from db import run_query, is_demo_mode
import demo_data
import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────
# PROJECTS
# ──────────────────────────────────────────────

@st.cache_data(ttl=1)
def get_all_projects() -> pd.DataFrame:
    """Fetch all projects with key details."""
    if not is_demo_mode():
        sql = """
            SELECT
                id,
                name                AS project_name,
                project_code,
                project_description,
                loc                 AS location,
                planned_start_date,
                actual_start_date,
                planned_end_date,
                actual_end_date,
                execution_start_date,
                execution_end_date,
                total_price,
                man_power,
                status,
                remark,
                mnager_remark       AS manager_remark,
                created_date,
                modified_date
            FROM project
            ORDER BY id DESC
        """
        result = run_query(sql)
        if not result.empty:
            return result
    # Always fall back to demo data
    return demo_data.get_demo_projects()


@st.cache_data(ttl=1)
def get_project_by_id(project_id: int) -> pd.DataFrame:
    """Fetch a single project by ID."""
    if not is_demo_mode():
        sql = """
            SELECT
                id,
                name                AS project_name,
                project_code,
                project_description,
                loc                 AS location,
                planned_start_date,
                actual_start_date,
                planned_end_date,
                actual_end_date,
                execution_start_date,
                execution_end_date,
                total_price,
                man_power,
                status,
                remark,
                mnager_remark       AS manager_remark
            FROM project
            WHERE id = %s
        """
        result = run_query(sql, (project_id,))
        if not result.empty:
            return result
    return demo_data.get_demo_project_by_id(project_id)


# ──────────────────────────────────────────────
# EXPENSES
# ──────────────────────────────────────────────

@st.cache_data(ttl=1)
def get_project_expenses(project_id: int) -> pd.DataFrame:
    """Daily expenses for a project, grouped by date and type."""
    if not is_demo_mode():
        sql = """
            SELECT
                reporting_date,
                parent_type,
                child_type,
                amount,
                report_timing
            FROM expenes_daily_report
            WHERE project_id = %s
            ORDER BY reporting_date
        """
        result = run_query(sql, (project_id,))
        if not result.empty:
            return result
    return demo_data.get_demo_expenses(project_id)


@st.cache_data(ttl=1)
def get_total_expenses_by_project(project_id: int) -> float:
    """Total expenses for a project."""
    if not is_demo_mode():
        sql = """
            SELECT COALESCE(SUM(amount), 0) AS total_expense
            FROM expenes_daily_report
            WHERE project_id = %s
        """
        df = run_query(sql, (project_id,))
        if not df.empty and df["total_expense"].iloc[0] > 0:
            return float(df["total_expense"].iloc[0])
    return demo_data.get_demo_total_expenses(project_id)


# ──────────────────────────────────────────────
# MANPOWER
# ──────────────────────────────────────────────

@st.cache_data(ttl=1)
def get_project_manpower(project_id: int) -> pd.DataFrame:
    """Daily manpower reports for a project."""
    if not is_demo_mode():
        sql = """
            SELECT
                reported_date,
                man_power_type,
                man_count,
                reporting_time,
                remark
            FROM manpower_daily_report
            WHERE project_id = %s
            ORDER BY reported_date
        """
        result = run_query(sql, (project_id,))
        if not result.empty:
            return result
    return demo_data.get_demo_manpower(project_id)


# ──────────────────────────────────────────────
# MATERIAL USAGE
# ──────────────────────────────────────────────

@st.cache_data(ttl=1)
def get_project_materials(project_id: int) -> pd.DataFrame:
    """Daily material usage for a project, joined with BOQ line details."""
    if not is_demo_mode():
        sql = """
            SELECT
                m.daily_report_date,
                m.used_material,
                m.daily_report_timing,
                bl.line_item_name,
                bl.unit_of_measurement,
                pbs.scope_quantity
            FROM material_uses_daily_report m
            LEFT JOIN project_boq_scope pbs ON pbs.id = m.project_boq_scope_id
            LEFT JOIN boq_lines bl ON bl.id = m.line_id
            WHERE m.project_id = %s
            ORDER BY m.daily_report_date
        """
        result = run_query(sql, (project_id,))
        if not result.empty:
            return result
    return demo_data.get_demo_materials(project_id)


# ──────────────────────────────────────────────
# MACHINERY
# ──────────────────────────────────────────────

@st.cache_data(ttl=1)
def get_project_machinery(project_id: int) -> pd.DataFrame:
    """Daily machinery usage for a project."""
    if not is_demo_mode():
        sql = """
            SELECT
                report_date,
                parent_type,
                child_type,
                start_time,
                end_time,
                submit_timing,
                remark
            FROM daily_machinery_usage
            WHERE project_id = %s
            ORDER BY report_date
        """
        result = run_query(sql, (project_id,))
        if not result.empty:
            return result
    return demo_data.get_demo_machinery(project_id)


# ──────────────────────────────────────────────
# BOQ (Bill of Quantities)
# ──────────────────────────────────────────────

@st.cache_data(ttl=1)
def get_project_boq_scope(project_id: int) -> pd.DataFrame:
    """BOQ items scoped to a project."""
    if not is_demo_mode():
        sql = """
            SELECT
                pbs.id              AS scope_id,
                bh.parent_item_code,
                bh.parent_item_name,
                bl.line_item_code,
                bl.line_item_name,
                bl.unit_of_measurement,
                pbs.scope_quantity,
                pbs.revision
            FROM project_boq_scope pbs
            JOIN boq_lines bl ON bl.id = pbs.boq_lines_id
            JOIN boq_header bh ON bh.id = bl.boq_header_id
            WHERE pbs.project_id = %s
            ORDER BY bh.parent_item_code, bl.line_item_code
        """
        result = run_query(sql, (project_id,))
        if not result.empty:
            return result
    return demo_data.get_demo_boq_scope(project_id)


# ──────────────────────────────────────────────
# DAILY REPORT APPROVALS
# ──────────────────────────────────────────────

@st.cache_data(ttl=1)
def get_daily_report_approvals(project_id: int) -> pd.DataFrame:
    """Daily report approval status for a project."""
    if not is_demo_mode():
        sql = """
            SELECT
                dra.reported_date,
                dra.reporting_time,
                dra.status,
                dra.pe_remark,
                dra.pm_remark,
                dra.dir_remark,
                u.full_name         AS submitted_by_name
            FROM daily_report_approval dra
            LEFT JOIN users u ON u.id = dra.submitted_by
            WHERE dra.project_id = %s
            ORDER BY dra.reported_date DESC
        """
        result = run_query(sql, (project_id,))
        if not result.empty:
            return result
    return demo_data.get_demo_approvals(project_id)


# ──────────────────────────────────────────────
# MRS (Material Receipt Slips)
# ──────────────────────────────────────────────

@st.cache_data(ttl=1)
def get_mrs_status(project_id: int) -> pd.DataFrame:
    """Material receipt slip approval statuses for a project."""
    if not is_demo_mode():
        sql = """
            SELECT
                mat.mrs_token_name,
                mat.approval_status,
                mat.approval_time,
                md.mrs_recipt_name,
                md.received_quantity,
                bl.line_item_name
            FROM mrs_approval_table mat
            LEFT JOIN mrs_details md ON md.approval_table_id = mat.id
            LEFT JOIN boq_lines bl ON bl.id = md.line_item_id
            WHERE mat.project_id = %s
            ORDER BY mat.created_time DESC
        """
        result = run_query(sql, (project_id,))
        if not result.empty:
            return result
    return demo_data.get_demo_mrs(project_id)


# ──────────────────────────────────────────────
# USERS & ROLES
# ──────────────────────────────────────────────

@st.cache_data(ttl=1)
def get_project_users(project_id: int) -> pd.DataFrame:
    """Users assigned to a project with their roles."""
    if not is_demo_mode():
        sql = """
            SELECT
                u.id                AS user_id,
                u.full_name,
                u.email_id,
                u.mobile,
                r.role_name,
                pum.status,
                pum.start_date,
                pum.end_date
            FROM project_user_mapping pum
            JOIN users u ON u.id = pum.user_id
            LEFT JOIN role r ON r.id = pum.role_id
            WHERE pum.project_id = %s
            ORDER BY r.role_name, u.full_name
        """
        result = run_query(sql, (project_id,))
        if not result.empty:
            return result
    return demo_data.get_demo_users(project_id)
