"""RF Lab Streamlit interface."""
import csv
import io
import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from rf_lab.core import (dipole_length_m, quarter_wave_m, swr, return_loss_db,
                         watts_to_dbm, dbm_to_watts, free_space_path_loss_db)
from rf_lab.yagi import design_yagi, cutting_list

st.set_page_config(page_title="RF Lab", page_icon="📡", layout="wide")
st.title("📡 RF Lab")
st.caption("Amateur Radio Engineering Suite · v0.2.0")
antenna, yagi, matching, power, propagation = st.tabs(
    ["Antenna Designer", "3-Element Yagi", "SWR Analyzer", "RF Power", "Path Loss"])
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
