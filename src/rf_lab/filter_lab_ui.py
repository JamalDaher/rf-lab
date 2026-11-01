"""Interactive offline FIR design and complex-IQ filtering workbench."""
import io
import json
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from rf_lab.filter_lab import KINDS,design_filter,frequency_response,apply_filter,filter_report
from rf_lab.sdr_lab import read_iq_bytes
from rf_lab.signal_classification import synthetic_classification_iq
from rf_lab.spectrum_analyzer import analyze_spectrum

def render():
    st.caption("Windowed-sinc FIR design · offline IQ processing · no live hardware")
    with st.expander("Filter design",expanded=True):
        a,b,c=st.columns(3)
        with a:
            rate=st.selectbox("Sample rate (Hz)",[8000,16000,48000],index=1,key="flt_rate")
        with b:
            kind=st.selectbox("Filter type",KINDS,key="flt_kind")
        with c:
            taps=st.slider("Filter taps (odd)",11,501,101,2,key="flt_taps")
        a,b=st.columns(2)
        with a:
            low=st.number_input("Cutoff / lower edge (Hz)",min_value=1.0,
                                max_value=rate/2-2.0,value=float(rate/8),key="flt_low")
        high=None
        if kind in ("Band-pass","Notch"):
            with b:
                high=st.number_input("Upper edge (Hz)",min_value=low+1.0,
                                     max_value=rate/2-1.0,value=float(max(low+1,rate/4)),
                                     key="flt_high")
    try:
        h=design_filter(kind,rate,low,high,taps)
        response=frequency_response(h,rate)
    except ValueError as exc:
        st.error(str(exc))
        return
    a,b=st.columns(2)
    a.metric("FIR taps",len(h))
    b.metric("Group delay",f"{response['group_delay_samples']:.0f} samples")
    fig=go.Figure(go.Scatter(x=response["frequency_hz"],y=response["gain_db"],
                              name="Magnitude",mode="lines"))
    fig.update_layout(height=330,xaxis_title="Baseband frequency offset (Hz)",
                      yaxis_title="Gain (dB)")
    st.plotly_chart(fig,use_container_width=True)
    with st.expander("Phase response"):
        phase=go.Figure(go.Scatter(x=response["frequency_hz"],y=response["phase_rad"],
                                   mode="lines",name="Phase"))
        phase.update_layout(height=260,xaxis_title="Frequency offset (Hz)",
                            yaxis_title="Wrapped phase (rad)")
        st.plotly_chart(phase,use_container_width=True)
    st.markdown("#### Apply to a recording")
    source=st.radio("IQ source",["Synthetic AM-like","Import IQ"],horizontal=True,key="flt_source")
    if source=="Synthetic AM-like":
        iq=synthetic_classification_iq("AM-like",rate,.5,30)
    else:
        fmt=st.selectbox("IQ format",["complex64","cs8"],key="flt_format")
        upload=st.file_uploader("IQ file (max 512 KiB)",type=["iq","bin","raw","cfile"],key="flt_upload")
        if upload is None:
            st.info("Upload an IQ file to preview filtering.")
            return
        try:
            iq=read_iq_bytes(upload.getvalue(),fmt)
        except ValueError as exc:
            st.error(str(exc))
            return
    try:
        filtered=apply_filter(iq,h)
        before=analyze_spectrum(iq,rate,fft_size=256)
        after=analyze_spectrum(filtered,rate,fft_size=256)
    except ValueError as exc:
        st.error(str(exc))
        return
    fig2=go.Figure()
    for label,part in (("Original",before),("Filtered",after)):
        fig2.add_trace(go.Scatter(x=part["frequency_hz"],y=part["psd_db_hz"],
                                  mode="lines",name=label))
    fig2.update_layout(height=340,xaxis_title="Baseband frequency offset (Hz)",
                       yaxis_title="Relative PSD (dB/Hz)")
    st.plotly_chart(fig2,use_container_width=True)
    a,b=st.columns(2)
    a.metric("Bandwidth before",f"{before['occupied_bandwidth_hz']:.1f} Hz")
    b.metric("Bandwidth after",f"{after['occupied_bandwidth_hz']:.1f} Hz")
    report=filter_report(kind,rate,low,high,h,response)
    report["occupied_bandwidth_before_hz"]=before["occupied_bandwidth_hz"]
    report["occupied_bandwidth_after_hz"]=after["occupied_bandwidth_hz"]
    st.download_button("Download filter report (JSON)",json.dumps(report,indent=2),
                       file_name="rf-lab-filter-report.json",mime="application/json")
    payload=np.column_stack([filtered.real.astype("<f4"),filtered.imag.astype("<f4")]).tobytes()
    st.download_button("Download filtered IQ (complex64)",payload,
                       file_name="rf-lab-filtered.iq",mime="application/octet-stream")
    st.info("Designed filters are finite-length approximations. Band edges are relative to "
            "baseband DC, so band-pass/notch responses are symmetric at positive and negative "
            "frequencies. Convolution edges contain zero-padding transients; "
            "not calibrated for RF power or hardware use.")
