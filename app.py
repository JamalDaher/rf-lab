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
from rf_lab.workbench import (shift_reference_plane, resonance_frequencies_hz, compare_sweeps)
from rf_lab.reporting import create_measurement_pdf
from rf_lab.tuning import (tuning_advice, tuning_comparison, add_history_entry,
                           history_json, load_history)
from rf_lab.measurements import (smith_grid, line_input_gamma, line_input_impedance,
    parse_s1p, swr_from_gamma, return_loss_from_gamma, best_match, comparison_mhz)
from rf_lab.advanced import (smith_coordinates, gamma_from_impedance, coax_loss_db,
                             delivered_power_w, COAX_DB_PER_100FT_100MHZ,
                             l_match_solutions)

st.set_page_config(page_title="RF Lab", page_icon="📡", layout="wide")
st.title("📡 RF Lab")
st.caption("Amateur Radio Engineering Suite · v0.6.0")
antenna, yagi, matching, power, propagation, smith, coax, lmatch, line_tab, vna_tab, workbench_tab, tuning_tab = st.tabs(
    ["Antenna Designer", "3-Element Yagi", "SWR Analyzer", "RF Power",
     "Path Loss", "Smith Chart", "Coax Loss", "L-Network",
     "Transmission Line", "NanoVNA S1P", "VNA Workbench", "Antenna Tuning"])
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
