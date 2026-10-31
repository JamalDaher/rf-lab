"""RF Lab Streamlit interface."""
import csv
import io
import math
import cmath
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from rf_lab.core import (dipole_length_m, quarter_wave_m, swr, return_loss_db,
                         watts_to_dbm, dbm_to_watts, free_space_path_loss_db)
from rf_lab.yagi import design_yagi, cutting_list
from rf_lab.yagi_pattern import simulate_yagi, yagi_surface
from rf_lab.mom import solve_yagi_mom
from rf_lab.validation import mesh_sensitivity, short_dipole_directivity_check
from rf_lab.nec_reference import load_reference, compare_reference
from rf_lab.nec2_runner import generate_yagi_nec2
from rf_lab.workbench import (shift_reference_plane, resonance_frequencies_hz, compare_sweeps)
from rf_lab.reporting import create_measurement_pdf
from rf_lab.patterns import (ANTENNA_TYPES, radiation_mesh, elevation_cut,
                             azimuth_cut, pattern_db)
from rf_lab.tuning import (tuning_advice, tuning_comparison, add_history_entry,
                           history_json, load_history)
from rf_lab.measurements import (smith_grid, line_input_gamma, line_input_impedance,
    parse_s1p, swr_from_gamma, return_loss_from_gamma, best_match, comparison_mhz)
from rf_lab.advanced import (smith_coordinates, gamma_from_impedance, coax_loss_db,
                             delivered_power_w, COAX_DB_PER_100FT_100MHZ,
                             l_match_solutions)

st.set_page_config(page_title="RF Lab", page_icon="📡", layout="wide")
st.title("📡 RF Lab")
st.caption("Amateur Radio Engineering Suite · v1.2.0")
antenna, yagi, matching, power, propagation, smith, coax, lmatch, line_tab, vna_tab, workbench_tab, tuning_tab, patterns_tab, yagi_pattern_tab, mom_tab, validation_tab, nec_tab = st.tabs(
    ["Antenna Designer", "3-Element Yagi", "SWR Analyzer", "RF Power",
     "Path Loss", "Smith Chart", "Coax Loss", "L-Network",
     "Transmission Line", "NanoVNA S1P", "VNA Workbench", "Antenna Tuning", "Radiation Patterns", "Yagi Patterns", "Thin-Wire MoM", "Validation", "NEC Comparison"])
with antenna:
    f = st.number_input("Frequency (MHz)", min_value=0.001, value=146.0)
    k = st.slider("Length correction factor", 0.80, 1.00, 0.95)
    st.metric("Half-wave dipole length", f"{dipole_length_m(f,k):.3f} m")
    st.metric("Each arm / quarter-wave vertical", f"{quarter_wave_m(f,k):.3f} m")
    st.info("Approximate starting dimensions; verify resonance with measurements.")
with yagi:
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
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0,design.boom_length_m*100], y=[0,0],
                                 mode="lines", line=dict(width=7, color="gray"),
                                 name="Boom"))
        for element in design.elements:
            x = element.position_m * 100
            half = element.length_m * 50
            fig.add_trace(go.Scatter(x=[x,x], y=[-half,half], mode="lines+markers",
                                     name=element.name, line=dict(width=7)))
        fig.update_layout(title="Top-down element layout (centimeters)",
                          xaxis_title="Boom position (cm)", yaxis_title="Element half-length (cm)",
                          yaxis_scaleanchor="x", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
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
with matching:
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
with power:
    w = st.number_input("Transmit power (W)", min_value=0.000001, value=5.0)
    st.metric("dBm", f"{watts_to_dbm(w):.2f}")
    st.metric("dBW", f"{watts_to_dbm(w)-30:.2f}")
    st.caption(f"Reverse conversion: {dbm_to_watts(watts_to_dbm(w)):.6g} W")
with propagation:
    frequency = st.number_input("Carrier frequency (MHz)", min_value=0.001, value=146.0)
    distance = st.number_input("Distance (km)", min_value=0.001, value=10.0)
    st.metric("Free-space path loss", f"{free_space_path_loss_db(frequency,distance):.2f} dB")
    distances = np.linspace(0.1, max(1, distance*2), 200)
    fig = go.Figure(go.Scatter(x=distances, y=[free_space_path_loss_db(frequency,d) for d in distances]))
    fig.update_layout(xaxis_title="Distance (km)", yaxis_title="Path loss (dB)")
    st.plotly_chart(fig, use_container_width=True)
    st.info("Ideal unobstructed free space only; terrain and foliage are not modeled.")

with smith:
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
with coax:
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
with lmatch:
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

with line_tab:
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
with vna_tab:
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

with workbench_tab:
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

with tuning_tab:
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

with patterns_tab:
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

with yagi_pattern_tab:
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

with mom_tab:
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

with validation_tab:
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

with nec_tab:
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

with nec_tab:
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
