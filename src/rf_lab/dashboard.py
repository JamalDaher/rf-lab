"""Presentation-only helpers for RF Lab's engineering dashboard."""
from collections import Counter

WORKSPACES = {
    "Projects": ("Project Library",),
    "Design & optimize": ("Antenna Designer","3-Element Yagi","Construction Assistant",
        "Tape-Measure Yagi","Yagi Patterns","Yagi Optimizer","Design Workbench"),
    "Signal analysis": ("Signal Analysis Workbench","SDR Signal Laboratory"),
    "Measure & match": ("SWR Analyzer","Smith Chart","L-Network","NanoVNA S1P",
        "VNA Workbench","Measurement & Tuning Workbench","Antenna Tuning"),
    "RF calculators": ("RF Power","Path Loss","Coax Loss","Transmission Line"),
    "Simulate & validate": ("Radiation Patterns","Thin-Wire MoM","Validation","NEC Comparison"),
}
FEATURED = (
    ("🗂️","Project Library","Organize builds, measurement sweeps and reports.","Projects"),
    ("📐","Design Workbench","Create, compare and export Yagi designs.","Design & optimize"),
    ("📏","Tape-Measure Yagi","Generate practical cut lists and build plans.","Design & optimize"),
    ("📊","Measurement & Tuning Workbench","Compare NanoVNA sweeps and tune conservatively.","Measure & match"),
    ("🧭","Smith Chart","Visualize complex impedance and matching.","Measure & match"),
    ("📡","SDR Signal Laboratory","Explore IQ constellations, digital modulation and waterfalls.","Signal analysis"),
)

def dashboard_metrics(projects,designs,tuning_entries):
    """Summarize session-only state without mutating or persisting anything."""
    return {
        "projects":len(projects),
        "designs":len(designs),
        "measurements":sum(len(p.get("measurements",[])) for p in projects),
        "tuning_records":len(tuning_entries)+sum(len(p.get("tuning_history",[])) for p in projects),
        "available_tools":sum(len(v) for v in WORKSPACES.values()),
    }

def project_previews(projects,limit=4):
    """Most recent project previews for quick access."""
    if not isinstance(limit,int) or limit<0:
        raise ValueError("limit must be a nonnegative integer")
    return [{"id":p["id"],"name":p["name"],"frequency_mhz":p["frequency_mhz"],
             "measurements":len(p.get("measurements",[]))}
            for p in reversed(projects[-limit:])] if limit else []
