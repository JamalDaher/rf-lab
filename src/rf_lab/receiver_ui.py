"""Streamlit controls for the offline SDR receiver pipeline."""
import io
import csv
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from rf_lab.sdr_lab import read_iq_bytes,iq_spectrum
from rf_lab.receiver import synthetic_receiver_iq,receiver_pipeline,export_complex64
from rf_lab.receiver_audio import prepare_audio,wav_bytes

def render():
    st.caption("Offline AM/FM IQ processing · playback and WAV export · no live SDR hardware")
    source=st.radio("Signal source",["Synthetic AM/FM","Recorded IQ"],horizontal=True,key="rx_source")
    left,right=st.columns(2)
    with left:
        rate=st.selectbox("Sample rate (Hz)",[8000,16000,48000],index=1,key="rx_rate") if source=="Synthetic AM/FM" else st.number_input("Sample rate (Hz)",min_value=1.0,max_value=100000000.0,value=16000.0,key="rx_import_rate")
    with right:
        demod=st.selectbox("Demodulation",["AM","FM"],key="rx_demod")
    if source=="Synthetic AM/FM":
        a,b=st.columns(2)
        with a:
            offset=st.slider("Carrier offset (Hz)",-3000,3000,2000,100,key="rx_offset")
            tone=st.slider("Modulating tone (Hz)",50,1000,200,50,key="rx_tone")
        with b:
            depth=st.slider("AM depth / FM index",0.0,1.0,0.5,0.05,key="rx_depth")
            duration=st.slider("Duration (s)",0.05,1.0,0.25,0.05,key="rx_duration")
        try:
            iq=synthetic_receiver_iq(demod,rate,duration,offset,tone,depth)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.caption("Synthetic input uses the selected demodulation type and carrier offset.")
    else:
        fmt=st.selectbox("IQ encoding",["complex64","cs8"],key="rx_format")
        uploaded=st.file_uploader("Recorded IQ file (max 512 KiB)",type=["iq","bin","raw","cfile"],key="rx_upload")
        if uploaded is None:
            st.info("Upload an IQ recording to configure the receiver.")
            return
        try:
            iq=read_iq_bytes(uploaded.getvalue(),fmt)
        except ValueError as exc:
            st.error(str(exc))
            return
    st.markdown("#### Receiver chain")
    max_tune=int(rate//2)-1
    tune=st.slider("Tune offset (Hz)",-max_tune,max_tune,
                   int(offset) if source=="Synthetic AM/FM" else 0,step=1,key="rx_tune")
    use_filter=st.checkbox("Enable FIR filter",value=True,key="rx_filter")
    filter_mode=st.selectbox("FIR type",["lowpass","highpass"],key="rx_filter_mode",disabled=not use_filter)
    cutoff=st.slider("Cutoff (Hz)",min_value=10,max_value=max(11,int(rate//2)-1),
                     value=min(1500,max(11,int(rate//2)-1)),step=1,key="rx_cutoff",disabled=not use_filter)
    try:
        stages=receiver_pipeline(iq,rate,tune,cutoff if use_filter else None,filter_mode,demod)
        a,b,c=st.columns(3)
        a.metric("IQ samples",len(iq))
        b.metric("Tuning offset",f"{tune:g} Hz")
        c.metric("Audio RMS",f"{np.sqrt(np.mean(stages['demodulated']**2)):.4f}")
        view=st.tabs(["IQ processing stages","Demodulated signal","Processed spectrum","Audio playback","Export"])
        with view[0]:
            for name in ("input","tuned","filtered"):
                st.markdown(f"**{name.title()} IQ**")
                fig=go.Figure()
                n=min(1200,len(iq))
                t=np.arange(n)/rate*1000
                fig.add_trace(go.Scatter(x=t,y=stages[name][:n].real,mode="lines",name="I"))
                fig.add_trace(go.Scatter(x=t,y=stages[name][:n].imag,mode="lines",name="Q"))
                fig.update_layout(xaxis_title="Time (ms)",yaxis_title="Amplitude",height=260)
                st.plotly_chart(fig,use_container_width=True)
        with view[1]:
            fig=go.Figure(go.Scatter(x=np.arange(len(iq))/rate,
                                     y=stages["demodulated"],mode="lines"))
            fig.update_layout(xaxis_title="Time (s)",yaxis_title="Demodulated amplitude")
            st.plotly_chart(fig,use_container_width=True)
            st.caption("FM output is instantaneous frequency in Hz. AM output is DC-removed envelope. "
                       "These are uncalibrated traces, not speaker-ready audio.")
        with view[2]:
            for name in ("input","filtered"):
                f,db=iq_spectrum(stages[name],rate)
                fig=go.Figure(go.Scatter(x=f,y=db,mode="lines"))
                fig.update_layout(title=name.title(),xaxis_title="Baseband offset (Hz)",
                                  yaxis_title="dB re amplitude 1",height=280)
                st.plotly_chart(fig,use_container_width=True)
        with view[3]:
            st.markdown("#### Recovered audio")
            agc=st.checkbox("Automatic gain control",value=True,key="rx_audio_agc")
            deemp=st.checkbox("FM de-emphasis (75 µs)",value=demod=="FM",
                               disabled=demod!="FM",key="rx_audio_deemp")
            filtering=st.checkbox("Audio low-pass",value=True,key="rx_audio_filter")
            maximum=max(101,min(7000,int(rate/2)-1))
            cutoff=st.slider("Audio cutoff (Hz)",100,maximum,min(3000,maximum),
                             key="rx_audio_cutoff",disabled=not filtering)
            playback_rate=st.selectbox("Playback sample rate (Hz)",[8000,16000,24000,48000],
                                       index=1,key="rx_playback_rate")
            try:
                audio,actual_rate=prepare_audio(
                    stages["demodulated"],rate,demod,use_deemphasis=deemp and demod=="FM",
                    use_agc=agc,cutoff_hz=cutoff if filtering else None,
                    output_rate=playback_rate)
                wav=wav_bytes(audio,actual_rate)
                st.audio(wav,format="audio/wav")
                st.download_button("Download recovered audio (WAV)",wav,
                                   file_name="rf-lab-recovered-audio.wav",mime="audio/wav")
                st.caption("Mono 16-bit PCM; linear resampling is educational and may alias "
                           "when downsampling high-rate recordings.")
            except ValueError as exc:
                st.error(f"Audio processing unavailable: {exc}")
        with view[4]:
            st.download_button("Download processed IQ (complex64)",
                               export_complex64(stages["filtered"]),
                               file_name="rf-lab-receiver-iq.cfile",mime="application/octet-stream")
            output=io.StringIO()
            writer=csv.writer(output)
            writer.writerow(["time_s","demodulated"])
            writer.writerows(zip(np.arange(len(iq))/rate,stages["demodulated"]))
            st.download_button("Download demodulated CSV",output.getvalue(),
                               file_name="rf-lab-demodulated.csv",mime="text/csv")
        st.warning("This is an illustrative offline receiver. FIR startup transients, frequency "
                   "offset, sampling and missing carrier/timing recovery affect results.")
    except ValueError as exc:
        st.error(str(exc))
