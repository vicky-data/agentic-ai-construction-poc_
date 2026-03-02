"""
Report Service — PDF report generation using ReportLab.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)


def generate_pdf_report(
    project_name: str,
    progress: dict,
    risk: dict,
    recommendations: list,
    expenses_summary: str = "",
    manpower_summary: str = "",
) -> bytes:
    """
    Generate a professional PDF report for a project.

    Returns:
        PDF as bytes (ready for st.download_button).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1E88E5"),
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#333333"),
        spaceBefore=15,
        spaceAfter=10,
    )
    body_style = styles["BodyText"]

    elements = []

    # ── Header ──
    elements.append(Paragraph(f"🏗️ Project Report — {project_name}", title_style))
    elements.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        body_style,
    ))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1E88E5")))
    elements.append(Spacer(1, 12))

    # ── Progress Summary ──
    elements.append(Paragraph("📊 Progress Summary", heading_style))
    progress_data = [
        ["Metric", "Value"],
        ["Health Status", progress.get("health", "N/A")],
        ["Time Elapsed", f"{progress.get('time_progress_pct', 0):.0f}%"],
        ["Days Remaining", str(progress.get("days_remaining", "N/A"))],
        ["Total Budget", f"₹{progress.get('total_budget', 0):,.0f}"],
        ["Total Spent", f"₹{progress.get('total_spent', 0):,.0f}"],
        ["Budget Used", f"{progress.get('cost_progress_pct', 0):.0f}%"],
        ["Cost Overrun", f"₹{progress.get('cost_overrun', 0):,.0f}"],
        ["Planned Start", str(progress.get("planned_start", "N/A"))],
        ["Planned End", str(progress.get("planned_end", "N/A"))],
    ]
    progress_table = Table(progress_data, colWidths=[3 * inch, 3 * inch])
    progress_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E88E5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(progress_table)
    elements.append(Spacer(1, 15))

    # ── Risk Assessment ──
    elements.append(Paragraph("⚠️ Risk Assessment", heading_style))
    elements.append(Paragraph(
        f"<b>Risk Level:</b> {risk.get('risk_level', 'N/A')} | "
        f"<b>Score:</b> {risk.get('risk_score', 0)}/10 | "
        f"<b>Confidence:</b> {risk.get('confidence', 0)}%",
        body_style,
    ))
    elements.append(Spacer(1, 5))

    for factor in risk.get("factors", []):
        elements.append(Paragraph(f"• {factor}", body_style))
    elements.append(Spacer(1, 15))

    # ── AI Recommendations ──
    elements.append(Paragraph("🤖 AI Recommendations", heading_style))
    if recommendations:
        rec_data = [["Priority", "Category", "Action"]]
        for rec in recommendations[:8]:
            rec_data.append([
                rec.get("priority", ""),
                rec.get("category", ""),
                rec.get("action", ""),
            ])
        rec_table = Table(rec_data, colWidths=[1.2 * inch, 1.2 * inch, 3.6 * inch])
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FF6D00")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF3E0")]),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(rec_table)
    else:
        elements.append(Paragraph("No recommendations at this time.", body_style))

    elements.append(Spacer(1, 15))

    # ── Additional Summaries ──
    if expenses_summary:
        elements.append(Paragraph("💰 Expense Summary", heading_style))
        elements.append(Paragraph(expenses_summary, body_style))
        elements.append(Spacer(1, 10))

    if manpower_summary:
        elements.append(Paragraph("👷 Manpower Summary", heading_style))
        elements.append(Paragraph(manpower_summary, body_style))
        elements.append(Spacer(1, 10))

    # ── Footer ──
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph(
        "<i>Generated by Agentic AI Construction POC — Nikitha Build Tech Pvt Ltd</i>",
        ParagraphStyle("Footer", parent=body_style, fontSize=8, textColor=colors.grey),
    ))

    doc.build(elements)
    return buffer.getvalue()
