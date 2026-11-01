"""Streamlit spectrum analyzer for synthetic and uploaded offline IQ."""
import csv
import io
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from rf_lab.sdr_lab import read_iq_bytes
from rf_lab.spectrum_analyzer import analyze_spectrum,synthetic_spectrum_iq

def render():
    st.caption("Offline complex-IQ spectrum measurements · relative dB/Hz · no hardware or calibrated dBm")
    source=st.radio("Signal source",["Synthetic test signal","Recorded IQ file"],
                    horizontal=True,key="sa_source")
    if source=="Synthetic test signal":
        a,b,c=st.columns(3)
        with a:
            rate=st.selectbox("Sample rate (Hz)",[8000,16000,48000],index=1,key="sa_rate")
            tone=st.slider("Primary tone (Hz)",-3500,3500,1800,100,key="sa_tone")
        with b:
            second=st.slider("Secondary tone (Hz)",-3500,3500,-2800,100,key="sa_second")
            noise=st.slider("Noise amplitude (dB)",-70,0,-28,1,key="sa_noise")
        with c:
            duration=st.slider("Duration (s)",.1,1.0,.5,.1,key="sa_duration")
            seed=st.number_input("Noise seed",0,100000,42,key="sa_seed")
        iq=synthetic_spectrum_iq(rate,duration,tone,second,noise,int(seed))
    else:
        a,b=st.columns(2)
        with a:
            rate=st.number_input("IQ sample rate (Hz)",min_value=1.0,
                                 max_value=100000000.0,value=16000.0,key="sa_import_rate")
        with b:
            fmt=st.selectbox("IQ encoding",["complex64","cs8"],key="sa_format")
        uploaded=st.file_uploader("IQ recording (max 512 KiB)",type=["iq","bin","raw","cfile"],
                                  key="sa_upload")
        if uploaded is None:
            st.info("Upload an IQ recording to analyze its spectrum.")
            return
        try:
            iq=read_iq_bytes(uploaded.getvalue(),fmt)
        except ValueError as exc:
            st.error(str(exc))
            return
    choices=[v for v in (128,256,512,1024,2048,4096) if v<=len(iq)]
    a,b,c=st.columns(3)
    with a:
        fft_size=st.selectbox("FFT size",choices,index=len(choices)-1 if len(choices)<4 else 3,key="sa_fft")
    with b:
        overlap=st.selectbox("FFT overlap (%)",[0,50,75],index=1,key="sa_overlap")
    with c:
        window=st.selectbox("Window",["Hann","Rectangular"],key="sa_window")
    threshold=st.slider("Peak threshold above estimated floor (dB)",3,40,10,key="sa_threshold")
    try:
        result=analyze_spectrum(iq,rate,fft_size,overlap,window,threshold)
    except ValueError as exc:
        st.error(str(exc))
        return
    a,b,c,d=st.columns(4)
    a.metric("Noise floor (dB/Hz)",f"{result['noise_floor_db_hz']:.1f}")
    b.metric("99% occupied bandwidth",f"{result['occupied_bandwidth_hz']:.0f} Hz")
    c.metric("Detected peaks",len(result["peaks"]))
    d.metric("Resolution",f"{result['resolution_hz']:.2f} Hz")
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=result["frequency_hz"],y=result["psd_db_hz"],
                             mode="lines",name="Averaged PSD"))
    fig.add_hline(y=result["noise_floor_db_hz"],line_dash="dash",
                  annotation_text="Median floor estimate")
    fig.add_vrect(x0=result["occupied_low_hz"],x1=result["occupied_high_hz"],
                  opacity=.1,line_width=0,annotation_text="99% occupied band")
    if result["peaks"]:
        fig.add_trace(go.Scatter(x=[p["frequency_hz"] for p in result["peaks"]],
                                 y=[p["level_db_hz"] for p in result["peaks"]],
                                 mode="markers",name="Peaks",marker_size=10))
    fig.update_layout(height=440,xaxis_title="Baseband frequency offset (Hz)",
                      yaxis_title="Power spectral density (dB/Hz)")
    st.plotly_chart(fig,use_container_width=True)
    st.caption(f"Welch averaging: {result['segments_averaged']} segments. "
               "Frequencies are offsets from the IQ recording center frequency.")
    st.markdown("#### Detected peaks")
    if result["peaks"]:
        st.dataframe(result["peaks"],hide_index=True,use_container_width=True,
                     column_config={"frequency_hz":"Offset (Hz)",
                                    "level_db_hz":"PSD (dB/Hz)",
                                    "above_floor_db":"Above floor (dB)"})
    else:
        st.info("No local maxima exceeded the selected threshold.")
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerow(["frequency_offset_hz","psd_db_per_hz"])
    writer.writerows(zip(result["frequency_hz"],result["psd_db_hz"]))
    st.download_button("Download spectrum CSV",output.getvalue(),
                       file_name="rf-lab-spectrum.csv",mime="text/csv")
    st.info("Educational estimates only. The median PSD is not a calibrated noise "
            "figure; 99% occupied bandwidth is computed from cumulative FFT-bin power. "
            "Strong tones, leakage, windowing and short recordings can bias these estimates.")
