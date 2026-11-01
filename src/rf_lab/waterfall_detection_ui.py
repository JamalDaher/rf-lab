"""Offline waterfall visualization and event tracking interface."""
import csv
import io
import plotly.graph_objects as go
import streamlit as st
from rf_lab.sdr_lab import read_iq_bytes
from rf_lab.waterfall_detection import analyze_waterfall,synthetic_activity_iq

def render():
    st.caption("Offline time-frequency activity · relative dB/Hz · no live SDR connection")
    source=st.radio("Signal source",["Synthetic activity","Recorded IQ file"],
                    horizontal=True,key="wf_source")
    if source=="Synthetic activity":
        a,b,c=st.columns(3)
        with a:
            rate=st.selectbox("Sample rate (Hz)",[8000,16000,48000],index=1,key="wf_rate")
        with b:
            duration=st.slider("Duration (s)",.2,1.2,1.0,.2,key="wf_duration")
        with c:
            noise=st.slider("Noise amplitude (dB)",-70,0,-32,key="wf_noise")
        seed=st.number_input("Noise seed",0,100000,42,key="wf_seed")
        iq=synthetic_activity_iq(rate,duration,noise,int(seed))
    else:
        a,b=st.columns(2)
        with a:
            rate=st.number_input("IQ sample rate (Hz)",min_value=1.0,
                                 max_value=100000000.0,value=16000.0,key="wf_import_rate")
        with b:
            fmt=st.selectbox("IQ encoding",["complex64","cs8"],key="wf_format")
        upload=st.file_uploader("IQ recording (max 512 KiB)",type=["iq","bin","raw","cfile"],
                                key="wf_upload")
        if upload is None:
            st.info("Upload a recording to view time-frequency activity.")
            return
        try:
            iq=read_iq_bytes(upload.getvalue(),fmt)
        except ValueError as exc:
            st.error(str(exc))
            return
    sizes=[n for n in (128,256,512,1024,2048) if n<=len(iq)]
    a,b,c=st.columns(3)
    with a:
        size=st.selectbox("FFT size",sizes,index=min(1,len(sizes)-1),key="wf_fft")
    with b:
        overlap=st.selectbox("Overlap (%)",[0,50,75],index=1,key="wf_overlap")
    with c:
        window=st.selectbox("Window",["Hann","Rectangular"],key="wf_window")
    threshold=st.slider("Detection threshold above floor (dB)",3,50,12,key="wf_threshold")
    try:
        data=analyze_waterfall(iq,rate,size,overlap,window,threshold)
    except ValueError as exc:
        st.error(str(exc))
        return
    a,b,c=st.columns(3)
    a.metric("Detected activity events",len(data["events"]))
    b.metric("Active frames",f"{data['activity_frames']} / {data['total_frames']}")
    c.metric("Median PSD floor",f"{data['noise_floor_db_hz']:.1f} dB/Hz")
    fig=go.Figure(go.Heatmap(x=data["time_s"],y=data["frequency_hz"],
                              z=data["power_db_hz"],colorscale="Viridis",
                              colorbar=dict(title="dB/Hz")))
    if data["events"]:
        fig.add_trace(go.Scatter(x=[(e["start_s"]+e["end_s"])/2 for e in data["events"]],
                                 y=[e["frequency_hz"] for e in data["events"]],
                                 mode="markers",name="Detected activity",
                                 marker=dict(symbol="circle-open",size=9,color="white")))
    fig.update_layout(height=500,xaxis_title="Time (s)",
                      yaxis_title="Baseband frequency offset (Hz)")
    st.plotly_chart(fig,use_container_width=True)
    st.markdown("#### Activity tracking")
    if data["events"]:
        st.dataframe(data["events"],hide_index=True,use_container_width=True)
    else:
        st.info("No sustained local spectral peaks exceeded the threshold.")
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerow(["frequency_offset_hz","start_s","end_s","peak_db_per_hz","above_floor_db"])
    for event in data["events"]:
        writer.writerow([event["frequency_hz"],event["start_s"],event["end_s"],
                         event["peak_db_hz"],event["above_floor_db"]])
    st.download_button("Download detected events (CSV)",output.getvalue(),
                       file_name="rf-lab-waterfall-events.csv",mime="text/csv")
    st.info("Activity detection uses a global median PSD threshold and tracks "
            "nearby spectral peaks across adjacent FFT frames. It can split "
            "chirps or merge overlapping signals; times and frequencies are "
            "approximate. No calibrated power, live receiver or persistent monitoring.")
