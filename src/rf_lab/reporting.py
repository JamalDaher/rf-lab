"""Generate a portable PDF measurement report with vector SWR plots."""
from io import BytesIO
import math

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing, Line, String, PolyLine

from rf_lab.measurements import S1P, swr_from_gamma
from rf_lab.workbench import compare_sweeps


def _swr_plot(sweeps: dict[str, S1P]) -> Drawing:
    """Small vector plot; infinite SWR values are not connected."""
    width, height = 490, 210
    drawing = Drawing(width, height)
    x0, y0, x1, y1 = 48, 34, 470, 187
    drawing.add(Line(x0, y0, x0, y1, strokeColor=colors.black))
    drawing.add(Line(x0, y0, x1, y0, strokeColor=colors.black))
    all_f = [f/1e6 for sweep in sweeps.values() for f in sweep.frequencies_hz]
    xmin, xmax = min(all_f), max(all_f)
    if xmin == xmax:
        xmin -= .5
        xmax += .5
    finite_swr = [swr_from_gamma(g) for sweep in sweeps.values() for g in sweep.gamma
                  if math.isfinite(swr_from_gamma(g))]
    ymax = min(20, max(2.0, max(finite_swr, default=2.0)))
    drawing.add(String(x0, 10, f"{xmin:.3f} MHz", fontSize=9))
    drawing.add(String(x1-85, 10, f"{xmax:.3f} MHz", fontSize=9))
    drawing.add(String(5, y1-3, f"{ymax:.1f}", fontSize=9))
    drawing.add(String(5, y0, "1.0", fontSize=9))
    palette = [colors.blue, colors.red, colors.green, colors.purple, colors.orange]
    for index, (name, sweep) in enumerate(sweeps.items()):
        color = palette[index % len(palette)]
        segment = []
        for f, gamma in zip(sweep.frequencies_hz, sweep.gamma):
            value = swr_from_gamma(gamma)
            if not math.isfinite(value):
                if len(segment) >= 2:
                    drawing.add(PolyLine(segment, strokeColor=color, strokeWidth=1.5))
                segment = []
                continue
            x = x0 + (f/1e6-xmin)/(xmax-xmin)*(x1-x0)
            y = y0 + (min(value, ymax)-1)/(ymax-1)*(y1-y0)
            segment.extend([x,y])
        if len(segment) >= 4:
            drawing.add(PolyLine(segment, strokeColor=color, strokeWidth=1.5))
        drawing.add(String(x0 + (index % 3)*145, height-10-(index//3)*12,
                           name[:20], fontSize=8, fillColor=color))
    return drawing


def create_measurement_pdf(sweeps: dict[str, S1P], design_mhz: float,
                           notes: str = "") -> bytes:
    """Create a PDF report with summaries and a vector SWR chart."""
    if not math.isfinite(design_mhz) or design_mhz <= 0:
        raise ValueError("design frequency must be positive and finite")
    if not sweeps:
        raise ValueError("at least one sweep is required")
    if len(sweeps) > 10:
        raise ValueError("PDF reports support up to ten sweeps")
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, leftMargin=48, rightMargin=48)
    styles = getSampleStyleSheet()
    story = [Paragraph("RF Lab - NanoVNA Measurement Report", styles["Title"]),
             Spacer(1, 12),
             Paragraph(f"Design frequency: {design_mhz:.4f} MHz", styles["Normal"]),
             Spacer(1, 12)]
    rows = [["Sweep", "Points", "Min SWR", "Best match (MHz)", "Reactance-zero (MHz)"]]
    for summary in compare_sweeps(sweeps):
        roots = ", ".join(f"{v:.3f}" for v in summary.resonances_mhz[:4])
        if len(summary.resonances_mhz) > 4:
            roots += " ..."
        rows.append([summary.name[:18], str(summary.points),
                     f"{summary.minimum_swr:.3f}" if summary.minimum_swr is not None else "N/A",
                     f"{summary.best_match_mhz:.4f}" if summary.best_match_mhz is not None else "N/A",
                     roots or "None found"])
    table = Table(rows, colWidths=[100, 45, 65, 100, 190], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0),colors.lightgrey),
        ("GRID", (0,0),(-1,-1),0.3,colors.grey),
        ("VALIGN", (0,0),(-1,-1),"TOP"),
        ("FONTSIZE", (0,0),(-1,-1),8),
        ("LEFTPADDING",(0,0),(-1,-1),5),
        ("RIGHTPADDING",(0,0),(-1,-1),5),
    ]))
    story.extend([table, Spacer(1, 16), Paragraph("SWR across frequency", styles["Heading2"]),
                  _swr_plot(sweeps), Spacer(1, 10)])
    if notes.strip():
        from xml.sax.saxutils import escape
        story.append(Paragraph("Notes: " + escape(notes[:2000]), styles["Normal"]))
        story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Minimum SWR is not necessarily resonance. Reactance-zero frequencies "
        "are linearly interpolated and depend on calibration plane and sweep resolution. "
        "Reference-plane shifting is a modeled correction, not instrument calibration.",
        styles["Italic"]))
    doc.build(story)
    return output.getvalue()
