"""Streamlit SDR signal laboratory presentation."""
import csv
import io
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from rf_lab.sdr_lab import simulate,iq_spectrum,waterfall,read_iq_bytes

def render():
    st.caption("Complex-baseband communications experiments · simulated signals and offline IQ files")
    mode=st.radio("Source",["Synthetic digital modulation","Import recorded IQ"],horizontal=True)
    try:
        if mode=="Synthetic digital modulation":
            a,b,c=st.columns(3)
            with a:
                modulation=st.selectbox("Digital modulation",["BPSK","QPSK","16-QAM"])
            with b:
                count=st.slider("Symbols",128,4096,1024,128)
            with c:
                snr=st.slider("Requested SNR (dB)",-10,40,20)
            result=simulate(modulation,count,snr)
            received=result["received"]
            a,b,c=st.columns(3)
            a.metric("EVM (RMS)",f"{result['evm_percent']:.2f}%")
            b.metric("BER (empirical)",f"{result['ber']:.5f}")
            c.metric("Measured SNR",f"{result['measured_snr_db']:.1f} dB")
            st.caption("BER is computed from fixed-length binary symbol labels in an ideal "
                       "synchronized AWGN channel, not Gray-coded modem BER. "
                       "EVM uses known transmitted symbols as reference.")
            fig=go.Figure()
            fig.add_trace(go.Scattergl(x=received.real,y=received.imag,
                                       mode="markers",name="Received",
                                       marker=dict(size=5,opacity=.5)))
            reference=np.unique(result["transmitted"])
            fig.add_trace(go.Scatter(x=reference.real,y=reference.imag,
                                     mode="markers",name="Ideal",
                                     marker=dict(size=12,symbol="x")))
            fig.update_layout(xaxis_title="In-phase (I)",yaxis_title="Quadrature (Q)",
                              yaxis_scaleanchor="x",height=450)
            st.plotly_chart(fig,use_container_width=True)
            samples=np.repeat(received,8)
            rate=8000
            with st.expander("Download simulated IQ"):
                stream=io.StringIO()
                writer=csv.writer(stream)
                writer.writerow(["symbol_index","I","Q","decision_label"])
                writer.writerows(zip(range(len(received)),received.real,received.imag,
                                     result["decisions"]))
                st.download_button("Download constellation CSV",stream.getvalue(),
                                   file_name="rf-lab-constellation.csv",mime="text/csv")
            st.info("Symbols are repeated eight times for illustrative FFT/waterfall viewing; "
                    "no pulse shaping, carrier recovery or timing recovery is modeled.")
        else:
            fmt=st.selectbox("IQ format",["complex64","cs8"],
                             help="complex64: little-endian float32 I/Q pairs; cs8: signed int8 I/Q pairs")
            rate=st.number_input("Sample rate (Hz)",min_value=1.0,
                                 max_value=100000000.0,value=1000000.0)
            upload=st.file_uploader("Upload IQ recording (max 512 KiB)",type=["iq","bin","raw","cfile"])
            if upload is None:
                st.info("Upload a local IQ recording to inspect it. Files are not transmitted to an SDR.")
                return
            samples=read_iq_bytes(upload.getvalue(),fmt)
            st.metric("IQ samples",len(samples))
            fig=go.Figure()
            fig.add_trace(go.Scattergl(x=samples[:2000].real,y=samples[:2000].imag,
                                       mode="markers",marker=dict(size=3,opacity=.4)))
            fig.update_layout(xaxis_title="I",yaxis_title="Q",height=400,yaxis_scaleanchor="x")
            st.plotly_chart(fig,use_container_width=True)
        st.markdown("#### Spectrum and waterfall")
        frequency,db=iq_spectrum(samples,rate)
        fig=go.Figure(go.Scatter(x=frequency,y=db,mode="lines"))
        fig.update_layout(xaxis_title="Offset frequency (Hz)",
                          yaxis_title="dB re complex amplitude 1")
        st.plotly_chart(fig,use_container_width=True)
        size=st.selectbox("Waterfall FFT bins",[128,256,512,1024],index=1)
        if len(samples)>=size:
            time,freq,values=waterfall(samples,rate,size)
            fig=go.Figure(go.Heatmap(x=time,y=freq,z=values,
                                     colorscale="Viridis",colorbar=dict(title="dB")))
            fig.update_layout(xaxis_title="Time (s)",yaxis_title="Offset frequency (Hz)")
            st.plotly_chart(fig,use_container_width=True)
        st.caption("Frequency axes are relative to the unknown IQ center frequency. "
                   "The amplitude scale is not calibrated dBm or power spectral density.")
    except ValueError as exc:
        st.error(str(exc))
