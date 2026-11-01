"""One uncluttered inspection dashboard for offline complex IQ."""
import json
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from rf_lab.sdr_lab import read_iq_bytes
from rf_lab.waterfall_detection import synthetic_activity_iq
from rf_lab.signal_classification import KINDS,synthetic_classification_iq
from rf_lab.signal_dashboard import inspect_signal,report_rows

def render():
    st.caption("One recording · synchronized frequency marker · spectrum + waterfall + classification")
    with st.expander("1 · Signal source and acquisition settings",expanded=True):
        source=st.radio("Source",["Synthetic activity","Synthetic modulation","Import IQ"],
                        horizontal=True,key="un_source")
        if source=="Import IQ":
            a,b=st.columns(2)
            with a:
                rate=st.number_input("Sample rate (Hz)",1.0,100000000.0,16000.0,key="un_rate")
            with b:
                fmt=st.selectbox("IQ encoding",["complex64","cs8"],key="un_fmt")
            upload=st.file_uploader("IQ file · 512 KiB maximum",type=["iq","bin","raw","cfile"],key="un_upload")
            if upload is None:
                st.info("Upload IQ samples to start inspection.")
                return
            try:
                iq=read_iq_bytes(upload.getvalue(),fmt)
            except ValueError as exc:
                st.error(str(exc))
                return
        else:
            a,b,c=st.columns(3)
            with a:
                rate=st.selectbox("Sample rate (Hz)",[8000,16000,48000],index=1,key="un_synth_rate")
            with b:
                duration=st.slider("Duration (s)",.2,1.0,.5,.1,key="un_duration")
            with c:
                snr=st.slider("Noise level / SNR (dB)",-5,60,30,key="un_snr")
            if source=="Synthetic modulation":
                kind=st.selectbox("Modulation shape",KINDS,key="un_kind")
                iq=synthetic_classification_iq(kind,rate,duration,snr)
            else:
                iq=synthetic_activity_iq(rate,duration,noise_db=max(-70,-snr))
    sizes=[n for n in (128,256,512,1024,2048) if n<=len(iq)]
    with st.expander("2 · Analysis controls",expanded=True):
        a,b,c=st.columns(3)
        with a:
            fft=st.selectbox("FFT size",sizes,index=min(1,len(sizes)-1),key="un_fft")
        with b:
            threshold=st.slider("Peak threshold (dB)",3,50,12,key="un_threshold")
        with c:
            marker=st.number_input("Frequency marker (Hz)",min_value=-float(rate)/2,
                                   max_value=float(rate)/2-float(rate)/fft,
                                   value=0.0,step=float(rate)/fft,key="un_marker")
    try:
        result=inspect_signal(iq,rate,fft,threshold,marker)
    except ValueError as exc:
        st.error(str(exc))
        return
    s,w,c=result["spectrum"],result["waterfall"],result["classification"]
    a,b,c1,d=st.columns(4)
    a.metric("99% occupied bandwidth",f"{s['occupied_bandwidth_hz']:.1f} Hz")
    b.metric("Spectral peaks",len(s["peaks"]))
    c1.metric("Activity events",len(w["events"]))
    d.metric("Signal shape",c["label"] if c else "Unclassified")
    st.caption("All frequency axes and the marker use complex-baseband frequency offsets (Hz).")
    fig=go.Figure(go.Scatter(x=s["frequency_hz"],y=s["psd_db_hz"],mode="lines",name="PSD"))
    fig.add_vline(x=result["marker"]["frequency_hz"],line_dash="dash",line_color="#F7B267")
    fig.update_layout(height=300,xaxis_title="Frequency offset (Hz)",yaxis_title="Relative PSD (dB/Hz)",
                      margin=dict(l=15,r=15,t=25,b=30))
    st.plotly_chart(fig,use_container_width=True)
    heat=go.Figure(go.Heatmap(x=w["time_s"],y=w["frequency_hz"],z=w["power_db_hz"],
                             colorscale="Viridis",colorbar=dict(title="dB/Hz")))
    heat.add_hline(y=result["marker"]["frequency_hz"],line_dash="dash",line_color="#F7B267")
    heat.update_layout(height=390,xaxis_title="Time (s)",yaxis_title="Frequency offset (Hz)",
                       margin=dict(l=15,r=15,t=25,b=30))
    st.plotly_chart(heat,use_container_width=True)
    st.caption(f"Marker: {result['marker']['frequency_hz']:.1f} Hz · "
               f"{result['marker']['psd_db_hz']:.1f} relative dB/Hz")
    tab1,tab2,tab3=st.tabs(["Signal inspector","Detected events","Export report"])
    with tab1:
        if c:
            st.write(f"**Best heuristic match:** {c['label']}")
            st.caption(c["explanation"])
            if c["uncertain"]:
                st.warning("Ambiguous classification; evidence is not calibrated probability.")
            st.dataframe([{"shape":k,"relative_evidence_percent":round(100*v,1)}
                          for k,v in c["scores"].items()],hide_index=True,use_container_width=True)
        else:
            st.info("Insufficient signal power to classify.")
        st.dataframe(s["peaks"],hide_index=True,use_container_width=True)
    with tab2:
        if w["events"]:
            st.dataframe(w["events"],hide_index=True,use_container_width=True)
        else:
            st.info("No sustained activity events at this threshold.")
    with tab3:
        report=report_rows(result)
        st.download_button("Download analysis report (JSON)",
                           json.dumps(report,indent=2),file_name="rf-lab-signal-report.json",
                           mime="application/json")
        st.caption("Includes numeric results, peak and event tables and heuristic evidence; excludes raw IQ.")
    st.info("Offline analysis only. Power values are relative, not calibrated dBm. "
            "Detected events may split or merge signals; classification is a heuristic, "
            "not a verified modulation decoder.")
