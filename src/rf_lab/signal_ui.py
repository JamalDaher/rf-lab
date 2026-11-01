"""Streamlit presentation for synthetic signal experiments."""
import csv
import io
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from rf_lab.signal_analysis import generate_signal,spectrum,analyze_signal,lowpass

def render():
    st.caption("Synthetic AM/FM/CW waveforms · educational simulation, not live SDR data")
    a,b,c=st.columns(3)
    with a:
        mode=st.selectbox("Modulation",["AM","FM","CW"])
        carrier=st.number_input("Carrier (Hz)",100.0,20000.0,1000.0,100.0)
    with b:
        tone=st.number_input("Modulation tone (Hz)",1.0,10000.0,100.0)
        depth=st.slider("AM depth / FM index",0.0,1.0,0.5,0.05)
    with c:
        rate=st.selectbox("Sample rate (samples/s)",[8000,16000,48000],index=1)
        duration=st.slider("Duration (s)",0.02,1.0,0.2,0.02)
    noise=st.checkbox("Add Gaussian noise")
    snr=st.slider("Requested SNR (dB)",-10,60,20) if noise else None
    window=st.selectbox("FFT window",["hann","rectangular"])
    filtering=st.checkbox("Apply low-pass FIR filter")
    cutoff=st.slider("FIR cutoff (Hz)",100,rate//2-100,min(1800,rate//2-100),100) if filtering else None
    try:
        t,y,clean=generate_signal(mode,carrier,tone,rate,duration,depth,snr)
        output=lowpass(y,rate,cutoff) if filtering else y
        m=analyze_signal(output,rate,window)
        f,amplitude,db=spectrum(output,rate,window)
        cols=st.columns(4)
        for col,label,value in zip(cols,["Dominant bin","RMS amplitude","Peak amplitude","FFT resolution"],
                                   [f"{m['dominant_frequency_hz']:.1f} Hz",f"{m['rms']:.4f}",
                                    f"{m['peak']:.4f}",f"{m['frequency_resolution_hz']:.2f} Hz"]):
            col.metric(label,value)
        wave,spec,exports=st.tabs(["Waveform","Spectrum","Export & details"])
        with wave:
            fig=go.Figure()
            n=min(len(t),1500)
            fig.add_trace(go.Scatter(x=t[:n]*1000,y=output[:n],name="Output",mode="lines"))
            if noise or filtering:
                fig.add_trace(go.Scatter(x=t[:n]*1000,y=clean[:n],name="Clean reference",
                                         mode="lines",line=dict(dash="dot")))
            fig.update_layout(xaxis_title="Time (ms)",yaxis_title="Normalized amplitude")
            st.plotly_chart(fig,use_container_width=True)
        with spec:
            fig=go.Figure(go.Scatter(x=f,y=db,mode="lines",name="FFT amplitude"))
            fig.update_layout(xaxis_title="Frequency (Hz)",yaxis_title="dB re amplitude 1",
                              xaxis_range=[0,min(rate/2,max(carrier*2.5,carrier+6*tone))])
            st.plotly_chart(fig,use_container_width=True)
            st.caption("One-sided window-corrected amplitude spectrum; not calibrated dBm or PSD.")
        with exports:
            st.json({"modulation":mode,"carrier_hz":carrier,"tone_hz":tone,
                     "depth_or_fm_index":depth,"requested_snr_db":snr,
                     "fir_cutoff_hz":cutoff,"window":window,**m})
            for label,filename,header,rows in [
                ("Download waveform CSV","rf-lab-waveform.csv",
                 ["time_s","output_amplitude","clean_amplitude"],zip(t,output,clean)),
                ("Download spectrum CSV","rf-lab-spectrum.csv",
                 ["frequency_hz","amplitude","db_re_1"],zip(f,amplitude,db))]:
                stream=io.StringIO()
                writer=csv.writer(stream)
                writer.writerow(header)
                writer.writerows(rows)
                st.download_button(label,stream.getvalue(),file_name=filename,mime="text/csv")
        st.info("All waveforms are synthetic. FM index sets peak deviation = index × tone frequency. "
                "Finite FFT resolution and FIR transients affect measurements.")
    except ValueError as exc:
        st.error(str(exc))
