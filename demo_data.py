"""
Demo Data Module — Provides realistic sample data for management demos.
Used when the PostgreSQL database is unavailable (e.g., Streamlit Cloud without RDS access).
All data mimics real Nikitha Build Tech project structures.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date


def _today():
    return datetime.now().date()


# ──────────────────────────────────────────────
# PROJECTS
# ──────────────────────────────────────────────

def get_demo_projects() -> pd.DataFrame:
    today = _today()
    return pd.DataFrame([
        {
            "id": 1,
            "project_name": "Gachibowli Sky Tower — 14 Floors",
            "project_code": "NBT-GT-2025",
            "project_description": "14-floor residential tower with basement parking and rooftop amenities",
            "location": "Gachibowli, Hyderabad",
            "planned_start_date": today - timedelta(days=180),
            "actual_start_date": today - timedelta(days=175),
            "planned_end_date": today + timedelta(days=120),
            "actual_end_date": None,
            "execution_start_date": today - timedelta(days=170),
            "execution_end_date": None,
            "total_price": 85000000.0,
            "man_power": 120,
            "status": "IN_PROGRESS",
            "remark": "Structural work on schedule. Interior fit-out phase starting.",
            "manager_remark": "Good progress. Monitor material costs closely.",
            "created_date": today - timedelta(days=200),
            "modified_date": today - timedelta(days=1),
        },
        {
            "id": 2,
            "project_name": "Jubilee Hills Premium Villa",
            "project_code": "NBT-JH-2025",
            "project_description": "Luxury 4BHK independent villa with landscaping and swimming pool",
            "location": "Jubilee Hills, Hyderabad",
            "planned_start_date": today - timedelta(days=90),
            "actual_start_date": today - timedelta(days=85),
            "planned_end_date": today + timedelta(days=45),
            "actual_end_date": None,
            "execution_start_date": today - timedelta(days=82),
            "execution_end_date": None,
            "total_price": 25000000.0,
            "man_power": 35,
            "status": "IN_PROGRESS",
            "remark": "Foundation and ground floor complete. First floor slab poured.",
            "manager_remark": "Slight delay in plumbing material delivery.",
            "created_date": today - timedelta(days=100),
            "modified_date": today - timedelta(days=2),
        },
        {
            "id": 3,
            "project_name": "Hitech City Commercial Complex",
            "project_code": "NBT-HC-2024",
            "project_description": "G+5 commercial office complex with co-working spaces",
            "location": "Hitech City, Hyderabad",
            "planned_start_date": today - timedelta(days=300),
            "actual_start_date": today - timedelta(days=295),
            "planned_end_date": today - timedelta(days=10),
            "actual_end_date": None,
            "execution_start_date": today - timedelta(days=290),
            "execution_end_date": None,
            "total_price": 120000000.0,
            "man_power": 200,
            "status": "IN_PROGRESS",
            "remark": "Interior and MEP work in final stages. Punch list items pending.",
            "manager_remark": "Project overdue by 10 days. Need to expedite finishing work.",
            "created_date": today - timedelta(days=320),
            "modified_date": today - timedelta(days=1),
        },
    ])


def get_demo_project_by_id(project_id: int) -> pd.DataFrame:
    df = get_demo_projects()
    return df[df["id"] == project_id].reset_index(drop=True)


# ──────────────────────────────────────────────
# EXPENSES
# ──────────────────────────────────────────────

def get_demo_expenses(project_id: int) -> pd.DataFrame:
    np.random.seed(project_id * 42)
    today = _today()

    budgets = {1: 85000000, 2: 25000000, 3: 120000000}
    budget = budgets.get(project_id, 50000000)
    days = {1: 170, 2: 82, 3: 290}
    num_days = days.get(project_id, 90)

    categories = [
        ("Labour", "Skilled Workers"),
        ("Labour", "Unskilled Workers"),
        ("Material", "Cement"),
        ("Material", "Steel"),
        ("Material", "Sand & Aggregate"),
        ("Equipment", "Crane Rental"),
        ("Equipment", "Excavator"),
        ("Overhead", "Site Office"),
        ("Overhead", "Safety Equipment"),
    ]

    rows = []
    for day_offset in range(num_days):
        report_date = today - timedelta(days=num_days - day_offset)
        # Generate 2-4 expense entries per day
        n_entries = np.random.randint(2, 5)
        for _ in range(n_entries):
            cat = categories[np.random.randint(0, len(categories))]
            # Scale amounts based on project budget
            base = budget / (num_days * 3)
            amount = round(base * np.random.uniform(0.3, 2.2), 2)
            rows.append({
                "reporting_date": report_date,
                "parent_type": cat[0],
                "child_type": cat[1],
                "amount": amount,
                "report_timing": np.random.choice(["MORNING", "EVENING"]),
            })

    return pd.DataFrame(rows)


def get_demo_total_expenses(project_id: int) -> float:
    df = get_demo_expenses(project_id)
    return float(df["amount"].sum()) if not df.empty else 0.0


# ──────────────────────────────────────────────
# MANPOWER
# ──────────────────────────────────────────────

def get_demo_manpower(project_id: int) -> pd.DataFrame:
    np.random.seed(project_id * 17)
    today = _today()

    base_counts = {1: {"Skilled": 45, "Unskilled": 60, "Supervisor": 8, "Helper": 15},
                   2: {"Skilled": 12, "Unskilled": 18, "Supervisor": 3, "Helper": 5},
                   3: {"Skilled": 70, "Unskilled": 100, "Supervisor": 15, "Helper": 25}}
    counts = base_counts.get(project_id, {"Skilled": 20, "Unskilled": 30, "Supervisor": 5, "Helper": 8})

    days = {1: 170, 2: 82, 3: 290}
    num_days = days.get(project_id, 90)

    rows = []
    for day_offset in range(num_days):
        report_date = today - timedelta(days=num_days - day_offset)
        for mp_type, base_count in counts.items():
            # Add natural variation, with a slight dip in recent days for project 3
            variation = np.random.uniform(0.7, 1.3)
            if project_id == 3 and day_offset > num_days - 14:
                variation *= 0.6  # Simulating manpower drop
            count = max(1, int(base_count * variation))
            rows.append({
                "reported_date": report_date,
                "man_power_type": mp_type,
                "man_count": count,
                "reporting_time": np.random.choice(["MORNING", "EVENING"]),
                "remark": "",
            })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# MATERIALS
# ──────────────────────────────────────────────

def get_demo_materials(project_id: int) -> pd.DataFrame:
    np.random.seed(project_id * 31)
    today = _today()

    materials = [
        {"line_item_name": "OPC Cement 53 Grade", "unit_of_measurement": "Bags", "scope_quantity": 5000},
        {"line_item_name": "TMT Steel 12mm", "unit_of_measurement": "Tonnes", "scope_quantity": 120},
        {"line_item_name": "River Sand (Fine)", "unit_of_measurement": "Cu.M", "scope_quantity": 800},
        {"line_item_name": "M20 Ready Mix Concrete", "unit_of_measurement": "Cu.M", "scope_quantity": 1200},
        {"line_item_name": "Red Bricks (Standard)", "unit_of_measurement": "Nos", "scope_quantity": 50000},
        {"line_item_name": "CPVC Pipes 1 inch", "unit_of_measurement": "Metres", "scope_quantity": 2000},
    ]

    days = {1: 170, 2: 82, 3: 290}
    num_days = days.get(project_id, 90)

    rows = []
    for day_offset in range(0, num_days, 3):  # Materials recorded every 3 days
        report_date = today - timedelta(days=num_days - day_offset)
        mat = materials[np.random.randint(0, len(materials))]
        used = round(mat["scope_quantity"] / (num_days / 3) * np.random.uniform(0.5, 1.8), 1)
        rows.append({
            "daily_report_date": report_date,
            "used_material": used,
            "daily_report_timing": np.random.choice(["MORNING", "EVENING"]),
            "line_item_name": mat["line_item_name"],
            "unit_of_measurement": mat["unit_of_measurement"],
            "scope_quantity": mat["scope_quantity"],
        })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# MACHINERY
# ──────────────────────────────────────────────

def get_demo_machinery(project_id: int) -> pd.DataFrame:
    np.random.seed(project_id * 53)
    today = _today()

    machinery_types = [
        ("Excavator", "JCB 3DX"),
        ("Excavator", "Hitachi ZX130"),
        ("Crane", "Mobile Crane 20T"),
        ("Crane", "Tower Crane"),
        ("Mixer", "Concrete Mixer 10/7"),
        ("Truck", "Tipper 16T"),
        ("Truck", "Transit Mixer"),
        ("Compactor", "Vibratory Roller"),
    ]

    days = {1: 170, 2: 82, 3: 290}
    num_days = days.get(project_id, 90)

    rows = []
    for day_offset in range(0, num_days, 2):  # Machinery every 2 days
        report_date = today - timedelta(days=num_days - day_offset)
        n_machines = np.random.randint(1, 4)
        for _ in range(n_machines):
            mach = machinery_types[np.random.randint(0, len(machinery_types))]
            start_hour = np.random.randint(6, 10)
            duration = np.random.randint(4, 10)
            rows.append({
                "report_date": report_date,
                "parent_type": mach[0],
                "child_type": mach[1],
                "start_time": f"{start_hour:02d}:00",
                "end_time": f"{start_hour + duration:02d}:00",
                "submit_timing": "MORNING",
                "remark": "",
            })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# BOQ SCOPE
# ──────────────────────────────────────────────

def get_demo_boq_scope(project_id: int) -> pd.DataFrame:
    return pd.DataFrame([
        {"scope_id": 1, "parent_item_code": "CIV-01", "parent_item_name": "Civil Works",
         "line_item_code": "CIV-01-01", "line_item_name": "OPC Cement 53 Grade",
         "unit_of_measurement": "Bags", "scope_quantity": 5000, "revision": 0},
        {"scope_id": 2, "parent_item_code": "CIV-01", "parent_item_name": "Civil Works",
         "line_item_code": "CIV-01-02", "line_item_name": "TMT Steel 12mm",
         "unit_of_measurement": "Tonnes", "scope_quantity": 120, "revision": 0},
        {"scope_id": 3, "parent_item_code": "CIV-01", "parent_item_name": "Civil Works",
         "line_item_code": "CIV-01-03", "line_item_name": "M20 Ready Mix Concrete",
         "unit_of_measurement": "Cu.M", "scope_quantity": 1200, "revision": 1},
        {"scope_id": 4, "parent_item_code": "CIV-02", "parent_item_name": "Masonry",
         "line_item_code": "CIV-02-01", "line_item_name": "Red Bricks (Standard)",
         "unit_of_measurement": "Nos", "scope_quantity": 50000, "revision": 0},
        {"scope_id": 5, "parent_item_code": "PLB-01", "parent_item_name": "Plumbing",
         "line_item_code": "PLB-01-01", "line_item_name": "CPVC Pipes 1 inch",
         "unit_of_measurement": "Metres", "scope_quantity": 2000, "revision": 0},
        {"scope_id": 6, "parent_item_code": "ELE-01", "parent_item_name": "Electrical",
         "line_item_code": "ELE-01-01", "line_item_name": "Copper Wire 2.5 sqmm",
         "unit_of_measurement": "Metres", "scope_quantity": 8000, "revision": 0},
        {"scope_id": 7, "parent_item_code": "FIN-01", "parent_item_name": "Finishing",
         "line_item_code": "FIN-01-01", "line_item_name": "Interior Emulsion Paint",
         "unit_of_measurement": "Litres", "scope_quantity": 3000, "revision": 0},
    ])


# ──────────────────────────────────────────────
# DAILY REPORT APPROVALS
# ──────────────────────────────────────────────

def get_demo_approvals(project_id: int) -> pd.DataFrame:
    np.random.seed(project_id * 73)
    today = _today()

    days = {1: 170, 2: 82, 3: 290}
    num_days = days.get(project_id, 90)

    submitters = {
        1: "Rajesh Kumar",
        2: "Srinivas Reddy",
        3: "Arjun Singh",
    }

    rows = []
    for day_offset in range(num_days):
        report_date = today - timedelta(days=num_days - day_offset)
        # Skip some days randomly for project 3 to create report gaps
        if project_id == 3 and day_offset > num_days - 10 and np.random.random() < 0.5:
            continue
        status = np.random.choice(
            ["APPROVED", "APPROVED", "APPROVED", "PENDING", "REJECTED"],
            p=[0.6, 0.2, 0.1, 0.07, 0.03],
        )
        rows.append({
            "reported_date": report_date,
            "reporting_time": np.random.choice(["MORNING", "EVENING"]),
            "status": status,
            "pe_remark": "Verified on site" if status == "APPROVED" else "Review pending",
            "pm_remark": "Approved" if status == "APPROVED" else "",
            "dir_remark": "",
            "submitted_by_name": submitters.get(project_id, "Demo User"),
        })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# MRS (Material Receipt Slips)
# ──────────────────────────────────────────────

def get_demo_mrs(project_id: int) -> pd.DataFrame:
    np.random.seed(project_id * 97)

    items = [
        ("MRS-001", "OPC Cement 53 Grade", 200),
        ("MRS-002", "TMT Steel 12mm", 15),
        ("MRS-003", "River Sand (Fine)", 50),
        ("MRS-004", "Red Bricks (Standard)", 5000),
        ("MRS-005", "CPVC Pipes 1 inch", 100),
        ("MRS-006", "M20 Ready Mix Concrete", 30),
    ]

    rows = []
    for token_name, item_name, qty in items:
        status = np.random.choice(["APPROVED", "PENDING", "APPROVED"])
        rows.append({
            "mrs_token_name": token_name,
            "approval_status": status,
            "approval_time": datetime.now() - timedelta(days=np.random.randint(1, 30)),
            "mrs_recipt_name": f"RCT-{token_name}",
            "received_quantity": qty * np.random.uniform(0.8, 1.2),
            "line_item_name": item_name,
        })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# USERS & TEAM
# ──────────────────────────────────────────────

def get_demo_users(project_id: int) -> pd.DataFrame:
    today = _today()
    return pd.DataFrame([
        {"user_id": 1, "full_name": "Vikram Sharma", "email_id": "vikram@nikithabuildtech.com",
         "mobile": "9876543210", "role_name": "Director",
         "status": "ACTIVE", "start_date": today - timedelta(days=365), "end_date": None},
        {"user_id": 2, "full_name": "Priya Reddy", "email_id": "priya@nikithabuildtech.com",
         "mobile": "9876543211", "role_name": "Project Manager",
         "status": "ACTIVE", "start_date": today - timedelta(days=200), "end_date": None},
        {"user_id": 3, "full_name": "Rajesh Kumar", "email_id": "rajesh@nikithabuildtech.com",
         "mobile": "9876543212", "role_name": "Site Engineer",
         "status": "ACTIVE", "start_date": today - timedelta(days=180), "end_date": None},
        {"user_id": 4, "full_name": "Srinivas Rao", "email_id": "srinivas@nikithabuildtech.com",
         "mobile": "9876543213", "role_name": "Site Engineer",
         "status": "ACTIVE", "start_date": today - timedelta(days=150), "end_date": None},
        {"user_id": 5, "full_name": "Anitha Kumari", "email_id": "anitha@nikithabuildtech.com",
         "mobile": "9876543214", "role_name": "Accountant",
         "status": "ACTIVE", "start_date": today - timedelta(days=300), "end_date": None},
        {"user_id": 6, "full_name": "Mohammed Irfan", "email_id": "irfan@nikithabuildtech.com",
         "mobile": "9876543215", "role_name": "Safety Officer",
         "status": "ACTIVE", "start_date": today - timedelta(days=160), "end_date": None},
    ])
