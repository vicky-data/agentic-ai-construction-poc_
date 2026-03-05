"""
📦 BOQ & MRS — Bill of Quantities upload and Material Receipt Slips
Access: Project Engineer, Project Manager, Admin
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import require_role, get_current_user, init_session, add_notification
from queries import get_all_projects, get_project_boq_scope, get_mrs_status

st.set_page_config(page_title="BOQ & MRS", page_icon="📦", layout="wide")

init_session()
require_role("Project Engineer", "Project Manager", "Admin", "Director")
user = get_current_user()

st.markdown("""
<div style="text-align:center; padding:10px 0 20px 0;">
    <h1 style="color:#1e293b; font-weight:300;">📦 BOQ & Material Receipt Slips</h1>
    <p style="color:#64748b; letter-spacing:1.5px; text-transform:uppercase;">
        Bill of Quantities • MRS Management
    </p>
</div>
""", unsafe_allow_html=True)

projects_df = get_all_projects()
proj_options = []
for _, p in projects_df.iterrows():
    pname = p.get("project_name", "Project #" + str(p["id"]))
    proj_options.append(pname + " (#" + str(p["id"]) + ")")
sel_proj = st.selectbox("🏗️ Select Project", options=proj_options)
sel_proj_id = projects_df.iloc[0]["id"] if not projects_df.empty else 1

tab_boq, tab_mrs_create, tab_mrs_status, tab_material_compare = st.tabs([
    "📋 BOQ View & Upload", "📝 Create MRS", "📊 MRS Status", "📈 Material vs BOQ"
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: BOQ VIEW & UPLOAD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_boq:
    st.markdown("### 📋 Bill of Quantities")

    # Existing BOQ from DB/demo
    boq_df = get_project_boq_scope(sel_proj_id)
    if not boq_df.empty:
        # Grouped summary view
        st.markdown("**Grouped Summary:**")
        if "parent_item_name" in boq_df.columns:
            for group_name, group_df in boq_df.groupby("parent_item_name"):
                with st.expander(f"📂 {group_name}", expanded=True):
                    display_cols = [c for c in ["line_item_code", "line_item_name", "unit_of_measurement", "scope_quantity", "revision"] if c in group_df.columns]
                    st.dataframe(group_df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.dataframe(boq_df, use_container_width=True)
    else:
        st.info("No BOQ data available for this project.")

    st.divider()
    st.markdown("### 📤 Upload BOQ (CSV)")
    st.caption("CSV Format: parent_item_code, parent_item_name, line_item_code, line_item_name, unit_of_measurement, scope_quantity")

    uploaded_boq = st.file_uploader("Upload BOQ CSV", type=["csv"], key="boq_upload")
    if uploaded_boq:
        try:
            new_boq = pd.read_csv(uploaded_boq)
            st.success(f"✅ Uploaded {len(new_boq)} BOQ items")
            st.dataframe(new_boq, use_container_width=True)

            if st.button("💾 Save BOQ", use_container_width=True):
                st.session_state["boq_data"] = new_boq
                add_notification(f"BOQ uploaded for {sel_proj}", "INFO", ["Project Manager", "Director"])
                st.success("BOQ saved successfully!")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: CREATE MRS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_mrs_create:
    st.markdown("### 📝 Create Material Receipt Slip (MRS)")

    # Auto-generate MRS number
    existing_mrs = st.session_state.get("mrs_records", [])
    today_str = datetime.now().strftime("%Y%m%d")
    today_count = len([m for m in existing_mrs if m.get("date") == today_str]) + 1
    mrs_number = f"MRS-{today_str}-{today_count:03d}"

    st.info(f"📌 MRS Number: **{mrs_number}** (auto-generated)")

    # BOQ items for selection
    boq_items = []
    if not boq_df.empty and "line_item_name" in boq_df.columns:
        boq_items = boq_df["line_item_name"].unique().tolist()
    boq_items.append("🆕 New Item (Not in BOQ)")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        selected_item = st.selectbox("Select BOQ Item", boq_items)
        if selected_item == "🆕 New Item (Not in BOQ)":
            new_item_name = st.text_input("New Item Name", placeholder="e.g., Waterproof Membrane")
        else:
            new_item_name = selected_item

    with col_m2:
        received_qty = st.number_input("Received Quantity", min_value=0.0, value=0.0, step=1.0)
        unit = st.selectbox("Unit", ["Bags", "Tonnes", "Cu.M", "Nos", "Metres", "Litres", "Kg", "Boxes"])

    supplier = st.text_input("Supplier Name", placeholder="e.g., Ultratech Cement Ltd")

    # Photo upload
    st.markdown("📷 **Attach Photo Proof**")
    photo = st.file_uploader("Upload photo of received materials", type=["jpg", "jpeg", "png"], key="mrs_photo")
    if photo:
        st.image(photo, caption="Uploaded Photo", width=300)

    remarks = st.text_area("Remarks", placeholder="Any observations about quality, quantity, etc.")

    if st.button("📤 Create MRS", use_container_width=True, type="primary"):
        if received_qty > 0:
            mrs_record = {
                "mrs_number": mrs_number,
                "date": today_str,
                "project_id": sel_proj_id,
                "project_name": sel_proj.split("(")[0].strip(),
                "item_name": new_item_name if selected_item == "🆕 New Item (Not in BOQ)" else selected_item,
                "received_quantity": received_qty,
                "unit": unit,
                "supplier": supplier,
                "has_photo": photo is not None,
                "remarks": remarks,
                "created_by": user["full_name"],
                "status": "PENDING",
                "created_at": datetime.now().isoformat(),
            }
            st.session_state.setdefault("mrs_records", []).append(mrs_record)
            add_notification(
                f"MRS {mrs_number} created: {mrs_record['item_name']} ({received_qty} {unit})",
                "INFO", ["Project Manager"]
            )
            st.success(f"✅ MRS {mrs_number} created successfully!")
            st.balloons()
        else:
            st.warning("Please enter received quantity.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: MRS STATUS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_mrs_status:
    st.markdown("### 📊 MRS Approval Status")

    # From session + demo data
    mrs_db = get_mrs_status(sel_proj_id)
    mrs_session = [m for m in st.session_state.get("mrs_records", []) if m.get("project_id") == sel_proj_id]

    if not mrs_db.empty:
        st.markdown("**From Database:**")
        st.dataframe(mrs_db, use_container_width=True, hide_index=True)

    if mrs_session:
        st.markdown("**Recently Created:**")
        session_df = pd.DataFrame(mrs_session)
        display_cols = [c for c in ["mrs_number", "item_name", "received_quantity", "unit", "supplier", "status", "created_by", "created_at"] if c in session_df.columns]
        st.dataframe(session_df[display_cols], use_container_width=True, hide_index=True)

    if mrs_db.empty and not mrs_session:
        st.info("No MRS records found.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB: MATERIAL vs BOQ COMPARISON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_material_compare:
    st.markdown("### 📈 Material Received vs BOQ Scope")

    from queries import get_project_materials
    materials = get_project_materials(sel_proj_id)

    if not materials.empty and "line_item_name" in materials.columns and "scope_quantity" in materials.columns:
        materials["used_material"] = pd.to_numeric(materials["used_material"], errors="coerce").fillna(0)
        materials["scope_quantity"] = pd.to_numeric(materials["scope_quantity"], errors="coerce").fillna(0)

        comparison = materials.groupby("line_item_name").agg(
            total_used=("used_material", "sum"),
            scope=("scope_quantity", "first"),
            unit=("unit_of_measurement", "first"),
        ).reset_index()
        comparison["usage_pct"] = (comparison["total_used"] / comparison["scope"] * 100).round(1)
        comparison["status"] = comparison["usage_pct"].apply(
            lambda x: "🔴 Over" if x > 100 else "🟡 High" if x > 80 else "🟢 OK"
        )

        st.dataframe(comparison, use_container_width=True, hide_index=True)

        # Bar chart
        import plotly.express as px
        fig = px.bar(comparison, x="line_item_name", y=["total_used", "scope"],
                     barmode="group", title="Material Usage vs Scope",
                     color_discrete_sequence=["#d4af37", "#6b7280"])
        fig.update_layout(
            height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#475569", xaxis_title="", yaxis_title="Quantity",
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No material data available for comparison.")
