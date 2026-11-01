"""RF Lab Streamlit interface."""
import csv
import io
import math
import cmath
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from rf_lab.core import (dipole_length_m, quarter_wave_m, swr, return_loss_db,
                         watts_to_dbm, dbm_to_watts, free_space_path_loss_db)
from rf_lab.yagi import design_yagi, cutting_list
from rf_lab.geometry_view import geometry_figure, dimension_rows
from rf_lab.construction import construction_plan, printable_plan_pdf
from rf_lab.tape_measure import tape_measure_plan, MOUNT_OPTIONS
from rf_lab.yagi_pattern import simulate_yagi, yagi_surface
from rf_lab.mom import solve_yagi_mom
from rf_lab.validation import mesh_sensitivity, short_dipole_directivity_check
from rf_lab.nec_reference import load_reference, compare_reference
from rf_lab.nec2_runner import generate_yagi_nec2
from rf_lab.workbench import (shift_reference_plane, resonance_frequencies_hz, compare_sweeps)
from rf_lab.reporting import create_measurement_pdf
from rf_lab.patterns import (ANTENNA_TYPES, radiation_mesh, elevation_cut,
                             azimuth_cut, pattern_db)
from rf_lab.measurement_workflow import parse_measurement_bytes, measurement_workflow
from rf_lab.dashboard import WORKSPACES, FEATURED, dashboard_metrics, project_previews
from rf_lab.project_library import (new_project, save_library, load_library, add_measurement,
    measurement_sweep, library_zip)
from rf_lab.tuning import (tuning_advice, tuning_comparison, add_history_entry,
                           history_json, load_history)
from rf_lab.measurements import (smith_grid, line_input_gamma, line_input_impedance,
    parse_s1p, swr_from_gamma, return_loss_from_gamma, best_match, comparison_mhz)
from rf_lab.advanced import (smith_coordinates, gamma_from_impedance, coax_loss_db,
                             delivered_power_w, COAX_DB_PER_100FT_100MHZ,
                             l_match_solutions)

st.set_page_config(page_title="RF Lab | RF Engineering Workbench", page_icon="📡", layout="wide", initial_sidebar_state="expanded")
# Consistent visual defaults for existing Plotly figures, without altering their data.
RF_CHART_COLORS = ["#39C6C0", "#7E9BFF", "#F7B267", "#E985B5", "#A8D672", "#B6A4FA"]
pio.templates["rf_lab"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E9F1F8", family="Arial, sans-serif", size=13),
        colorway=RF_CHART_COLORS,
        margin=dict(l=32,r=24,t=44,b=42),
        xaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.14)",
                   zerolinecolor="rgba(148,163,184,.25)", automargin=True),
        yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.14)",
                   zerolinecolor="rgba(148,163,184,.25)", automargin=True),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
)
pio.templates.default = "plotly+rf_lab"

st.markdown("""<style>
:root {--rf-accent:#39C6C0;--rf-border:rgba(148,163,184,.19)}
.block-container {max-width:1240px;padding-top:1.4rem;padding-bottom:4rem}
h1,h2,h3 {letter-spacing:-.035em;line-height:1.25}
h1 {font-weight:750}
[data-testid="stCaptionContainer"] {line-height:1.55}
[data-testid="stSidebar"] {border-right:1px solid var(--rf-border)}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {letter-spacing:-.025em}
[data-testid="stMetric"] {
  background:rgba(148,163,184,.055);
  border:1px solid var(--rf-border);
  border-radius:14px;
  padding:15px 17px;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-radius:16px;
}
.stButton > button, .stDownloadButton > button, .stLinkButton > a {
  border-radius:10px;min-height:2.65rem;transition:filter .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {filter:brightness(1.12)}
[data-testid="stAlert"] {border-radius:12px}
[data-testid="stDataFrame"] {border-radius:12px;overflow:hidden}
[data-testid="stPlotlyChart"] {border:1px solid var(--rf-border);border-radius:14px;padding:6px}
@media(max-width:768px) {
  .block-container {padding:1rem .8rem 3rem}
  h1 {font-size:1.8rem!important}
  h2 {font-size:1.45rem!important}
  h3 {font-size:1.15rem!important}
  [data-testid="stHorizontalBlock"] {flex-wrap:wrap;gap:.7rem}
  [data-testid="column"] {min-width:min(100%,270px)!important;flex:1 1 100%!important}
  [data-testid="stMetric"] {padding:12px}
  [data-testid="stPlotlyChart"] {padding:0}
}
@media(prefers-reduced-motion:reduce) {
  .stButton > button, .stDownloadButton > button {transition:none}
}
/* v3.0.0 professional interface refinements */
:root {--rf-surface:#141F30;--rf-ink:#E9F1F8;--rf-muted:#9BAEC2}
.rf-eyebrow {color:#39C6C0;font-size:.74rem;letter-spacing:.17em;font-weight:700;margin:.6rem 0 .7rem}
.block-container {max-width:1320px;padding-top:1.7rem}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#101D2E 0%,#0B1220 100%)}
[data-testid="stSidebar"] [role="radiogroup"] {gap:.3rem}
[data-testid="stSidebar"] [role="radiogroup"] label {border-radius:9px;padding:.3rem .4rem}
[data-testid="stMetric"] {background:linear-gradient(145deg,rgba(57,198,192,.075),rgba(148,163,184,.035));border-radius:15px}
[data-testid="stMetricValue"] {font-variant-numeric:tabular-nums;letter-spacing:-.04em}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:rgba(148,163,184,.16)}
[data-testid="stPlotlyChart"] {background:rgba(148,163,184,.025)}
.stButton > button[kind="primary"] {background:#39C6C0;color:#0B1220}
button:focus-visible,a:focus-visible,input:focus-visible {outline:2px solid #39C6C0;outline-offset:2px}
@media(max-width:768px) {
  .block-container {padding-top:.75rem}
  [data-testid="stMetric"] {padding:10px}
  [data-testid="stMetricLabel"] {font-size:.8rem}
  [data-testid="stMetricValue"] {font-size:1.45rem}
  .rf-eyebrow {font-size:.65rem;letter-spacing:.1em}
}
</style>""",unsafe_allow_html=True)
st.title("📡 RF Lab")
st.caption("ENGINEERING WORKBENCH  /  v3.0.0")
with st.sidebar:
    st.header("Navigation")
    st.caption("One focused tool at a time.")
    category=st.radio("Workspace",["Home","Projects","Design & optimize","Measure & match","Signal analysis","RF calculators","Simulate & validate"],label_visibility="collapsed",key="rf_category")
    options={name:list(tools) for name,tools in WORKSPACES.items()}
    if category=="Home":
        section="Home"
    else:
        section=st.selectbox("Tool",options[category],key="rf_section_"+category)
    st.divider()
    st.caption("Experimental simulations require independent measurement.")
    st.link_button("GitHub source","https://github.com/JamalDaher/rf-lab")
if section != "Home":
    st.subheader(section)

def open_workspace(category_name, tool_name):
    """Switch both navigation controls before Streamlit instantiates them."""
    st.session_state["rf_category"]=category_name
    st.session_state["rf_section_"+category_name]=tool_name

if section == "Home":
    st.markdown('<div class="rf-eyebrow">RF ENGINEERING PLATFORM · VERSION 2.8.0</div>',
                unsafe_allow_html=True)
    st.markdown("## Your RF engineering workspace")
    st.caption("Design, build, measure and validate antenna systems in one place. "
               "Choose a workflow below to get started.")
    metrics=dashboard_metrics(st.session_state.get("antenna_projects",[]),
                              st.session_state.get("design_library",[]),
                              st.session_state.get("mt_history",[]))
    summary=st.columns(4,gap="small")
    for column,(label,key) in zip(summary,[
        ("Antenna projects","projects"),("Saved designs","designs"),
        ("S1P measurements","measurements"),("Available tools","available_tools")]):
        with column:
            st.metric(label,metrics[key])
    st.markdown("### Quick launch")
    for start in (0,3):
        cols=st.columns(3,gap="medium")
        for col,(symbol,name,description,group) in zip(cols,FEATURED[start:start+3]):
            with col:
                with st.container(border=True):
                    st.markdown(f"#### {symbol} {name}")
                    st.caption(description)
                    st.button("Open workspace",key="home_"+name,
                              use_container_width=True,
                              on_click=open_workspace,args=(group,name))
    st.markdown("### Recent projects")
    previews=project_previews(st.session_state.get("antenna_projects",[]))
    if previews:
        for project in previews:
            with st.container(border=True):
                left,right=st.columns([3,1])
                with left:
                    st.markdown(f"**{project['name']}**")
                    st.caption(f"{project['frequency_mhz']:g} MHz · "
                               f"{project['measurements']} saved measurements")
                with right:
                    st.button("Open project",key="home_project_"+project["id"],
                              use_container_width=True,
                              on_click=open_workspace,args=("Projects","Project Library"))
    else:
        with st.container(border=True):
            st.markdown("**Start your first antenna project**")
            st.caption("Keep dimensions, build steps, NanoVNA measurements and reports together.")
            st.button("Create a project",key="home_new_project",
                      on_click=open_workspace,args=("Projects","Project Library"))
    with st.expander("Engineering model limitations",expanded=False):
        st.info("Heuristic antenna dimensions and experimental EFIE simulations "
                "are not validated performance guarantees. Check independent NEC "
                "results and calibrated measurements before transmitting.")
    st.caption("Session data is temporary. Export JSON/ZIP backups from Project Library.")

if section == "SDR Signal Laboratory":
    from rf_lab.sdr_ui import render as render_sdr
    render_sdr()

if section == "Signal Analysis Workbench":
    from rf_lab.signal_ui import render
    render()

if section == "Antenna Designer":
    f = st.number_input("Frequency (MHz)", min_value=0.001, value=146.0)
    k = st.slider("Length correction factor", 0.80, 1.00, 0.95)
    st.metric("Half-wave dipole length", f"{dipole_length_m(f,k):.3f} m")
    st.metric("Each arm / quarter-wave vertical", f"{quarter_wave_m(f,k):.3f} m")
    st.info("Approximate starting dimensions; verify resonance with measurements.")
if section == "3-Element Yagi":
    band = st.selectbox("Frequency preset", ["2 m (146 MHz)", "70 cm (435 MHz)", "Custom"])
    default = {"2 m (146 MHz)": 146.0, "70 cm (435 MHz)": 435.0}.get(band, 146.0)
    yf = st.number_input("Yagi frequency (MHz)", min_value=0.001, value=default, key=f"yagi_frequency_{band}")
    gap = st.number_input("Driven-element feed gap (mm)", min_value=0.1, value=12.0)
    try:
        design = design_yagi(yf, gap)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.metric("Reflector-to-director spacing", f"{design.boom_length_m*100:.1f} cm")
        view_col, unit_col = st.columns(2)
        with view_col:
            drawing_view = st.radio("Engineering view", ["3D", "Top view"], horizontal=True,
                                    key="yagi_drawing_view")
        with unit_col:
            drawing_unit = st.selectbox("Drawing units", ["cm", "in", "mm"],
                                        key="yagi_drawing_units")
        fig = geometry_figure(design, view=drawing_view or "3D", unit=drawing_unit)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Interactive dimensional model (not an EM simulation). "
                   "Drag to rotate the 3D view; zoom or hover to inspect the elements.")
        st.markdown("**Dimension schedule**")
        st.dataframe(dimension_rows(design, drawing_unit),
                     use_container_width=True, hide_index=True)
        st.metric("Driven feed gap", f"{design.feed_gap_m * {'cm': 100, 'in': 39.37007874015748, 'mm': 1000}[drawing_unit]:.2f} {drawing_unit}")
        rows = cutting_list(design)
        display = [{"Part": r["part"], "Qty": r["quantity"],
                    "Each length (cm)": round(r["length_m"]*100,2),
                    "Each length (in)": round(r["length_in"],2)} for r in rows]
        st.subheader("Cutting list")
        st.dataframe(display, use_container_width=True, hide_index=True)
        st.caption("Positions from reflector center: " + ", ".join(
            f"{e.name}: {e.position_m*100:.1f} cm" for e in design.elements))
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(display[0]))
        writer.writeheader()
        writer.writerows(display)
        st.download_button("Download cutting list (CSV)", output.getvalue(),
                           file_name=f"yagi_{yf:g}MHz_cutting_list.csv", mime="text/csv")
        st.warning("Heuristic starting dimensions, not a validated tape-measure build. "
                   "Element width, mounting and feed matching affect resonance and SWR. "
                   "Tune with an antenna analyzer; keep clear of overhead power lines.")
if section == "Construction Assistant":
    st.caption("Build planning for the heuristic three-element Yagi. Verify dimensions, "
               "electrical matching and mechanical design before construction.")
    left, right = st.columns(2)
    with left:
        build_frequency = st.number_input("Build frequency (MHz)", min_value=0.001,
                                          value=146.0, key="build_frequency")
        build_gap = st.number_input("Driven feed gap (mm)", min_value=0.1,
                                    value=12.0, key="build_gap")
    with right:
        build_allowance = st.number_input("Extra trim length per physical piece (mm)",
                                          min_value=0.0, max_value=100.0, value=10.0,
                                          step=1.0, key="build_allowance")
        build_unit = st.selectbox("Shop drawing units", ["cm", "in", "mm"],
                                  key="build_unit")
    try:
        build_design = design_yagi(build_frequency, build_gap)
        plan = construction_plan(build_design, build_allowance)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.plotly_chart(geometry_figure(build_design, "Top view", build_unit),
                        use_container_width=True)
        st.markdown("#### Cut schedule")
        factor = {"cm":100.0, "in":39.37007874015748, "mm":1000.0}[build_unit]
        st.dataframe([{
            "Part": item["part"], "Qty": item["quantity"],
            f"Nominal ({build_unit})": round(item["nominal_m"]*factor,2),
            f"Initial cut ({build_unit})": round(item["initial_cut_m"]*factor,2),
        } for item in plan["cuts"]], use_container_width=True, hide_index=True)
        st.caption("Initial cuts include the selected extra trim length per piece. "
                   "Final dimensions must be measured after tuning.")
        st.markdown("#### Materials to source")
        st.dataframe([{"Material": name, "Qty": qty, "Specification": note}
                      for name, qty, note in plan["materials"]],
                     use_container_width=True, hide_index=True)
        with st.expander("Step-by-step assembly and tuning", expanded=True):
            for number, step in enumerate(plan["steps"],1):
                st.checkbox(f"{number}. {step}", key=f"build_step_{number}")
        pdf = printable_plan_pdf(plan, build_unit)
        st.download_button("Download printable construction packet (PDF)", pdf,
                           file_name=f"rf_lab_yagi_build_{build_frequency:g}MHz.pdf",
                           mime="application/pdf", use_container_width=True)
        st.warning("Starting geometry only. Use a calibrated antenna analyzer and "
                   "appropriate mounting, feed isolation and matching. "
                   "Stay well clear of power lines; verify structural and RF safety.")

if section == "Tape-Measure Yagi":
    st.caption("Portable three-element steel tape-measure Yagi construction planner. "
               "Starting dimensions are heuristic and must be tuned on the finished assembly.")
    left, right = st.columns(2)
    with left:
        tape_freq = st.number_input("Target frequency (MHz)", min_value=0.001,
                                    value=146.0, key="tape_freq")
        tape_gap = st.number_input("Driven feed gap (mm)", min_value=0.1,
                                   value=12.0, key="tape_gap")
        tape_width = st.number_input("Tape blade width (mm)", min_value=5.0,
                                     max_value=100.0, value=25.0, key="tape_width")
    with right:
        tape_margin = st.number_input("PVC boom end margin, each end (mm)",
                                      min_value=0.0, max_value=500.0,
                                      value=50.0, key="tape_margin")
        tape_trim = st.number_input("Extra trim per blade piece (mm)",
                                    min_value=0.0, max_value=100.0,
                                    value=10.0, key="tape_trim")
        tape_mount = st.selectbox("Mounting option", list(MOUNT_OPTIONS),
                                  key="tape_mount")
        tape_unit = st.selectbox("Dimensions", ["cm","in","mm"], key="tape_unit")
    try:
        tape_design, tape_plan = tape_measure_plan(
            tape_freq, tape_gap, tape_trim, tape_margin, tape_width, tape_mount)
    except ValueError as exc:
        st.error(str(exc))
    else:
        scale = {"cm":100.0,"in":39.37007874015748,"mm":1000.0}[tape_unit]
        st.plotly_chart(geometry_figure(tape_design, "Top view", tape_unit),
                        use_container_width=True)
        st.caption("Drawing origin is the reflector centerline. "
                   "Physical boom-end mounting marks appear below.")
        a, b = st.columns(2)
        a.metric("Minimum PVC boom stock", f"{tape_plan['boom_stock_m']*scale:.2f} {tape_unit}")
        b.metric("Tape needed before cutting waste", f"{tape_plan['total_tape_m']*scale:.2f} {tape_unit}")
        st.markdown("#### Tape-blade cutting schedule")
        st.dataframe([{
            "Part": cut["part"], "Pieces":cut["quantity"],
            f"Nominal ({tape_unit})":round(cut["nominal_m"]*scale,2),
            f"Initial cut ({tape_unit})":round(cut["initial_cut_m"]*scale,2),
        } for cut in tape_plan["cuts"]],use_container_width=True,hide_index=True)
        st.markdown("#### Mark positions from physical PVC boom end")
        st.dataframe([{"Element":name, f"Position ({tape_unit})":round(position*scale,2)}
                      for name,position in tape_plan["positions_from_boom_end"]],
                     use_container_width=True,hide_index=True)
        st.markdown("#### Hardware and materials")
        st.dataframe([{"Item":name,"Qty":qty,"Notes":note}
                      for name,qty,note in tape_plan["materials"]],
                     use_container_width=True,hide_index=True)
        with st.expander("Field assembly and tuning checklist",expanded=True):
            for index, step in enumerate(tape_plan["steps"],1):
                st.checkbox(f"{index}. {step}",key=f"tape_step_{index}")
        packet = printable_plan_pdf(tape_plan,tape_unit)
        st.download_button("Download tape-measure Yagi build packet (PDF)",packet,
                           file_name=f"rf_lab_tape_yagi_{tape_freq:g}MHz.pdf",
                           mime="application/pdf",use_container_width=True)
        st.warning("Steel tape is sharp and springy; wear gloves and eye protection. "
                   "Secure all blades and stay clear of overhead power lines. "
                   "Tape width and mounting hardware affect resonance; use an analyzer "
                   "to verify matching before transmitting.")

if section == "SWR Analyzer":
    r = st.number_input("Resistance (Ω)", min_value=0.0, value=75.0)
    x = st.number_input("Reactance (Ω)", value=0.0)
    z0 = st.number_input("Reference impedance (Ω)", min_value=0.1, value=50.0)
    z = complex(r, x)
    value = swr(z, z0)
    st.metric("SWR", f"{value:.3f}" if math.isfinite(value) else "∞")
    st.metric("Return loss", f"{return_loss_db(z,z0):.2f} dB")
    resistances = np.linspace(1, 200, 200)
    fig = go.Figure(go.Scatter(x=resistances, y=[swr(complex(v,x),z0) for v in resistances]))
    fig.update_layout(xaxis_title="Resistance (Ω)", yaxis_title="SWR")
    st.plotly_chart(fig, use_container_width=True)
if section == "RF Power":
    w = st.number_input("Transmit power (W)", min_value=0.000001, value=5.0)
    st.metric("dBm", f"{watts_to_dbm(w):.2f}")
    st.metric("dBW", f"{watts_to_dbm(w)-30:.2f}")
    st.caption(f"Reverse conversion: {dbm_to_watts(watts_to_dbm(w)):.6g} W")
if section == "Path Loss":
    frequency = st.number_input("Carrier frequency (MHz)", min_value=0.001, value=146.0)
    distance = st.number_input("Distance (km)", min_value=0.001, value=10.0)
    st.metric("Free-space path loss", f"{free_space_path_loss_db(frequency,distance):.2f} dB")
    distances = np.linspace(0.1, max(1, distance*2), 200)
    fig = go.Figure(go.Scatter(x=distances, y=[free_space_path_loss_db(frequency,d) for d in distances]))
    fig.update_layout(xaxis_title="Distance (km)", yaxis_title="Path loss (dB)")
    st.plotly_chart(fig, use_container_width=True)
    st.info("Ideal unobstructed free space only; terrain and foliage are not modeled.")

if section == "Smith Chart":
    st.subheader("Impedance Smith chart")
    sr = st.number_input("Load resistance (Ω)", min_value=0.0, value=75.0, key="smith_r")
    sx = st.number_input("Load reactance (Ω)", value=25.0, key="smith_x")
    sz0 = st.number_input("Reference impedance (Ω)", min_value=0.1, value=50.0, key="smith_z0")
    gx, gy = smith_coordinates(complex(sr, sx), sz0)
    st.metric("Reflection coefficient magnitude", f"{abs(complex(gx,gy)):.4f}")
    theta = np.linspace(0, 2*np.pi, 361)
    chart = go.Figure()
    chart.add_trace(go.Scatter(x=np.cos(theta), y=np.sin(theta),
                               mode="lines", name="|Γ| = 1", line=dict(color="gray")))
    # Complete impedance grid: constant-resistance circles and reactance arcs.
    for label, points in smith_grid():
        chart.add_trace(go.Scatter(x=[p.real for p in points], y=[p.imag for p in points],
                                   mode="lines", line=dict(color="lightgray", width=1),
                                   name=label, showlegend=False))
    chart.add_trace(go.Scatter(x=[gx], y=[gy], mode="markers+text",
                               text=[f"Z={sr:g}{sx:+g}j Ω"], textposition="top center",
                               marker=dict(size=12, color="crimson"), name="Load"))
    chart.update_layout(xaxis=dict(range=[-1.12,1.12], scaleanchor="y", zeroline=True),
                        yaxis=dict(range=[-1.12,1.12], zeroline=True),
                        title="Reflection-coefficient plane", height=520)
    st.plotly_chart(chart, use_container_width=True)
    st.caption("Normalized constant-resistance circles and constant-reactance arcs.")
if section == "Coax Loss":
    st.subheader("Approximate coaxial cable attenuation")
    cable = st.selectbox("Cable type", list(COAX_DB_PER_100FT_100MHZ))
    cf = st.number_input("Coax frequency (MHz)", min_value=0.001, value=146.0)
    length = st.number_input("Cable length (ft)", min_value=0.0, value=50.0)
    input_w = st.number_input("Input power (W)", min_value=0.001, value=10.0)
    loss = coax_loss_db(cable, cf, length)
    st.metric("Estimated matched-line loss", f"{loss:.2f} dB")
    st.metric("Estimated output power", f"{delivered_power_w(input_w,loss):.2f} W")
    st.info("Illustrative cable figures and sqrt(f) scaling. Excludes connectors, "
            "mismatch, temperature and datasheet-specific performance.")
if section == "L-Network":
    st.subheader("Ideal resistive L-network matching")
    source = st.number_input("Source resistance (Ω)", min_value=0.001, value=50.0)
    load = st.number_input("Load resistance (Ω)", min_value=0.001, value=200.0)
    mf = st.number_input("Match frequency (MHz)", min_value=0.001, value=146.0)
    solutions = l_match_solutions(source, load, mf)
    if not solutions:
        st.success("Already matched: no L-network required.")
    else:
        for index, solution in enumerate(solutions, 1):
            with st.container(border=True):
                st.markdown(f"**Solution {index}: {solution.topology}**")
                st.write(f"Series: {solution.series_component} = {solution.series_value * (1e9 if solution.series_component.startswith('Inductor') else 1e12):.3f} {'nH' if solution.series_component.startswith('Inductor') else 'pF'}")
                st.write(f"Shunt: {solution.shunt_component} = {solution.shunt_value * (1e9 if solution.shunt_component.startswith('Inductor') else 1e12):.3f} {'nH' if solution.shunt_component.startswith('Inductor') else 'pF'}")
    st.warning("Ideal lossless components, positive real resistances only. "
               "Verify component parasitics, bandwidth, power handling and actual matching with a VNA.")

if section == "Transmission Line":
    st.subheader("Transmission-line impedance transformation")
    lr = st.number_input("Line load resistance (Ω)", min_value=0.0, value=100.0)
    lx = st.number_input("Line load reactance (Ω)", value=0.0)
    lf = st.number_input("Line frequency (MHz)", min_value=0.001, value=146.0)
    ll = st.number_input("Line length (m)", min_value=0.0, value=1.0)
    lvf = st.slider("Velocity factor", min_value=0.10, max_value=1.0, value=0.66)
    lloss = st.number_input("Matched-line loss (dB / 100 m)", min_value=0.0, value=0.0)
    lz0 = st.number_input("Line characteristic impedance (Ω)", min_value=0.1, value=50.0)
    load_z = complex(lr, lx)
    try:
        gin = line_input_gamma(load_z, lf, ll, lvf, lloss, lz0)
        zin = line_input_impedance(load_z, lf, ll, lvf, lloss, lz0)
        st.metric("Input impedance", f"{zin.real:.2f} {zin.imag:+.2f}j Ω")
        st.metric("Input |Γ|", f"{abs(gin):.4f}")
    except ValueError as exc:
        st.error(str(exc))
    lengths = np.linspace(0, ll, 150)
    trajectory = [line_input_gamma(load_z, lf, float(v), lvf, lloss, lz0) for v in lengths]
    fig = go.Figure()
    for label, pts in smith_grid():
        fig.add_trace(go.Scatter(x=[p.real for p in pts], y=[p.imag for p in pts],
                                 mode="lines", line=dict(color="lightgray", width=1),
                                 showlegend=False, name=label))
    fig.add_trace(go.Scatter(x=[p.real for p in trajectory], y=[p.imag for p in trajectory],
                             mode="lines+markers", name="Line transformation",
                             marker=dict(size=3)))
    fig.update_layout(xaxis=dict(range=[-1.1,1.1], scaleanchor="y"),
                      yaxis=dict(range=[-1.1,1.1]), height=500,
                      title="Source-facing reflection coefficient vs line length")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Ideal uniform line with constant velocity factor and specified matched-line loss.")
if section == "Project Library":
    st.caption("Antenna projects with designs, construction checks, measurements and tuning records. "
               "Stored in this browser session only; export a backup to retain them.")
    if "antenna_projects" not in st.session_state:
        st.session_state.antenna_projects=[]
    projects=st.session_state.antenna_projects
    with st.expander("Create a project",expanded=not bool(projects)):
        with st.form("project_create"):
            pn=st.text_input("Project name",value="2 m tape-measure Yagi")
            pf=st.number_input("Target frequency (MHz)",min_value=0.001,value=146.0)
            pnotes=st.text_area("Project notes",max_chars=2000)
            create=st.form_submit_button("Create project")
        if create:
            try:
                if len(projects)>=50:
                    raise ValueError("Project limit of 50 reached")
                projects.append(new_project(pn,pf,pnotes))
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    with st.expander("Import or export library",expanded=False):
        backup=st.file_uploader("Import RF Lab project library (JSON)",type=["json"],
                                key="project_import")
        if backup is not None and st.button("Import and merge by project ID",key="project_merge"):
            try:
                incoming=load_library(backup.getvalue())
                merged={p["id"]:p for p in projects}
                merged.update({p["id"]:p for p in incoming})
                save_library(list(merged.values()))
                st.session_state.antenna_projects=list(merged.values())
                st.success("Projects imported. Matching IDs were replaced by imported versions.")
                st.rerun()
            except (ValueError,UnicodeDecodeError,TypeError) as exc:
                st.error(str(exc))
        if projects:
            st.download_button("Download all projects (JSON)",save_library(projects),
                               file_name="rf-lab-projects.json",mime="application/json")
            st.download_button("Download project backup (ZIP)",library_zip(projects),
                               file_name="rf-lab-projects.zip",mime="application/zip")
    if projects:
        st.metric("Antenna projects",len(projects))
        st.dataframe([{"Project":p["name"],"Frequency (MHz)":p["frequency_mhz"],
                       "Measurements":len(p["measurements"]),
                       "Tuning entries":len(p["tuning_history"]),
                       "Design saved":p["design"] is not None}
                      for p in projects],hide_index=True,use_container_width=True)
        ids={p["id"]:p for p in projects}
        chosen=st.selectbox("Open project",list(ids),
                            format_func=lambda k:ids[k]["name"],key="project_selected")
        project=ids[chosen]
        idx=next(i for i,p in enumerate(projects) if p["id"]==chosen)
        with st.container(border=True):
            st.markdown("#### Project details")
            project["notes"]=st.text_area("Notes",value=project["notes"],
                                          key="project_notes_"+chosen,max_chars=2000)
            st.caption(f"Target: {project['frequency_mhz']:g} MHz · "
                       f"Created: {project['created_at'][:10]}")
            st.markdown("#### Antenna design")
            saved=st.session_state.get("design_library",[])
            if saved:
                choice=st.selectbox("Attach an existing Design Workbench design",
                                    range(len(saved)),format_func=lambda i:saved[i]["name"],
                                    key="project_design_select")
                if st.button("Attach selected design",key="project_attach"):
                    project["design"]=saved[choice]
                    st.success("Design attached to project.")
            else:
                st.caption("Save a design in Design Workbench first, then attach it here.")
            if project["design"] is not None:
                st.json(project["design"],expanded=False)
            st.markdown("#### Construction checklist")
            build_steps=[
                "Verify antenna dimensions and feed arrangement",
                "Prepare boom and mark element positions",
                "Cut, deburr and secure elements",
                "Install insulated feedpoint and strain relief",
                "Inspect mechanical and electrical connections",
                "Measure and document final resonance and SWR",
            ]
            checks=project["construction_checks"]
            if len(checks)!=len(build_steps):
                checks=[False]*len(build_steps)
            project["construction_checks"]=[
                st.checkbox(step,value=checks[i],key=f"project_check_{chosen}_{i}")
                for i,step in enumerate(build_steps)]
            st.markdown("#### NanoVNA measurements")
            uploaded=st.file_uploader("Attach a calibrated .s1p measurement",
                                      type=["s1p"],key="project_s1p_"+chosen)
            if uploaded is not None and st.button("Add measurement",key="project_add_s1p"):
                try:
                    sweep=parse_measurement_bytes(uploaded.getvalue())
                    projects[idx]=add_measurement(project,uploaded.name,sweep)
                    st.success("Measurement attached.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            if project["measurements"]:
                from rf_lab.measurement_workflow import measurement_snapshot
                rows=[]
                plot=go.Figure()
                for measurement in project["measurements"]:
                    sweep=measurement_sweep(measurement)
                    snapshot=measurement_snapshot(sweep,project["frequency_mhz"])
                    rows.append({"Sweep":measurement["name"],
                                 "Best match (MHz)":snapshot["best_match_mhz"],
                                 "Minimum SWR":snapshot["minimum_swr"],
                                 "Resonance (MHz)":snapshot["resonance_mhz"]})
                    plot.add_trace(go.Scatter(x=[f/1e6 for f in sweep.frequencies_hz],
                        y=[v if math.isfinite(v) else None for v in
                           (swr_from_gamma(g) for g in sweep.gamma)],
                        name=measurement["name"]))
                st.dataframe(rows,hide_index=True,use_container_width=True)
                plot.update_layout(xaxis_title="Frequency (MHz)",yaxis_title="SWR")
                st.plotly_chart(plot,use_container_width=True)
                st.download_button("Download project measurement PDF",
                    create_measurement_pdf({
                        f"{i+1} {m['name'][:35]}":measurement_sweep(m)
                        for i,m in enumerate(project["measurements"])},
                        project["frequency_mhz"],project["notes"]),
                    file_name="rf-lab-project-measurements.pdf",mime="application/pdf")
            st.markdown("#### Tuning history")
            history=st.session_state.get("mt_history",[])
            if history and st.button("Copy tuning workbench history into project",
                                     key="project_tuning_copy"):
                project["tuning_history"]=load_history(history_json(history))
                st.success("Tuning history attached.")
            if project["tuning_history"]:
                st.dataframe(project["tuning_history"],hide_index=True,use_container_width=True)
            st.caption("Export JSON or ZIP after editing. Browser session data is not permanent.")

if section == "NanoVNA S1P":
    st.subheader("NanoVNA Touchstone S1P import")
    upload = st.file_uploader("Upload .s1p measurement", type=["s1p"])
    design_frequency = st.number_input("Comparison design frequency (MHz)",
                                       min_value=0.001, value=146.0)
    if upload is not None:
        try:
            measurement = parse_s1p(upload.getvalue().decode("utf-8-sig"))
        except (UnicodeDecodeError, ValueError) as exc:
            st.error(f"Could not parse S1P: {exc}")
        else:
            mhz = np.array(measurement.frequencies_hz)/1e6
            swrs = [swr_from_gamma(g) for g in measurement.gamma]
            losses = [return_loss_from_gamma(g) for g in measurement.gamma]
            st.caption(f"{len(mhz)} points · Reference impedance {measurement.reference_ohm:g} Ω")
            try:
                measured_mhz, delta_mhz = comparison_mhz(measurement, design_frequency)
                st.metric("Minimum-SWR frequency", f"{measured_mhz:.4f} MHz",
                          delta=f"{delta_mhz:+.4f} MHz vs design")
                st.metric("Minimum SWR", f"{best_match(measurement)[1]:.3f}")
            except ValueError as exc:
                st.warning(str(exc))
            sweep = go.Figure()
            sweep.add_trace(go.Scatter(x=mhz, y=[v if math.isfinite(v) else None for v in swrs],
                                       name="SWR"))
            sweep.update_layout(title="Measured SWR", xaxis_title="Frequency (MHz)",
                                yaxis_title="SWR")
            st.plotly_chart(sweep, use_container_width=True)
            lossfig = go.Figure(go.Scatter(x=mhz,
                y=[v if math.isfinite(v) else None for v in losses], name="Return loss"))
            lossfig.update_layout(title="Measured return loss", xaxis_title="Frequency (MHz)",
                                  yaxis_title="Return loss (dB)")
            st.plotly_chart(lossfig, use_container_width=True)
            sm = go.Figure()
            for label, pts in smith_grid():
                sm.add_trace(go.Scatter(x=[p.real for p in pts], y=[p.imag for p in pts],
                                        mode="lines", line=dict(color="lightgray", width=1),
                                        showlegend=False, name=label))
            sm.add_trace(go.Scatter(x=[g.real for g in measurement.gamma],
                                    y=[g.imag for g in measurement.gamma],
                                    mode="lines+markers", marker=dict(size=3),
                                    name="Measured S11"))
            sm.update_layout(title="Measured S11 Smith chart",
                             xaxis=dict(range=[-1.1,1.1], scaleanchor="y"),
                             yaxis=dict(range=[-1.1,1.1]), height=500)
            st.plotly_chart(sm, use_container_width=True)
            st.info("Minimum SWR is a best-match frequency, not necessarily zero-reactance resonance. "
                    "Measurement accuracy depends on calibration and fixture setup.")

if section == "VNA Workbench":
    st.subheader("NanoVNA measurement workbench")
    files = st.file_uploader("Upload up to five S1P sweeps", type=["s1p"],
                             accept_multiple_files=True, key="workbench_files")
    design_mhz = st.number_input("Target design frequency (MHz)", min_value=0.001,
                                  value=146.0, key="workbench_design")
    st.markdown("**Reference-plane correction**")
    shift_m = st.number_input("Shift toward antenna/DUT (m)", value=0.0,
                               help="Positive removes cable phase; negative shifts away.")
    shift_vf = st.slider("Cable velocity factor", 0.1, 1.0, 0.66, key="workbench_vf")
    shift_loss = st.number_input("Cable loss (dB / 100 m)", min_value=0.0,
                                 value=0.0, key="workbench_loss")
    notes = st.text_area("Report notes", placeholder="Antenna, calibration, cable, and tuning changes")
    if files:
        if len(files) > 5:
            st.error("Please upload no more than five sweeps.")
        else:
            sweeps = {}
            for index, uploaded in enumerate(files, 1):
                label = f"{index}: {uploaded.name}"
                try:
                    raw = parse_s1p(uploaded.getvalue().decode("utf-8-sig"))
                    corrected = shift_reference_plane(raw, shift_m, shift_vf, shift_loss)
                    sweeps[label] = corrected
                except (UnicodeDecodeError, ValueError) as exc:
                    st.error(f"{uploaded.name}: {exc}")
            if sweeps:
                refs = {s.reference_ohm for s in sweeps.values()}
                if len(refs) > 1:
                    st.warning("Files have different reference impedances. Direct SWR "
                               "comparison requires a common reference impedance.")
                summaries = compare_sweeps(sweeps)
                rows = []
                for summary in summaries:
                    rows.append({
                        "Sweep": summary.name,
                        "Points": summary.points,
                        "Minimum SWR": round(summary.minimum_swr, 3)
                                       if summary.minimum_swr is not None else None,
                        "Best match (MHz)": round(summary.best_match_mhz, 4)
                                            if summary.best_match_mhz is not None else None,
                        "Reactance-zero crossings (MHz)":
                            ", ".join(f"{v:.4f}" for v in summary.resonances_mhz) or "None found",
                    })
                st.dataframe(rows, hide_index=True, use_container_width=True)
                swr_fig = go.Figure()
                rl_fig = go.Figure()
                smith_fig = go.Figure()
                for label, pts in smith_grid():
                    smith_fig.add_trace(go.Scatter(
                        x=[p.real for p in pts], y=[p.imag for p in pts],
                        mode="lines", line=dict(color="lightgray", width=1),
                        showlegend=False, name=label))
                for name, sweep in sweeps.items():
                    frequencies = [f/1e6 for f in sweep.frequencies_hz]
                    swr_fig.add_trace(go.Scatter(
                        x=frequencies,
                        y=[v if math.isfinite(v) else None
                           for v in (swr_from_gamma(g) for g in sweep.gamma)],
                        name=name))
                    rl_fig.add_trace(go.Scatter(
                        x=frequencies,
                        y=[v if math.isfinite(v) else None
                           for v in (return_loss_from_gamma(g) for g in sweep.gamma)],
                        name=name))
                    smith_fig.add_trace(go.Scatter(
                        x=[g.real for g in sweep.gamma],
                        y=[g.imag for g in sweep.gamma],
                        mode="lines", name=name))
                swr_fig.update_layout(title="SWR comparison",
                                      xaxis_title="Frequency (MHz)", yaxis_title="SWR")
                rl_fig.update_layout(title="Return loss comparison",
                                     xaxis_title="Frequency (MHz)", yaxis_title="Return loss (dB)")
                smith_fig.update_layout(title="S11 comparison",
                    xaxis=dict(range=[-1.1, 1.1], scaleanchor="y"),
                    yaxis=dict(range=[-1.1, 1.1]), height=500)
                st.plotly_chart(swr_fig, use_container_width=True)
                st.plotly_chart(rl_fig, use_container_width=True)
                st.plotly_chart(smith_fig, use_container_width=True)
                try:
                    pdf = create_measurement_pdf(sweeps, design_mhz, notes)
                    st.download_button("Download measurement report (PDF)", pdf,
                        file_name="rf_lab_measurement_report.pdf", mime="application/pdf")
                except ValueError as exc:
                    st.error(f"Could not create PDF report: {exc}")
                st.info("Zero-reactance crossings are interpolated between samples. "
                        "Reference-plane correction is not a replacement for VNA calibration.")

if section == "Measurement & Tuning Workbench":
    st.caption("A guided workflow from calibrated NanoVNA sweeps to conservative "
               "tuning advice, before/after comparison, session history and a PDF report.")
    with st.container(border=True):
        st.markdown("#### 1 · Configure your antenna")
        c1,c2,c3=st.columns(3)
        with c1:
            mt_target=st.number_input("Target frequency (MHz)",min_value=0.001,
                                       value=146.0,key="mt_target")
        with c2:
            mt_length=st.number_input("Adjustable element length (mm)",min_value=0.1,
                                       value=1000.0,key="mt_length")
        with c3:
            mt_tolerance=st.number_input("Frequency tolerance (MHz)",min_value=0.0,
                                          value=0.05,step=0.01,key="mt_tolerance")
        mt_name=st.text_input("Antenna / session name",value="Portable Yagi",key="mt_name")
    with st.container(border=True):
        st.markdown("#### 2 · Import NanoVNA measurements")
        c1,c2=st.columns(2)
        with c1:
            mt_before=st.file_uploader("Before tuning (.s1p)",type=["s1p"],
                                        key="mt_before")
        with c2:
            mt_after=st.file_uploader("After tuning (.s1p), optional",type=["s1p"],
                                       key="mt_after")
        st.caption("Calibrate at the same reference plane for both sweeps. "
                   "Touchstone v1 S11 data in RI, MA or DB format is supported.")
    if "mt_history" not in st.session_state:
        st.session_state.mt_history=[]
    mt_notes=st.text_area("Build notes and changes made",key="mt_notes",
                           placeholder="Element material, mount, calibration plane, measured trim...")
    if mt_before is not None:
        try:
            mt_b=parse_measurement_bytes(mt_before.getvalue())
            mt_a=parse_measurement_bytes(mt_after.getvalue()) if mt_after is not None else None
            mt_result=measurement_workflow(mt_b,mt_target,mt_length,mt_a,mt_tolerance)
        except ValueError as exc:
            st.error(f"Measurement workflow: {exc}")
        else:
            st.markdown("#### 3 · Inspect measurements")
            snap=mt_result["before"]
            c1,c2,c3=st.columns(3)
            c1.metric("Best match (minimum SWR)",
                      f"{snap['best_match_mhz']:.4f} MHz" if snap["best_match_mhz"] is not None else "N/A")
            c2.metric("Minimum SWR",
                      f"{snap['minimum_swr']:.3f}" if snap["minimum_swr"] is not None else "N/A")
            c3.metric("Reactance-zero resonance",
                      f"{snap['resonance_mhz']:.4f} MHz" if snap["resonance_mhz"] is not None else "Not detected")
            if not snap["target_covered"]:
                st.warning("Target frequency is outside the measured sweep range.")
            if mt_result["after"] is not None:
                st.markdown("**Before / after summary**")
                st.dataframe([{"Stage":label,
                    "Best match (MHz)":s["best_match_mhz"],
                    "Minimum SWR":s["minimum_swr"],
                    "Reactance-zero (MHz)":s["resonance_mhz"]}
                    for label,s in (("Before",snap),("After",mt_result["after"]))],
                    use_container_width=True,hide_index=True)
                st.dataframe([mt_result["comparison"]],hide_index=True,
                             use_container_width=True)
            swr_chart=go.Figure()
            for label,sweep in (("Before",mt_b),("After",mt_a)):
                if sweep is None:
                    continue
                swr_chart.add_trace(go.Scatter(
                    x=[freq/1e6 for freq in sweep.frequencies_hz],
                    y=[value if math.isfinite(value) else None for value in
                       (swr_from_gamma(g) for g in sweep.gamma)],
                    name=label,mode="lines"))
            swr_chart.add_vline(x=mt_target,line_dash="dash",
                                annotation_text="Target")
            swr_chart.update_layout(title="Measured SWR comparison",
                                     xaxis_title="Frequency (MHz)",yaxis_title="SWR")
            st.plotly_chart(swr_chart,use_container_width=True)
            st.markdown("#### 4 · Tuning recommendation")
            guidance=mt_result["advice"]
            st.markdown(f"**Suggested direction: {guidance.direction}**")
            if guidance.estimated_change_mm is not None:
                st.metric("First-order length change",
                          f"{guidance.estimated_change_mm:+.2f} mm")
            st.info(guidance.message)
            st.caption("The estimate applies to a single adjustable resonant element. "
                       "Yagi coupling, feed matching and tape-blade width may change the result.")
            st.markdown("#### 5 · Save and print")
            if st.button("Save result to session history",key="mt_save"):
                try:
                    st.session_state.mt_history=add_history_entry(
                        st.session_state.mt_history,mt_name,guidance,mt_length,mt_notes)
                    st.success("Saved to this browser session; export JSON for persistence.")
                except ValueError as exc:
                    st.error(str(exc))
            report_sweeps={"Before":mt_b}
            if mt_a is not None:
                report_sweeps["After"]=mt_a
            report_notes=(f"Antenna: {mt_name}. Adjustable length: {mt_length:g} mm. "
                          f"Tuning guidance: {guidance.direction}; "
                          f"estimated change: {guidance.estimated_change_mm} mm. "
                          f"Notes: {mt_notes}")
            try:
                mt_pdf=create_measurement_pdf(report_sweeps,mt_target,report_notes)
                st.download_button("Download measurement and tuning PDF",mt_pdf,
                    file_name="rf_lab_tuning_report.pdf",mime="application/pdf",
                    key="mt_pdf",use_container_width=True)
            except ValueError as exc:
                st.error(str(exc))
    with st.expander("Tuning session history · import/export",expanded=False):
        mt_import=st.file_uploader("Import saved history (JSON)",type=["json"],
                                    key="mt_import")
        if mt_import is not None and st.button("Import history",key="mt_import_btn"):
            try:
                st.session_state.mt_history=load_history(
                    mt_import.getvalue().decode("utf-8-sig"))
                st.success("Imported session history.")
            except (ValueError,UnicodeDecodeError) as exc:
                st.error(str(exc))
        if st.session_state.mt_history:
            st.dataframe(st.session_state.mt_history,use_container_width=True,
                         hide_index=True)
            st.download_button("Export history (JSON)",
                               history_json(st.session_state.mt_history),
                               file_name="rf_lab_tuning_history.json",
                               mime="application/json",key="mt_export")
            if st.button("Clear history",key="mt_clear"):
                st.session_state.mt_history=[]
                st.rerun()
    st.warning("A minimum-SWR point is not necessarily resonance. "
               "Length estimates are first-order only: make small changes and remeasure. "
               "No measured or modeled output certifies safe transmit power.")

if section == "Antenna Tuning":
    st.subheader("Antenna tuning assistant")
    st.caption("First-order length guidance for an adjustable resonant element, not a full antenna model.")
    target = st.number_input("Tuning target (MHz)", min_value=0.001, value=146.0,
                              key="tuning_target")
    current_length = st.number_input("Current resonant element length (mm)",
                                     min_value=0.1, value=1000.0)
    tolerance = st.number_input("On-target tolerance (MHz)", min_value=0.0,
                                value=0.05, step=0.01)
    before_file = st.file_uploader("Before measurement (.s1p)", type=["s1p"],
                                   key="tuning_before")
    after_file = st.file_uploader("After measurement (.s1p), optional",
                                  type=["s1p"], key="tuning_after")
    session_label = st.text_input("Tuning session label", value="Antenna tuning")
    session_notes = st.text_area("Tuning notes", key="tuning_notes")
    if "tuning_history" not in st.session_state:
        st.session_state.tuning_history = []
    import_file = st.file_uploader("Import previous tuning history (JSON)",
                                   type=["json"], key="tuning_history_import")
    if import_file is not None and st.button("Import tuning history"):
        try:
            st.session_state.tuning_history = load_history(
                import_file.getvalue().decode("utf-8-sig"))
            st.success("Tuning history imported into this session.")
        except (ValueError, UnicodeDecodeError) as exc:
            st.error(f"History import failed: {exc}")
    if before_file is not None:
        try:
            before = parse_s1p(before_file.getvalue().decode("utf-8-sig"))
        except (ValueError, UnicodeDecodeError) as exc:
            st.error(f"Before measurement: {exc}")
        else:
            advice = tuning_advice(before, target, current_length, tolerance)
            if advice.resonance_mhz is not None:
                st.metric("Nearest measured resonance", f"{advice.resonance_mhz:.4f} MHz",
                          delta=f"{advice.frequency_error_mhz:+.4f} MHz vs target")
            st.markdown(f"**Tuning guidance: {advice.direction.capitalize()}**")
            if advice.estimated_change_mm is not None:
                st.metric("Estimated length change",
                          f"{advice.estimated_change_mm:+.2f} mm")
            st.info(advice.message)
            if after_file is not None:
                try:
                    after = parse_s1p(after_file.getvalue().decode("utf-8-sig"))
                except (ValueError, UnicodeDecodeError) as exc:
                    st.error(f"After measurement: {exc}")
                else:
                    if before.reference_ohm != after.reference_ohm:
                        st.warning("Reference impedances differ; compare results with caution.")
                    comparison = tuning_comparison(before, after, target)
                    st.subheader("Before vs after")
                    st.dataframe([comparison], hide_index=True, use_container_width=True)
                    fig = go.Figure()
                    for name, sweep in (("Before", before), ("After", after)):
                        fig.add_trace(go.Scatter(
                            x=[f/1e6 for f in sweep.frequencies_hz],
                            y=[v if math.isfinite(v) else None for v in
                               (swr_from_gamma(g) for g in sweep.gamma)], name=name))
                    fig.add_vline(x=target, line_dash="dash",
                                  annotation_text="Target")
                    fig.update_layout(title="Before/after SWR",
                                      xaxis_title="Frequency (MHz)", yaxis_title="SWR")
                    st.plotly_chart(fig, use_container_width=True)
            if st.button("Add tuning result to session history"):
                try:
                    st.session_state.tuning_history = add_history_entry(
                        st.session_state.tuning_history, session_label, advice,
                        current_length, session_notes)
                    st.success("Result saved in this browser session.")
                except ValueError as exc:
                    st.error(str(exc))
    if st.session_state.tuning_history:
        st.subheader("Tuning history")
        st.dataframe(st.session_state.tuning_history,
                     hide_index=True, use_container_width=True)
        st.download_button("Export tuning history (JSON)",
                           history_json(st.session_state.tuning_history),
                           file_name="rf_lab_tuning_history.json",
                           mime="application/json")
        if st.button("Clear session history"):
            st.session_state.tuning_history = []
            st.rerun()
    st.warning("Length guidance assumes resonance varies approximately inversely "
               "with element length. Do not cut to the full estimate without "
               "small adjustments and repeated measurements.")

if section == "Radiation Patterns":
    st.subheader("Interactive antenna radiation patterns")
    st.caption("Idealized normalized far-field models — not an electromagnetic solver or coverage prediction.")
    model = st.selectbox("Antenna model", ANTENNA_TYPES, key="pattern_model")
    pattern_frequency = st.number_input("Operating frequency (MHz)", min_value=0.001,
                                         value=146.0, key="pattern_frequency")
    st.metric("Free-space wavelength", f"{299.792458 / pattern_frequency:.3f} m")
    floor = st.slider("Plot floor (dB)", min_value=-60, max_value=-10,
                      value=-35, step=5)
    elevation_angle = st.slider("Azimuth-cut elevation above horizon (degrees)",
                                min_value=-90, max_value=90, value=0)
    theta_deg, elevation_power = elevation_cut(model)
    azimuth_deg, azimuth_power = azimuth_cut(model, elevation_angle)
    left, right = st.columns(2)
    with left:
        elevation_fig = go.Figure(go.Scatterpolar(
            theta=theta_deg, r=np.maximum(10*np.log10(np.maximum(elevation_power, 1e-12)), floor)-floor,
            mode="lines", name="Elevation"))
        elevation_fig.update_layout(title="Elevation cut (relative power, dB)",
            polar=dict(radialaxis=dict(tickvals=[0, -floor/2, -floor],
                ticktext=[f"{floor} dB", f"{floor/2:g} dB", "0 dB"],
                range=[0, -floor])), showlegend=False)
        st.plotly_chart(elevation_fig, use_container_width=True)
    with right:
        azimuth_fig = go.Figure(go.Scatterpolar(
            theta=azimuth_deg,
            r=np.maximum(10*np.log10(np.maximum(azimuth_power, 1e-12)), floor)-floor,
            mode="lines", name="Azimuth"))
        azimuth_fig.update_layout(title="Azimuth cut (relative power, dB)",
            polar=dict(radialaxis=dict(tickvals=[0, -floor/2, -floor],
                ticktext=[f"{floor} dB", f"{floor/2:g} dB", "0 dB"],
                range=[0, -floor])), showlegend=False)
        st.plotly_chart(azimuth_fig, use_container_width=True)
    px, py, pz, radius = radiation_mesh(model)
    surface = go.Figure(go.Surface(x=px, y=py, z=pz, surfacecolor=radius,
                                    colorscale="Viridis", showscale=True,
                                    colorbar=dict(title="Relative field")))
    surface.update_layout(title="Rotatable 3D field-amplitude pattern",
        scene=dict(xaxis_title="X", yaxis_title="Y", zaxis_title="Antenna axis (Z)",
                   aspectmode="data"), height=560)
    st.plotly_chart(surface, use_container_width=True)
    st.info("0 dB is the pattern maximum, not dBi. The models are rotationally "
            "symmetric and assume ideal free space or perfect ground. "
            "Frequency affects wavelength but not the normalized ideal pattern.")

if section == "Yagi Patterns":
    st.subheader("3-element Yagi radiation-pattern explorer")
    st.caption("Exploratory coupled-element surrogate; not a validated NEC or thin-wire EM solver.")
    yf_pattern = st.number_input("Yagi pattern frequency (MHz)", min_value=0.001,
                                  value=146.0, key="yp_frequency")
    default_design = design_yagi(yf_pattern)
    wavelength = 299.792458/yf_pattern
    names = ("Reflector", "Driven", "Director")
    lengths = []
    for name, element in zip(names, default_design.elements):
        lengths.append(st.number_input(f"{name} length (cm)", min_value=0.1,
            value=round(element.length_m*100, 2), key=f"yp_len_{name}"))
    spacing1 = st.number_input("Reflector → driven spacing (cm)", min_value=0.1,
        value=round(default_design.elements[1].position_m*100,2))
    spacing2 = st.number_input("Driven → director spacing (cm)", min_value=0.1,
        value=round((default_design.elements[2].position_m-
                     default_design.elements[1].position_m)*100,2))
    coupling = st.slider("Illustrative coupling strength (not calibrated)",
                         min_value=0.0, max_value=0.8, value=0.25, step=0.05)
    positions = [0, spacing1/100, (spacing1+spacing2)/100]
    lengths_m = [length/100 for length in lengths]
    try:
        result = simulate_yagi(yf_pattern, lengths_m, positions, coupling, samples=91)
        xx, yy, zz, rr = yagi_surface(yf_pattern, lengths_m, positions, coupling)
    except (ValueError, np.linalg.LinAlgError) as exc:
        st.error(f"Could not calculate pattern: {exc}")
    else:
        m1, m2 = st.columns(2)
        m1.metric("Surrogate directivity (dBi)", f"{result.directivity_dbi:.2f}")
        m2.metric("Forward/back ratio (dB)", f"{result.front_to_back_db:.2f}")
        left, right = st.columns(2)
        with left:
            azfig = go.Figure(go.Scatterpolar(
                theta=result.azimuth_deg,
                r=np.maximum(result.azimuth_db,-40)+40, mode="lines"))
            azfig.update_layout(title="Azimuth (0° toward director)",
                polar=dict(radialaxis=dict(range=[0,40],
                    tickvals=[0,10,20,30,40],
                    ticktext=["-40","-30","-20","-10","0"])))
            st.plotly_chart(azfig, use_container_width=True)
        with right:
            elfig = go.Figure(go.Scatterpolar(
                theta=result.elevation_deg,
                r=np.maximum(result.elevation_db,-40)+40, mode="lines"))
            elfig.update_layout(title="Elevation (polar angle from element axis)",
                polar=dict(radialaxis=dict(range=[0,40],
                    tickvals=[0,10,20,30,40],
                    ticktext=["-40","-30","-20","-10","0"])))
            st.plotly_chart(elfig, use_container_width=True)
        fig3d = go.Figure(go.Surface(x=xx,y=yy,z=zz,surfacecolor=rr,
                                     colorscale="Viridis"))
        fig3d.update_layout(title="3D normalized field pattern",
            scene=dict(xaxis_title="Boom direction (X)", yaxis_title="Y",
                       zaxis_title="Elements (Z)",aspectmode="data"),
            height=550)
        st.plotly_chart(fig3d, use_container_width=True)
        st.dataframe([{"Element":name,"Length (cm)":lengths[i],
                       "Position (cm)":positions[i]*100,
                       "Relative current magnitude":abs(result.currents[i])}
                      for i,name in enumerate(names)],hide_index=True,
                     use_container_width=True)
    st.warning("The coupled-current model uses heuristic interactions, not "
               "physical mutual impedances. Directivity and front/back values "
               "are illustrative and must not be treated as verified antenna gain.")

if section == "Thin-Wire MoM":
    st.subheader("Experimental thin-wire EFIE antenna solver")
    st.error("Research prototype: numerical results are NOT validated. "
             "Feed impedance and SWR can be seriously inaccurate and mesh-dependent. "
             "Do not use for construction, matching, gain or safety decisions.")
    mom_freq = st.number_input("MoM frequency (MHz)", min_value=0.001,
                                value=146.0, key="mom_frequency")
    mom_default = design_yagi(mom_freq)
    mom_lengths = []
    for element in mom_default.elements:
        mom_lengths.append(st.number_input(f"MoM {element.name} length (cm)",
            min_value=0.1, value=round(element.length_m*100,2),
            key=f"mom_len_{element.name}")/100)
    mom_s1 = st.number_input("MoM reflector-to-driven spacing (cm)",
        min_value=0.1, value=round(mom_default.elements[1].position_m*100,2))
    mom_s2 = st.number_input("MoM driven-to-director spacing (cm)",
        min_value=0.1, value=round((mom_default.elements[2].position_m-
                                  mom_default.elements[1].position_m)*100,2))
    mom_radius = st.number_input("Wire radius (mm)", min_value=0.01,
                                 value=2.0, step=0.25)
    mom_segments = st.select_slider("Segments per element (odd)",
                                    options=[5,7,9,11,13,15,17,19,21],
                                    value=9)
    mom_positions = [0,mom_s1/100,(mom_s1+mom_s2)/100]
    if st.button("Run experimental EFIE solve"):
        try:
            solution = solve_yagi_mom(mom_freq,mom_lengths,mom_positions,
                wire_radius_mm=mom_radius,segments_per_element=mom_segments)
        except (ValueError, np.linalg.LinAlgError) as exc:
            st.error(f"Solver failed: {exc}")
        else:
            st.caption("All results below are experimental and mesh-dependent.")
            cols = st.columns(4)
            cols[0].metric("Feed impedance (Ω, unvalidated)",
                f"{solution.feed_impedance_ohm.real:.1f} "
                f"{solution.feed_impedance_ohm.imag:+.1f}j")
            cols[1].metric("SWR (unvalidated)",f"{solution.swr_50:.2f}")
            cols[2].metric("Directivity (dBi, unvalidated)",
                           f"{solution.directivity_dbi:.2f}")
            cols[3].metric("Front/back (dB, unvalidated)",
                           f"{solution.front_to_back_db:.2f}")
            st.caption(f"Matrix condition number: {solution.condition_number:.3g}")
            fig_current = go.Figure()
            for index,name in enumerate(("Reflector","Driven","Director")):
                mask=solution.element_indices==index
                fig_current.add_trace(go.Scatter(
                    x=solution.segment_centers_m[mask]*100,
                    y=np.abs(solution.currents_a[mask]),
                    mode="lines+markers",name=name))
            fig_current.update_layout(title="Solved current magnitudes",
                xaxis_title="Position along element (cm)",
                yaxis_title="Current magnitude (A)")
            st.plotly_chart(fig_current,use_container_width=True)
            ca,ce=st.columns(2)
            with ca:
                fa=go.Figure(go.Scatterpolar(theta=solution.azimuth_deg,
                    r=np.maximum(solution.azimuth_db,-40)+40,mode="lines"))
                fa.update_layout(title="Azimuth (0° toward director)",
                    polar=dict(radialaxis=dict(range=[0,40])))
                st.plotly_chart(fa,use_container_width=True)
            with ce:
                fe=go.Figure(go.Scatterpolar(theta=solution.elevation_deg,
                    r=np.maximum(solution.elevation_db,-40)+40,mode="lines"))
                fe.update_layout(title="Elevation from element axis",
                    polar=dict(radialaxis=dict(range=[0,40])))
                st.plotly_chart(fe,use_container_width=True)
            st.info("Change the segment count and rerun to inspect mesh "
                    "sensitivity. Stability alone does not establish physical accuracy.")
    st.markdown("See [solver assumptions](https://github.com/JamalDaher/rf-lab/blob/main/docs/thin-wire-mom.md) "
                "after this version is merged.")

if section == "Validation":
    st.subheader("Numerical validation diagnostics")
    st.warning("These diagnostics DO NOT validate the EFIE solver against NEC "
               "or measured antennas. No engineering-grade accuracy claim.")
    check = short_dipole_directivity_check()
    st.metric("Short-dipole integration absolute error",
              f"{check['absolute_error']:.3g}")
    st.caption("Checks numerical angular integration of sin²(θ) against "
               "the analytical directivity 1.5 (1.7609 dBi); "
               "not an EFIE solver benchmark.")
    vf = st.number_input("Validation frequency (MHz)",min_value=0.001,
                         value=146.0,key="validation_frequency")
    wavelength = 299792458.0/(vf*1e6)
    vl = [.505*wavelength,.475*wavelength,.45*wavelength]
    vp = [0,.2*wavelength,.35*wavelength]
    st.caption("Fixed demonstration Yagi geometry: lengths 0.505λ, 0.475λ, "
               "0.450λ; positions 0, 0.20λ, 0.35λ; wire radius 2 mm.")
    if st.button("Run mesh sensitivity study"):
        try:
            study = mesh_sensitivity(vf,vl,vp,meshes=(5,7,9,11))
        except (ValueError,np.linalg.LinAlgError) as exc:
            st.error(f"Mesh study failed: {exc}")
        else:
            st.dataframe([{
                "Segments/element":r.segments,
                "Feed R (Ω)":round(r.impedance_ohm.real,3),
                "Feed X (Ω)":round(r.impedance_ohm.imag,3),
                "SWR":round(r.swr,3),
                "Directivity (dBi)":round(r.directivity_dbi,3),
                "F/B (dB)":round(r.front_to_back_db,3),
                "Matrix condition":round(r.condition_number,2),
                "Relative ΔZ":r.relative_impedance_change,
                "ΔDirectivity (dB)":r.directivity_change_db
            } for r in study.rows],hide_index=True,use_container_width=True)
            st.metric("Mesh threshold check",
                      "Within thresholds" if study.numerically_stable
                      else "Outside thresholds")
            st.warning(study.warning)
    st.markdown("[Read the validation limitations and outstanding acceptance "
                "gates](https://github.com/JamalDaher/rf-lab/blob/main/docs/validation-v1.md)")

if section == "NEC Comparison":
    st.subheader("NEC-2 / NEC-4 reference comparison")
    st.warning("Requires independently generated NEC results. RF Lab does not "
               "run NEC or include a verified NEC benchmark. Comparisons are "
               "not proof of physical accuracy.")
    st.markdown("[Reference JSON format and modeling requirements]"
                "(https://github.com/JamalDaher/rf-lab/blob/main/docs/nec-reference-comparison.md)")
    uploaded_reference = st.file_uploader("Upload NEC reference JSON",
                                           type=["json"],key="nec_reference_upload")
    if uploaded_reference is not None:
        try:
            reference = load_reference(uploaded_reference.getvalue())
        except (ValueError,TypeError,KeyError,UnicodeDecodeError) as exc:
            st.error(f"Invalid NEC reference: {exc}")
        else:
            st.caption(f"Source: {reference.source} · {reference.solver} "
                       f"{reference.solver_version}")
            if st.button("Compare experimental EFIE against reference"):
                try:
                    comparison = compare_reference(reference)
                except (ValueError,np.linalg.LinAlgError) as exc:
                    st.error(f"Comparison failed: {exc}")
                else:
                    st.metric("Absolute feed impedance error (Ω)",
                              f"{comparison['impedance_absolute_error_ohm']:.2f}")
                    st.metric("Relative feed impedance error",
                              f"{100*comparison['impedance_relative_error']:.1f}%")
                    st.metric("Directivity difference (dB)",
                              f"{comparison['directivity_error_db']:+.2f}")
                    rows=[
                        {"Metric":"Resistance error (Ω)",
                         "Difference":comparison["resistance_error_ohm"]},
                        {"Metric":"Reactance error (Ω)",
                         "Difference":comparison["reactance_error_ohm"]},
                        {"Metric":"Directivity difference (dB)",
                         "Difference":comparison["directivity_error_db"]}
                    ]
                    if comparison["front_to_back_error_db"] is not None:
                        rows.append({"Metric":"Front/back difference (dB)",
                                     "Difference":comparison["front_to_back_error_db"]})
                    if comparison["azimuth_rms_error_db"] is not None:
                        rows.append({"Metric":"Azimuth RMS error (dB)",
                                     "Difference":comparison["azimuth_rms_error_db"]})
                    st.dataframe(rows,hide_index=True,use_container_width=True)
                    if comparison["azimuth_angles_deg"] is not None:
                        fig=go.Figure()
                        fig.add_trace(go.Scatter(
                            x=comparison["azimuth_angles_deg"],
                            y=comparison["azimuth_reference_db"],
                            name="NEC reference",mode="lines+markers"))
                        fig.add_trace(go.Scatter(
                            x=comparison["azimuth_angles_deg"],
                            y=comparison["azimuth_model_db"],
                            name="Experimental EFIE",mode="lines+markers"))
                        fig.update_layout(xaxis_title="Azimuth (degrees)",
                                          yaxis_title="Relative pattern (dB)")
                        st.plotly_chart(fig,use_container_width=True)
                    st.warning("Compare geometry, excitation and pattern "
                               "normalization before interpreting these errors.")

if section == "NEC Comparison":
    st.divider()
    st.subheader("Generate a NEC-2 input deck")
    st.caption("Creates a free-space 3-element Yagi model for an independently "
               "installed NEC-2 solver. Streamlit Cloud does not run NEC.")
    nec_freq=st.number_input("Deck frequency (MHz)",min_value=0.001,
                             value=146.0,key="nec_deck_frequency")
    nec_wavelength=299792458/(nec_freq*1e6)
    nec_lengths=[.505*nec_wavelength,.475*nec_wavelength,.45*nec_wavelength]
    nec_positions=[0,.2*nec_wavelength,.35*nec_wavelength]
    nec_count=st.select_slider("NEC segments per element",
                               options=[5,7,9,11,13,15,17,19,21],
                               value=9,key="nec_deck_segments")
    nec_radius=st.number_input("NEC wire radius (mm)",min_value=0.01,
                               value=2.0,key="nec_deck_radius")
    try:
        nec_deck=generate_yagi_nec2(nec_freq,nec_lengths,nec_positions,
                                    wire_radius_mm=nec_radius,
                                    segments_per_element=nec_count)
    except ValueError as exc:
        st.error(f"Invalid NEC geometry: {exc}")
    else:
        st.download_button("Download NEC-2 input (.nec)",data=nec_deck,
                           file_name="rf_lab_yagi.nec",mime="text/plain")
        with st.expander("Preview NEC-2 input deck"):
            st.code(nec_deck,language="text")
    st.info("Run this deck with a compatible local NEC-2 solver, inspect the "
            "raw output, and convert verified results to the reference JSON "
            "format for comparison above. This release does not claim a "
            "completed automated solver-to-JSON pipeline.")

if section == "NEC Comparison":
    st.divider()
    st.subheader("Local NEC-2 benchmark reports")
    st.caption("Run the trusted NEC executable on your own computer with "
               "python -m rf_lab.nec2_cli, then upload comparison.json here.")
    st.code("python -m rf_lab.nec2_cli --adapter nec2c --executable nec2c "
            "--solver-version VERIFIED_VERSION --output-dir ./nec-results",
            language="bash")
    report_upload=st.file_uploader("Upload local comparison.json",
                                   type=["json"],key="nec_local_report")
    if report_upload is not None:
        try:
            import json
            report=json.loads(report_upload.getvalue())
            manifest=report["manifest"]
            metrics=report["comparison"]
            if (manifest["schema_version"]!=1 or
                    manifest["reference_solver"]!="NEC-2" or
                    not isinstance(metrics["absolute_error_ohm"],(int,float))):
                raise ValueError("unsupported report format")
            st.caption(f"Solver version: {manifest['solver_version']}")
            st.caption(f"Input SHA-256: {manifest['deck_sha256']}")
            st.metric("NEC vs experimental EFIE impedance error (Ω)",
                      f"{metrics['absolute_error_ohm']:.3f}")
            st.metric("Relative impedance error",
                      f"{100*metrics['relative_error']:.2f}%")
            st.dataframe([
                {"Metric":"Resistance error (Ω)",
                 "Value":metrics["resistance_error_ohm"]},
                {"Metric":"Reactance error (Ω)",
                 "Value":metrics["reactance_error_ohm"]}
            ],hide_index=True,use_container_width=True)
            st.warning("This is an imported local report, not an independently "
                       "verified NEC reference or physical accuracy certificate.")
        except (ValueError,TypeError,KeyError,UnicodeDecodeError) as exc:
            st.error(f"Could not read local benchmark report: {exc}")

if section == "NEC Comparison":
    st.divider()
    st.subheader("NEC radiation pattern comparison")
    st.caption("Available only for reports with successfully parsed NEC "
               "theta=90° azimuth cuts; normalized gains are not directivity.")
    if report_upload is not None:
        try:
            import json
            pattern_report=json.loads(report_upload.getvalue())
            metrics=pattern_report["comparison"]
            if "pattern_rms_error_db" in metrics:
                st.metric("Normalized pattern RMS error (dB)",
                          f"{metrics['pattern_rms_error_db']:.2f}")
                fig=go.Figure()
                fig.add_trace(go.Scatter(x=metrics["pattern_angles_deg"],
                    y=metrics["nec_relative_db"],name="NEC-2c",mode="lines"))
                fig.add_trace(go.Scatter(x=metrics["pattern_angles_deg"],
                    y=metrics["model_relative_db"],name="Experimental EFIE",
                    mode="lines"))
                fig.update_layout(xaxis_title="NEC phi (degrees)",
                                  yaxis_title="Normalized gain (dB)")
                st.plotly_chart(fig,use_container_width=True)
            else:
                st.info("No comparable radiation cut in this report. "
                        +str(metrics.get("pattern_parse_warning","")))
        except (ValueError,KeyError,TypeError,UnicodeDecodeError) as exc:
            st.error(f"Unable to display radiation comparison: {exc}")

if section == "NEC Comparison":
    st.divider()
    st.subheader("Scientific benchmark suite — mesh sensitivity")
    st.caption("Upload summary.json produced by the local NEC-2c benchmark "
               "CLI. These comparisons are not certified physical validation.")
    st.code("python -m rf_lab.benchmark_cli --executable nec2c "
            "--solver-version VERIFIED_VERSION --output-dir ./benchmarks",
            language="bash")
    suite_upload=st.file_uploader("Upload benchmark summary.json",
                                  type=["json"],key="benchmark_suite_upload")
    if suite_upload is not None:
        try:
            import json
            summary=json.loads(suite_upload.getvalue())
            if (summary.get("schema_version")!=1 or
                    summary.get("kind")!="rf-lab-nec2c-mesh-benchmark"):
                raise ValueError("unsupported benchmark summary")
            cases=summary["cases"]
            if not isinstance(cases,list) or not 2<=len(cases)<=8:
                raise ValueError("expected 2–8 benchmark cases")
            rows=[]
            for case in cases:
                n=int(case["segments_per_element"])
                if n<5 or n>31 or n%2==0:
                    raise ValueError("invalid mesh")
                rows.append({"Segments":n,
                    "NEC R (Ω)":float(case["nec_real_ohm"]),
                    "NEC X (Ω)":float(case["nec_imag_ohm"]),
                    "EFIE R (Ω)":float(case["efie_real_ohm"]),
                    "EFIE X (Ω)":float(case["efie_imag_ohm"]),
                    "Error (Ω)":float(case["absolute_error_ohm"])})
            st.dataframe(rows,hide_index=True,use_container_width=True)
            fig=go.Figure()
            for name in ("NEC R (Ω)","EFIE R (Ω)","NEC X (Ω)","EFIE X (Ω)"):
                fig.add_trace(go.Scatter(x=[row["Segments"] for row in rows],
                    y=[row[name] for row in rows],mode="lines+markers",name=name))
            fig.update_layout(xaxis_title="Segments per element",
                              yaxis_title="Feed impedance component (Ω)")
            st.plotly_chart(fig,use_container_width=True)
            st.download_button("Download benchmark summary",
                data=json.dumps(summary,indent=2),file_name="summary.json",
                mime="application/json")
            st.warning("Mesh convergence is numerical sensitivity, not "
                       "independent proof of antenna-model accuracy.")
        except (ValueError,KeyError,TypeError,UnicodeDecodeError) as exc:
            st.error(f"Invalid benchmark summary: {exc}")

if section == "NEC Comparison":
    st.divider()
    st.subheader("Validation dashboard & PDF reports")
    st.caption("Compare two compatible mesh benchmarks, generate a PDF, "
               "and inspect reproducibility metadata. No certified physical "
               "accuracy is implied.")
    baseline_upload=st.file_uploader("Optional baseline summary.json",
        type=["json"],key="benchmark_history_baseline")
    candidate_upload=st.file_uploader("Candidate summary.json",
        type=["json"],key="benchmark_history_candidate")
    if candidate_upload is not None:
        try:
            from rf_lab.benchmark_reports import validate_summary,compare_summaries
            from rf_lab.benchmark_pdf import build_pdf
            import json
            candidate=validate_summary(candidate_upload.getvalue())
            baseline=(validate_summary(baseline_upload.getvalue())
                      if baseline_upload is not None else None)
            st.success("Benchmark schema and internal numerical consistency verified.")
            st.caption("SHA-256 values in an uploaded summary are declarations; "
                       "verifying raw deck and solver-output bytes requires "
                       "the original local artifacts.")
            st.dataframe(candidate["cases"],hide_index=True,use_container_width=True)
            if baseline is not None:
                diff=compare_summaries(baseline,candidate)
                st.subheader("Historical numerical differences")
                st.dataframe(diff["changes"],hide_index=True,use_container_width=True)
                fig=go.Figure()
                fig.add_trace(go.Scatter(
                    x=[r["segments_per_element"] for r in diff["changes"]],
                    y=[r["impedance_error_change_ohm"] for r in diff["changes"]],
                    mode="lines+markers",name="Change in absolute error"))
                fig.update_layout(xaxis_title="Segments per element",
                                  yaxis_title="Error change (Ω)")
                st.plotly_chart(fig,use_container_width=True)
            pdf=build_pdf(candidate,baseline)
            st.download_button("Download scientific benchmark PDF",
                data=pdf,file_name="rf-lab-benchmark-report.pdf",
                mime="application/pdf",key="benchmark_pdf_download")
            st.warning("Validated data structure, not electromagnetic accuracy.")
        except (ValueError,TypeError,KeyError,UnicodeDecodeError) as exc:
            st.error(f"Benchmark validation failed: {exc}")

if section == "Yagi Optimizer":
    st.subheader("Experimental 3-element Yagi optimizer")
    st.warning("Optimization uses an experimental, unvalidated EFIE model. "
               "Scores are not measured antenna gain, match or performance. "
               "Confirm designs with NEC and an antenna analyzer before building.")
    from rf_lab.yagi_optimizer import optimize_yagi,cutting_list,optimized_nec_deck
    opt_frequency=st.number_input("Optimization frequency (MHz)",
        min_value=1.0,max_value=3000.0,value=146.0,key="opt_frequency")
    opt_wavelength=299792458/(opt_frequency*1e6)
    opt_objective=st.selectbox("Objective",
        ["balanced","match","front_to_back","directivity"],key="opt_objective")
    opt_iterations=st.slider("Candidate evaluations",1,40,12,key="opt_iterations")
    opt_seed=st.number_input("Reproducible random seed",
        min_value=0,max_value=2**32-1,value=42,step=1,key="opt_seed")
    opt_length=st.slider("Maximum length variation (%)",0,30,8,key="opt_length")
    opt_spacing=st.slider("Maximum spacing variation (%)",0,30,20,key="opt_spacing")
    opt_segments=st.select_slider("EFIE segments per element",
        options=[5,7,9,11],value=7,key="opt_segments")
    opt_radius=st.number_input("Wire radius (mm)",min_value=0.01,
        value=2.0,key="opt_radius")
    st.caption("Baseline geometry: lengths 0.505λ / 0.475λ / 0.450λ; "
               "boom positions 0 / 0.20λ / 0.35λ. Reflector position fixed.")
    if st.button("Optimize candidate geometry",key="run_yagi_optimizer"):
        try:
            result=optimize_yagi(opt_frequency,
                [.505*opt_wavelength,.475*opt_wavelength,.45*opt_wavelength],
                [0,.2*opt_wavelength,.35*opt_wavelength],
                objective=opt_objective,iterations=opt_iterations,
                seed=int(opt_seed),length_variation=opt_length/100,
                spacing_variation=opt_spacing/100,
                segments_per_element=opt_segments,wire_radius_mm=opt_radius)
            st.metric("Best experimental objective score",f"{result.best.score:.3f}",
                delta=f"{result.best.score-result.original.score:+.3f} vs baseline")
            st.caption(f"Evaluated {result.evaluated} candidates; "
                       f"rejected {result.rejected}.")
            st.dataframe(cutting_list(result),hide_index=True,use_container_width=True)
            fig=go.Figure()
            for name,candidate in (("Original",result.original),
                                    ("Optimized",result.best)):
                fig.add_trace(go.Scatter(x=[x*100 for x in candidate.positions_m],
                    y=[x*100 for x in candidate.lengths_m],
                    name=name,mode="lines+markers"))
            fig.update_layout(xaxis_title="Boom position (cm)",
                              yaxis_title="Element length (cm)")
            st.plotly_chart(fig,use_container_width=True)
            convergence=go.Figure()
            convergence.add_trace(go.Scatter(
                x=[row["evaluation"] for row in result.history],
                y=[row["best_score"] for row in result.history],
                mode="lines+markers",name="Best score"))
            convergence.update_layout(xaxis_title="Candidate evaluation",
                                      yaxis_title="Experimental objective score")
            st.plotly_chart(convergence,use_container_width=True)
            st.download_button("Download optimized NEC input",
                data=optimized_nec_deck(result),file_name="optimized-yagi.nec",
                mime="text/plain")
            import csv
            import io
            stream=io.StringIO()
            writer=csv.DictWriter(stream,fieldnames=["element","length_mm",
                                                      "boom_position_mm"])
            writer.writeheader()
            writer.writerows(cutting_list(result))
            st.download_button("Download candidate cutting list (CSV)",
                data=stream.getvalue(),file_name="candidate-yagi-dimensions.csv",
                mime="text/csv")
        except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
            st.error(f"Optimization could not complete: {exc}")

if section == "Design Workbench":
    from rf_lab.design_workbench import (make_design,validate_design,design_json,
        compare_designs,frequency_sweep,package_design)
    st.caption("Portable JSON designs · local session history · experimental EFIE frequency sweeps")
    if "design_library" not in st.session_state:
        st.session_state.design_library=[]
    left,right=st.columns([2,1])
    with left:
        design_name=st.text_input("Design name",value="2 m reference Yagi",max_chars=80)
        frequency=st.number_input("Design frequency (MHz)",min_value=1.0,max_value=3000.0,value=146.0,key="dw_freq")
        wavelength=299792458/(frequency*1e6)
        lengths=[st.number_input(label,min_value=0.01,value=round(factor*wavelength,5),format="%.5f",key=f"dw_l{i}")
                 for i,(label,factor) in enumerate(zip(
                     ["Reflector length (m)","Driven length (m)","Director length (m)"],[.505,.475,.45]))]
        gap1=st.number_input("Reflector → driven spacing (m)",min_value=.001,value=round(.2*wavelength,5),format="%.5f")
        gap2=st.number_input("Driven → director spacing (m)",min_value=.001,value=round(.15*wavelength,5),format="%.5f")
    with right:
        radius=st.number_input("Wire radius (mm)",min_value=.01,value=2.0,key="dw_radius")
        mesh=st.select_slider("Mesh segments per element",options=[5,7,9,11],value=7,key="dw_mesh")
        uploads=st.file_uploader("Import saved design JSON files",type=["json"],
                                 accept_multiple_files=True,key="dw_import")
        if st.button("Import designs"):
            for upload in uploads or []:
                try:
                    design=validate_design(upload.getvalue())
                    st.session_state.design_library=[
                        d for d in st.session_state.design_library if d["name"]!=design["name"]]+[design]
                except (ValueError,TypeError,KeyError) as exc:
                    st.error(f"{upload.name}: {exc}")
    try:
        current=make_design(design_name,frequency,lengths,[0,gap1,gap1+gap2],radius,mesh)
        st.download_button("Download current design JSON",design_json(current),
                           file_name="rf-lab-design.json",mime="application/json")
        if st.button("Save design to this session"):
            st.session_state.design_library=[
                d for d in st.session_state.design_library if d["name"]!=current["name"]]+[current]
            st.success("Saved in this browser session. Download JSON for permanent storage.")
        designs=st.session_state.design_library
        if designs:
            st.subheader("Session design history")
            st.dataframe(compare_designs(designs[:5]),hide_index=True,use_container_width=True)
            st.caption("History is temporary. Export JSON to keep designs across sessions.")
        st.subheader("Experimental frequency sweep")
        a,b,p=st.columns(3)
        with a:
            start=st.number_input("Start (MHz)",min_value=0.1,value=round(frequency*.95,3),key="dw_start")
        with b:
            stop=st.number_input("Stop (MHz)",min_value=0.2,value=round(frequency*1.05,3),key="dw_stop")
        with p:
            points=st.slider("Sweep points",2,21,7,key="dw_points")
        if st.button("Run EFIE frequency sweep",key="dw_run"):
            try:
                st.session_state.dw_sweep=frequency_sweep(current,start,stop,points)
                st.session_state.dw_sweep_design=design_json(current)
            except (ValueError,np.linalg.LinAlgError,OverflowError) as exc:
                st.error(str(exc))
        sweep=(st.session_state.get("dw_sweep",[])
               if st.session_state.get("dw_sweep_design")==design_json(current) else [])
        if sweep:
            st.dataframe(sweep,hide_index=True,use_container_width=True)
            figure=go.Figure()
            figure.add_trace(go.Scatter(x=[x["frequency_mhz"] for x in sweep],
                y=[x["swr_50"] for x in sweep],mode="lines+markers",name="Estimated SWR"))
            figure.update_layout(xaxis_title="Frequency (MHz)",yaxis_title="Experimental SWR")
            st.plotly_chart(figure,use_container_width=True)
        st.download_button("Download design package (ZIP)",
            data=package_design(current,sweep),file_name="rf-lab-design-package.zip",
            mime="application/zip")
        st.warning("EFIE sweep estimates are unvalidated. The package includes an NEC deck "
                   "for independent analysis; it is not a verified construction plan.")
    except (ValueError,TypeError) as exc:
        st.error(f"Invalid design: {exc}")
