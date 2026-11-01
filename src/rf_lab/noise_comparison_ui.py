"""Interactive AM/FM noise comparison lab."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from rf_lab.noise_comparison import compare_noise

def render():
    st.caption("Hear how additive white Gaussian noise affects AM and FM reception.")
    a,b,c=st.columns(3)
    with a:
        snr=st.slider("Channel SNR (dB)",-5,50,15,1,key="noise_snr")
    with b:
        tone=st.slider("Audio tone (Hz)",100,1000,300,50,key="noise_tone")
    with c:
        duration=st.slider("Signal duration (s)",.2,2.0,.8,.2,key="noise_duration")
    seed=st.number_input("Noise seed",min_value=0,max_value=100000,value=42,key="noise_seed")
    try:
        results=compare_noise(snr,tone,duration,int(seed))
        cols=st.columns(2)
        for col,mode in zip(cols,("AM","FM")):
            result=results[mode]
            with col:
                st.subheader(mode)
                st.metric("Recovered audio SNR",f"{result['audio_snr_db']:.1f} dB")
                st.caption("Clean reference")
                st.audio(result["clean_wav"],format="audio/wav")
                st.caption("With channel noise")
                st.audio(result["noisy_wav"],format="audio/wav")
                st.download_button(f"Download {mode} noisy WAV",result["noisy_wav"],
                                   file_name=f"rf-lab-{mode.lower()}-noise.wav",mime="audio/wav")
                n=min(800,len(result["noisy"]))
                fig=go.Figure()
                fig.add_trace(go.Scatter(x=np.arange(n)/16000,y=result["clean"][:n],
                                         name="Clean",mode="lines"))
                fig.add_trace(go.Scatter(x=np.arange(n)/16000,y=result["noisy"][:n],
                                         name="Noisy",mode="lines"))
                fig.update_layout(xaxis_title="Time (s)",yaxis_title="Normalized audio",
                                  height=300,margin=dict(l=20,r=20,t=25,b=25))
                st.plotly_chart(fig,use_container_width=True)
        st.markdown("#### Comparison")
        st.write(f"At {snr} dB nominal channel SNR, recovered audio SNR is "
                 f"{results['AM']['audio_snr_db']:.1f} dB for AM and "
                 f"{results['FM']['audio_snr_db']:.1f} dB for FM.")
        st.info("These are controlled, single-tone, complex-baseband AWGN experiments. "
                "AM and FM use the same nominal input SNR but different waveform powers "
                "and independent deterministic noise realizations. Audio SNR is measured "
                "against the corresponding clean demodulated reference after FIR settling. "
                "FM does not always outperform AM: performance depends on deviation, "
                "bandwidth, channel SNR and discriminator threshold effects. "
                "Playback uses a common per-mode clean/noisy scale without AGC.")
    except ValueError as exc:
        st.error(str(exc))
