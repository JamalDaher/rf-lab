"""Compare two IQ captures in one offline, side-by-side workbench."""
import json
import plotly.graph_objects as go
import streamlit as st
from rf_lab.sdr_lab import read_iq_bytes
from rf_lab.signal_classification import KINDS,synthetic_classification_iq
from rf_lab.signal_comparison import compare_recordings,comparison_report

def _source(side):
    st.markdown("**"+side+"**")
    mode=st.radio("Input",["Synthetic reference","IQ file"],horizontal=True,key="cmp_mode_"+side)
    if mode=="Synthetic reference":
        kind=st.selectbox("Signal shape",KINDS,index=1 if side=="Before" else 2,key="cmp_kind_"+side)
        rate=st.selectbox("Sample rate (Hz)",[8000,16000,48000],index=1,key="cmp_rate_"+side)
        snr=st.slider("SNR (dB)",-5,60,30,key="cmp_snr_"+side)
        return synthetic_classification_iq(kind,rate,.5,snr),rate
    rate=st.number_input("Sample rate (Hz)",min_value=1.0,max_value=100000000.0,
                         value=16000.0,key="cmp_file_rate_"+side)
    fmt=st.selectbox("Encoding",["complex64","cs8"],key="cmp_fmt_"+side)
    uploaded=st.file_uploader("IQ capture · max 512 KiB",type=["iq","bin","raw","cfile"],
                              key="cmp_upload_"+side)
    if uploaded is None:
        return None,rate
    return read_iq_bytes(uploaded.getvalue(),fmt),rate

def render():
    st.caption("Compare offline captures · common frequency axis in Hz · relative spectral power")
    left,right=st.columns(2)
    try:
        with left:
            before,rate_before=_source("Before")
        with right:
            after,rate_after=_source("After")
    except ValueError as exc:
        st.error(str(exc))
        return
    if before is None or after is None:
        st.info("Provide both captures to compare them.")
        return
    with st.expander("Analysis settings"):
        a,b=st.columns(2)
        with a:
            fft=st.selectbox("FFT size",[128,256,512,1024,2048],index=1,key="cmp_fft")
        with b:
            threshold=st.slider("Detection threshold (dB)",3,50,12,key="cmp_threshold")
    try:
        result=compare_recordings(before,after,rate_before,rate_after,fft,threshold)
    except ValueError as exc:
        st.error(str(exc))
        return
    m=result["metrics"]
    a,b,c=st.columns(3)
    a.metric("Bandwidth change",f"{m['bandwidth_change_hz']:+.1f} Hz")
    b.metric("Noise-floor change",f"{m['noise_floor_change_db']:+.1f} dB")
    c.metric("Activity events",f"{m['event_count_before']} → {m['event_count_after']}")
    tab1,tab2,tab3=st.tabs(["Spectrum overlay","Before vs after","Report"])
    with tab1:
        fig=go.Figure()
        for label,key in [("Before","before_db_hz"),("After","after_db_hz")]:
            fig.add_trace(go.Scatter(x=result["frequency_hz"],y=result[key],name=label,mode="lines"))
        fig.update_layout(height=390,xaxis_title="Baseband frequency offset (Hz)",
                          yaxis_title="Relative PSD (dB/Hz)")
        st.plotly_chart(fig,use_container_width=True)
        diff=go.Figure(go.Scatter(x=result["frequency_hz"],y=result["delta_db"],mode="lines",
                                  name="After minus before"))
        diff.add_hline(y=0,line_dash="dash")
        diff.update_layout(height=260,xaxis_title="Frequency offset (Hz)",
                           yaxis_title="PSD difference (dB)")
        st.plotly_chart(diff,use_container_width=True)
    with tab2:
        st.dataframe([{"metric":"99% occupied bandwidth (Hz)",
                       "before":m["bandwidth_before_hz"],"after":m["bandwidth_after_hz"]},
                      {"metric":"Detected spectral peaks","before":m["peak_count_before"],
                       "after":m["peak_count_after"]},
                      {"metric":"Waterfall events","before":m["event_count_before"],
                       "after":m["event_count_after"]},
                      {"metric":"Heuristic classification","before":m["classification_before"],
                       "after":m["classification_after"]}],hide_index=True,use_container_width=True)
        if m["classification_before"]!=m["classification_after"]:
            st.warning("Heuristic classification changed; this does not prove modulation changed.")
    with tab3:
        st.download_button("Download comparison report (JSON)",
                           json.dumps(comparison_report(result),indent=2),
                           file_name="rf-lab-signal-comparison.json",mime="application/json")
    st.info("Comparisons use relative PSD and a common frequency-offset grid. "
            "Differences can reflect receiver gain, tuning, noise, filtering, "
            "capture duration or sample rate—not necessarily antenna performance. "
            "No live SDR hardware or calibrated power measurements.")
