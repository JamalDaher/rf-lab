"""PDF report generator for traceable benchmark summaries (ReportLab)."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from .benchmark_reports import validate_summary,compare_summaries

def build_pdf(summary,baseline=None):
    """Return PDF bytes; no file I/O or external solver required."""
    current=validate_summary(summary)
    diff=compare_summaries(baseline,current) if baseline is not None else None
    buffer=BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=(595,842),leftMargin=44,rightMargin=44,
                          topMargin=48,bottomMargin=48)
    styles=getSampleStyleSheet()
    story=[Paragraph("RF Lab | Scientific Benchmark Report",styles["Title"]),
           Spacer(1,12),
           Paragraph("<b>Validation status: UNVALIDATED</b>",styles["Heading2"]),
           Paragraph("Numerical mesh sensitivity and solver comparison only. "
                     "Not a certified antenna measurement or physical accuracy result.",
                     styles["BodyText"]),Spacer(1,12)]
    metadata=[
        ("Solver version",current["solver_version"]),
        ("Frequency (MHz)",str(current["frequency_mhz"])),
        ("Wire radius (mm)",str(current["wire_radius_mm"])),
        ("Mesh sizes",", ".join(map(str,current["mesh_sizes"])))
    ]
    for name,value in metadata:
        story.append(Paragraph(f"<b>{escape(name)}:</b> {escape(value)}",styles["BodyText"]))
    story.extend([Spacer(1,14),Paragraph("Impedance comparison",styles["Heading2"])])
    table=[["Mesh","NEC R","NEC X","EFIE R","EFIE X","Error |Z|"]]
    for row in current["cases"]:
        table.append([str(row["segments_per_element"])]+[
            f"{row[k]:.3f}" for k in ("nec_real_ohm","nec_imag_ohm",
                                      "efie_real_ohm","efie_imag_ohm",
                                      "absolute_error_ohm")])
    t=Table(table,repeatRows=1,colWidths=[55,78,78,78,78,94])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17365d")),
                           ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                           ("GRID",(0,0),(-1,-1),.3,colors.lightgrey),
                           ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.whitesmoke]),
                           ("BOTTOMPADDING",(0,0),(-1,-1),8)]))
    story.append(t)
    if diff is not None:
        story.extend([Spacer(1,14),Paragraph("Historical comparison",styles["Heading2"]),
            Paragraph("Baseline: "+escape(diff["baseline_solver_version"])+
                      " | Candidate: "+escape(diff["candidate_solver_version"]),
                      styles["BodyText"])])
        for change in diff["changes"]:
            story.append(Paragraph(
                f"Mesh {change['segments_per_element']}: "
                f"error change {change['impedance_error_change_ohm']:+.3f} ohm; "
                f"NEC delta {change['nec_impedance_change_ohm']:.3f} ohm",
                styles["BodyText"]))
    story.extend([Spacer(1,14),Paragraph("Provenance digests",styles["Heading2"])])
    for row in current["cases"]:
        story.append(Paragraph(
            f"Mesh {row['segments_per_element']} | deck SHA-256: "
            f"{escape(row['deck_sha256'])}<br/>"
            f"solver output SHA-256: {escape(row['output_sha256'])}",
            styles["BodyText"]))
    story.extend([Spacer(1,14),Paragraph("Limitations",styles["Heading2"])])
    for warning in current.get("caveats",[])[:8]:
        story.append(Paragraph(escape(str(warning)),styles["BodyText"]))
    doc.build(story)
    return buffer.getvalue()
