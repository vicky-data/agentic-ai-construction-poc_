"""
Data Module — Replaces fake demo data with the REAL client PostgreSQL snapshot data.
Reads parsed CSV files securely to act as a "streaming" local flat-file database suitable for Streamlit Cloud.
"""

import pandas as pd
import os

CSV_DIR = os.path.join(os.path.dirname(__file__), "sql_data", "parsed_csvs")

# Helper to load CSV cleanly
def _load_csv(table_name):
    path = os.path.join(CSV_DIR, f"{table_name}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

# Cached DataFrames
_projects_df = _load_csv("project")
_expenses_df = _load_csv("expenes_daily_report")
_manpower_df = _load_csv("manpower_daily_report")
_materials_df = _load_csv("material_uses_daily_report")
_machinery_df = _load_csv("daily_machinery_usage")
_boq_scope_df = _load_csv("project_boq_scope")
_boq_lines_df = _load_csv("boq_lines")
_boq_header_df = _load_csv("boq_header")
_approvals_df = _load_csv("daily_report_approval")
_mrs_approval_df = _load_csv("mrs_approval_table")
_mrs_details_df = _load_csv("mrs_details")
_users_df = _load_csv("users")
_pum_df = _load_csv("project_user_mapping")
_role_df = _load_csv("role")

# ──────────────────────────────────────────────
# PROJECTS
# ──────────────────────────────────────────────
def get_demo_projects() -> pd.DataFrame:
    df = _projects_df.copy()
    if df.empty: return df
    df = df.rename(columns={
        "name": "project_name",
        "loc": "location",
        "mnager_remark": "manager_remark"
    })
    # Force correct data types
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.sort_values(by="id", ascending=False).reset_index(drop=True)
    return df

def get_demo_project_by_id(project_id: int) -> pd.DataFrame:
    df = get_demo_projects()
    if df.empty: return df
    return df[df["id"] == project_id].reset_index(drop=True)

# ──────────────────────────────────────────────
# EXPENSES
# ──────────────────────────────────────────────
def get_demo_expenses(project_id: int) -> pd.DataFrame:
    df = _expenses_df.copy()
    if df.empty: return df
    df["project_id"] = pd.to_numeric(df["project_id"], errors="coerce")
    df = df[df["project_id"] == project_id]
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    # Return specific columns
    cols = ["reporting_date", "parent_type", "child_type", "amount", "report_timing"]
    available_cols = [c for c in cols if c in df.columns]
    return df[available_cols].copy()

def get_demo_total_expenses(project_id: int) -> float:
    df = get_demo_expenses(project_id)
    if df.empty or "amount" not in df.columns: return 0.0
    return float(df["amount"].sum())

# ──────────────────────────────────────────────
# MANPOWER
# ──────────────────────────────────────────────
def get_demo_manpower(project_id: int) -> pd.DataFrame:
    df = _manpower_df.copy()
    if df.empty: return df
    df["project_id"] = pd.to_numeric(df["project_id"], errors="coerce")
    df = df[df["project_id"] == project_id]
    cols = ["reported_date", "man_power_type", "man_count", "reporting_time", "remark"]
    available_cols = [c for c in cols if c in df.columns]
    return df[available_cols].copy()

# ──────────────────────────────────────────────
# MATERIAL USAGE
# ──────────────────────────────────────────────
def get_demo_materials(project_id: int) -> pd.DataFrame:
    m = _materials_df.copy()
    if m.empty: return pd.DataFrame()
    
    m["project_id"] = pd.to_numeric(m["project_id"], errors="coerce")
    m = m[m["project_id"] == project_id]
    
    pbs = _boq_scope_df.copy()
    bl = _boq_lines_df.copy()
    
    if not pbs.empty:
        pbs["id"] = pd.to_numeric(pbs["id"], errors="coerce")
        m["project_boq_scope_id"] = pd.to_numeric(m["project_boq_scope_id"], errors="coerce")
        m = m.merge(pbs, left_on="project_boq_scope_id", right_on="id", how="left", suffixes=("", "_pbs"))
    else:
        m["scope_quantity"] = 0
        
    if not bl.empty:
        bl["id"] = pd.to_numeric(bl["id"], errors="coerce")
        m["line_id"] = pd.to_numeric(m["line_id"], errors="coerce")
        m = m.merge(bl, left_on="line_id", right_on="id", how="left", suffixes=("", "_bl"))
    else:
        m["line_item_name"] = "Unknown"
        m["unit_of_measurement"] = "-"
        
    cols = ["daily_report_date", "used_material", "daily_report_timing", "line_item_name", "unit_of_measurement", "scope_quantity"]
    available = [c for c in cols if c in m.columns]
    return m[available].copy()

# ──────────────────────────────────────────────
# MACHINERY
# ──────────────────────────────────────────────
def get_demo_machinery(project_id: int) -> pd.DataFrame:
    df = _machinery_df.copy()
    if df.empty: return df
    df["project_id"] = pd.to_numeric(df["project_id"], errors="coerce")
    df = df[df["project_id"] == project_id]
    cols = ["report_date", "parent_type", "child_type", "start_time", "end_time", "submit_timing", "remark"]
    available = [c for c in cols if c in df.columns]
    return df[available].copy()

# ──────────────────────────────────────────────
# BOQ (Bill of Quantities)
# ──────────────────────────────────────────────
def get_demo_boq_scope(project_id: int) -> pd.DataFrame:
    pbs = _boq_scope_df.copy()
    if pbs.empty: return pd.DataFrame()
    
    pbs["project_id"] = pd.to_numeric(pbs["project_id"], errors="coerce")
    pbs = pbs[pbs["project_id"] == project_id]
    pbs = pbs.rename(columns={"id": "scope_id"})
    
    bl = _boq_lines_df.copy()
    bh = _boq_header_df.copy()
    
    if not bl.empty:
        bl["id"] = pd.to_numeric(bl["id"], errors="coerce")
        pbs["boq_lines_id"] = pd.to_numeric(pbs["boq_lines_id"], errors="coerce")
        pbs = pbs.merge(bl, left_on="boq_lines_id", right_on="id", how="inner")
        
        if not bh.empty:
            bh["id"] = pd.to_numeric(bh["id"], errors="coerce")
            pbs["boq_header_id"] = pd.to_numeric(pbs["boq_header_id"], errors="coerce")
            pbs = pbs.merge(bh, left_on="boq_header_id", right_on="id", how="inner")
            
    cols = ["scope_id", "parent_item_code", "parent_item_name", "line_item_code", "line_item_name", "unit_of_measurement", "scope_quantity", "revision"]
    available = [c for c in cols if c in pbs.columns]
    return pbs[available].copy()

# ──────────────────────────────────────────────
# DAILY REPORT APPROVALS
# ──────────────────────────────────────────────
def get_demo_approvals(project_id: int) -> pd.DataFrame:
    dra = _approvals_df.copy()
    if dra.empty: return pd.DataFrame()
    
    dra["project_id"] = pd.to_numeric(dra["project_id"], errors="coerce")
    dra = dra[dra["project_id"] == project_id]
    
    u = _users_df.copy()
    if not u.empty:
        u["id"] = pd.to_numeric(u["id"], errors="coerce")
        dra["submitted_by"] = pd.to_numeric(dra["submitted_by"], errors="coerce")
        dra = dra.merge(u, left_on="submitted_by", right_on="id", how="left")
        dra = dra.rename(columns={"full_name": "submitted_by_name"})
    else:
        dra["submitted_by_name"] = "Unknown"
        
    cols = ["reported_date", "reporting_time", "status", "pe_remark", "pm_remark", "dir_remark", "submitted_by_name"]
    available = [c for c in cols if c in dra.columns]
    # sort by date
    if 'reported_date' in available:
        dra = dra.sort_values(by="reported_date", ascending=False)
    return dra[available].copy()

# ──────────────────────────────────────────────
# MRS (Material Receipt Slips)
# ──────────────────────────────────────────────
def get_demo_mrs(project_id: int) -> pd.DataFrame:
    mat = _mrs_approval_df.copy()
    if mat.empty: return pd.DataFrame()
    
    mat["project_id"] = pd.to_numeric(mat["project_id"], errors="coerce")
    mat = mat[mat["project_id"] == project_id]
    
    md = _mrs_details_df.copy()
    bl = _boq_lines_df.copy()
    
    if not md.empty:
        md["approval_table_id"] = pd.to_numeric(md["approval_table_id"], errors="coerce")
        mat["id"] = pd.to_numeric(mat["id"], errors="coerce")
        mat = mat.merge(md, left_on="id", right_on="approval_table_id", how="left")
        
        if not bl.empty:
            bl["id"] = pd.to_numeric(bl["id"], errors="coerce")
            mat["line_item_id"] = pd.to_numeric(mat["line_item_id"], errors="coerce")
            mat = mat.merge(bl, left_on="line_item_id", right_on="id", how="left")
            
    cols = ["mrs_token_name", "approval_status", "approval_time", "mrs_recipt_name", "received_quantity", "line_item_name"]
    available = [c for c in cols if c in mat.columns]
    return mat[available].copy()

# ──────────────────────────────────────────────
# USERS & ROLES
# ──────────────────────────────────────────────
def get_demo_users(project_id: int) -> pd.DataFrame:
    pum = _pum_df.copy()
    if pum.empty: return pd.DataFrame()
    
    pum["project_id"] = pd.to_numeric(pum["project_id"], errors="coerce")
    pum = pum[pum["project_id"] == project_id]
    
    u = _users_df.copy()
    r = _role_df.copy()
    
    if not u.empty:
        u["id"] = pd.to_numeric(u["id"], errors="coerce")
        pum["user_id"] = pd.to_numeric(pum["user_id"], errors="coerce")
        pum = pum.merge(u, left_on="user_id", right_on="id", how="inner", suffixes=("", "_u"))
        pum = pum.rename(columns={"id": "user_id"})  # Original u.id
        
        if not r.empty:
            r["id"] = pd.to_numeric(r["id"], errors="coerce")
            pum["role_id"] = pd.to_numeric(pum["role_id"], errors="coerce")
            pum = pum.merge(r, left_on="role_id", right_on="id", how="left", suffixes=("", "_r"))
            
    cols = ["user_id", "full_name", "email_id", "mobile", "role_name", "status", "start_date", "end_date"]
    available = [c for c in cols if c in pum.columns]
    return pum[available].copy()
