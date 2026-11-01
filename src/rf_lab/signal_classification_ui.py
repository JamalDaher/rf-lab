"""Signal classification laboratory Streamlit interface."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from rf_lab.sdr_lab import read_iq_bytes
from rf_lab.signal_classification import KINDS,synthetic_classification_iq,classify_signal

def render():
    st.caption("Experimental modulation-shape heuristics · offline IQ only · not a verified signal decoder")
    source=st.radio("Signal source",["Synthetic reference","Recorded IQ file"],
                    horizontal=True,key="cl_source")
    if source=="Synthetic reference":
        a,b,c=st.columns(3)
        with a:
            kind=st.selectbox("Reference signal",KINDS,key="cl_kind")
            rate=st.selectbox("Sample rate (Hz)",[8000,16000,48000],index=1,key="cl_rate")
        with b:
            snr=st.slider("SNR (dB)",-5,60,30,key="cl_snr")
            duration=st.slider("Duration (s)",.2,1.0,.5,.1,key="cl_duration")
        with c:
            seed=st.number_input("Random seed",0,100000,42,key="cl_seed")
        iq=synthetic_classification_iq(kind,rate,duration,snr,int(seed))
    else:
        a,b=st.columns(2)
        with a:
            rate=st.number_input("IQ sample rate (Hz)",min_value=1.0,
                                 max_value=100000000.0,value=16000.0,key="cl_import_rate")
        with b:
            fmt=st.selectbox("IQ format",["complex64","cs8"],key="cl_fmt")
        upload=st.file_uploader("Offline IQ (max 512 KiB)",type=["iq","bin","raw","cfile"],
                                key="cl_upload")
        if upload is None:
            st.info("Upload IQ data to estimate its modulation characteristics.")
            return
        try:
            iq=read_iq_bytes(upload.getvalue(),fmt)
        except ValueError as exc:
            st.error(str(exc))
            return
    try:
        result=classify_signal(iq,rate)
    except ValueError as exc:
        st.error(str(exc))
        return
    st.metric("Best matching signal shape",result["label"])
    if result["uncertain"]:
        st.warning("Classification is ambiguous: multiple signal shapes may fit these measurements.")
    st.write(result["explanation"])
    scores=result["scores"]
    st.caption("Relative heuristic evidence only — these values are NOT calibrated probabilities.")
    fig=go.Figure(go.Bar(x=list(scores),y=[100*v for v in scores.values()]))
    fig.update_layout(yaxis_title="Relative evidence (%)",yaxis_range=[0,100],
                      height=320,margin=dict(l=15,r=15,t=20,b=35))
    st.plotly_chart(fig,use_container_width=True)
    features=result["features"]
    a,b,c=st.columns(3)
    a.metric("99% spectral bandwidth",f"{features['occupied_bandwidth_hz']:.1f} Hz")
    b.metric("Frequency variation",f"{features['instantaneous_frequency_std_hz']:.1f} Hz")
    c.metric("Envelope variation",f"{features['amplitude_cv']:.3f}")
    with st.expander("Detailed signal features"):
        st.dataframe([{"feature":k,"value":round(v,6)} for k,v in features.items()],
                     hide_index=True,use_container_width=True)
    n=min(len(iq),1000)
    fig2=go.Figure()
    fig2.add_trace(go.Scatter(x=np.arange(n)/rate,y=np.abs(iq[:n]),
                              name="Envelope",mode="lines"))
    fig2.update_layout(height=270,xaxis_title="Time (s)",yaxis_title="IQ magnitude")
    st.plotly_chart(fig2,use_container_width=True)
    st.info("CW, AM, FM and digital-like signals can overlap in these features. "
            "Frequency offsets, filters, fading, noise, carrier suppression and "
            "unknown formats can cause incorrect labels. Verify with demodulation "
            "and independent measurements before relying on any classification.")
