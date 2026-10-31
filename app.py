"""RF Lab Streamlit interface."""
import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from rf_lab.core import (dipole_length_m, quarter_wave_m, swr, return_loss_db,
                         watts_to_dbm, dbm_to_watts, free_space_path_loss_db)

st.set_page_config(page_title="RF Lab", page_icon="📡", layout="wide")
st.title("📡 RF Lab")
st.caption("Amateur Radio Engineering Suite · v0.1.0")
antenna, matching, power, propagation = st.tabs(
    ["Antenna Designer", "SWR Analyzer", "RF Power", "Path Loss"])
with antenna:
    f = st.number_input("Frequency (MHz)", min_value=0.001, value=146.0)
    k = st.slider("Length correction factor", 0.80, 1.00, 0.95)
    st.metric("Half-wave dipole length", f"{dipole_length_m(f,k):.3f} m")
    st.metric("Each arm / quarter-wave vertical", f"{quarter_wave_m(f,k):.3f} m")
    st.info("Approximate starting dimensions; verify resonance with measurements.")
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
