"""Construction planning for a heuristic three-element Yagi.

This module provides an auditable cut schedule and printable shop sheet.
It does not certify electrical performance, mechanical loads or RF safety.
"""
from io import BytesIO
import math

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)

from rf_lab.yagi import cutting_list

UNIT_SCALE = {"cm": 100.0, "in": 39.37007874015748, "mm": 1000.0}
STEPS = (
    "Verify dimensions against your chosen element material, mounts and feed method; these are heuristic starting lengths.",
    "Measure and mark the boom positions from the reflector reference end; dry-fit mounts before drilling.",
    "Cut elements with the selected positive trim allowance; deburr and label each piece.",
    "Mount reflector and director centered and square to the boom. Confirm element insulation and spacing.",
    "Mount the two driven arms symmetrically, preserving the specified center feed gap; fit suitable insulated feed supports.",
    "Install the selected feedline, matching network and strain relief. Check continuity and intended isolation before energizing.",
    "Secure the assembly and verify all mechanical connections. Keep the antenna well clear of overhead electrical lines.",
    "Measure resonance and SWR at low power with a calibrated antenna analyzer; trim incrementally and remeasure.",
    "Document final dimensions and measured results. Do not assume gain, matching or safe transmit power from this plan.",
)


def construction_plan(design, trim_allowance_mm=0.0):
    """Return nominal and initial cut lengths, positions and a materials checklist.

    Allowance is added to *each physical cut piece*, not the complete driven
    element. The builder must trim and measure the final electrical dimensions.
    """
    if not math.isfinite(trim_allowance_mm) or not 0 <= trim_allowance_mm <= 100:
        raise ValueError("Trim allowance must be between 0 and 100 mm")
    allowance = trim_allowance_mm / 1000.0
    cuts = []
    for row in cutting_list(design):
        if not math.isfinite(row["length_m"]) or row["length_m"] <= 0:
            raise ValueError("Invalid cut length")
        cuts.append({
            "part": row["part"],
            "quantity": row["quantity"],
            "nominal_m": row["length_m"],
            "initial_cut_m": row["length_m"] + allowance,
        })
    materials = [
        ("Boom stock", 1, "At least reflector-to-director spacing plus mounting/end clearance"),
        ("Element stock", sum(row["quantity"] for row in cuts), "Cut pieces; diameter/material chosen by builder"),
        ("Element mounts", len(design.elements), "Check isolation and mechanical suitability"),
        ("Driven-element insulators", 1, "Feed gap support; configuration dependent"),
        ("Feedline and connector", 1, "Choose for frequency, impedance and weather exposure"),
        ("Matching/balun components", 1, "As determined by actual measured impedance"),
        ("Fasteners and strain relief", 1, "Quantity depends on mounting method"),
    ]
    return {
        "frequency_mhz": design.frequency_mhz,
        "boom_length_m": design.boom_length_m,
        "feed_gap_m": design.feed_gap_m,
        "trim_allowance_mm": trim_allowance_mm,
        "positions": [(element.name, element.position_m) for element in design.elements],
        "cuts": cuts,
        "materials": materials,
        "steps": STEPS,
    }


def printable_plan_pdf(plan, unit="cm"):
    """Create a letter-size multi-page shop packet with diagram and checklist."""
    if unit not in UNIT_SCALE:
        raise ValueError("Unsupported length unit")
    scale = UNIT_SCALE[unit]
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=42,
                            rightMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("RF Lab | Antenna Construction Sheet", styles["Title"]),
        Paragraph(f"Three-element Yagi | {plan['frequency_mhz']:.3f} MHz", styles["Heading2"]),
        Paragraph("HEURISTIC STARTING GEOMETRY - VERIFY BY MEASUREMENT", styles["Heading3"]),
        Paragraph("Lengths include no kerf compensation or mounting corrections. "
                  "A positive allowance is added to every physical cut piece. "
                  "Never treat these dimensions as validated performance or structural specifications.",
                  styles["BodyText"]),
        Spacer(1, 14),
    ]
    def table(data, widths):
        t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,0),colors.HexColor("#14354a")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),.35,colors.HexColor("#aab9c8")),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),
             [colors.white,colors.HexColor("#f1f5f9")]),
            ("BOTTOMPADDING",(0,0),(-1,-1),7),
            ("TOPPADDING",(0,0),(-1,-1),7),
        ]))
        return t
    story.append(Paragraph("Cutting schedule", styles["Heading2"]))
    rows = [["Part","Qty",f"Nominal ({unit})",f"Initial cut ({unit})"]]
    for cut in plan["cuts"]:
        rows.append([cut["part"],str(cut["quantity"]),
                     f'{cut["nominal_m"]*scale:.2f}',
                     f'{cut["initial_cut_m"]*scale:.2f}'])
    story.append(table(rows,[174,42,128,128]))
    story.append(Spacer(1,8))
    story.append(Paragraph(
        f"Extra trim allowance: {plan['trim_allowance_mm']:.1f} mm per piece. "
        f"Feed gap: {plan['feed_gap_m']*scale:.2f} {unit}. "
        f"Reflector-to-director spacing: {plan['boom_length_m']*scale:.2f} {unit}.",
        styles["BodyText"]))
    story.append(Spacer(1,14))
    story.append(Paragraph("Boom layout | measured from reflector center",styles["Heading2"]))
    positions = [["Element",f"Position ({unit})"]]
    for name, position in plan["positions"]:
        positions.append([name,f"{position*scale:.2f}"])
    story.append(table(positions,[240,232]))
    story.append(Spacer(1,14))
    if "positions_from_boom_end" in plan:
        story.append(Paragraph("Tape-measure boom and mounting reference", styles["Heading2"]))
        story.append(Paragraph(
            f"PVC boom minimum stock length: {plan['boom_stock_m']*scale:.2f} {unit}. "
            f"End margin: {plan['boom_end_margin_mm']:.1f} mm at each end. "
            f"Tape width: {plan['tape_width_mm']:.1f} mm. "
            f"Total initial tape length: {plan['total_tape_m']*scale:.2f} {unit} "
            "(excludes kerf and waste).", styles["BodyText"]))
        physical = [["Element", f"Mark from physical boom end ({unit})"]]
        for name, position in plan["positions_from_boom_end"]:
            physical.append([name, f"{position*scale:.2f}"])
        story.append(Spacer(1,8))
        story.append(table(physical,[240,232]))
        story.append(Spacer(1,12))
    story.append(Paragraph("Materials checklist (verify specifications)",styles["Heading2"]))
    for name, qty, note in plan["materials"]:
        story.append(Paragraph(f"[ ] {qty} x <b>{name}</b> - {note}",styles["BodyText"]))
        story.append(Spacer(1,5))
    story.append(Spacer(1,12))
    story.append(Paragraph("Assembly and tuning checklist",styles["Heading2"]))
    for i, step in enumerate(plan["steps"],1):
        story.append(KeepTogether([
            Paragraph(f"[ ] {i}. {step}",styles["BodyText"]),Spacer(1,7)
        ]))
    story.append(Spacer(1,10))
    story.append(Paragraph("As-built notes: _________________________________",styles["BodyText"]))
    story.append(Paragraph("Measured frequency / SWR: _________________________",styles["BodyText"]))
    doc.build(story)
    return buffer.getvalue()
