"""Reproducible AM vs FM comparisons under identical complex AWGN conditions."""
import math
import numpy as np
from rf_lab.receiver import synthetic_receiver_iq,receiver_pipeline
from rf_lab.receiver_audio import prepare_audio,wav_bytes

def compare_noise(snr_db=15,tone_hz=300,duration_s=.5,seed=42,
                  rate=16000,carrier_hz=2000,depth=.6):
    if not isinstance(snr_db,(int,float)) or not math.isfinite(snr_db) or not -5<=snr_db<=50:
        raise ValueError("SNR must be between -5 and 50 dB")
    if type(seed)!=int or not 0<=seed<=2**32-1:
        raise ValueError("seed must be a 32-bit nonnegative integer")
    if not isinstance(tone_hz,(int,float)) or not math.isfinite(tone_hz) or not 50<=tone_hz<=1000:
        raise ValueError("tone must be 50–1000 Hz")
    if not isinstance(duration_s,(int,float)) or not math.isfinite(duration_s) or not .1<=duration_s<=2:
        raise ValueError("duration must be 0.1–2 seconds")
    rng=np.random.default_rng(seed)
    result={}
    for mode in ("AM","FM"):
        clean=synthetic_receiver_iq(mode,rate,duration_s,carrier_hz,tone_hz,depth)
        # Each mode gets its own noise realization with equal signal-relative SNR.
        signal_power=np.mean(abs(clean)**2)
        noise=(rng.standard_normal(len(clean))+1j*rng.standard_normal(len(clean)))
        noise*=np.sqrt(signal_power/(2*10**(snr_db/10)))
        noisy=clean+noise
        clean_audio=receiver_pipeline(clean,rate,carrier_hz,1500,demodulation=mode)["demodulated"]
        noisy_audio=receiver_pipeline(noisy,rate,carrier_hz,1500,demodulation=mode)["demodulated"]
        # Use identical clean-reference scale for both paths; avoid independently
        # normalizing the noise and concealing signal degradation.
        clean_audio=clean_audio[150:]
        noisy_audio=noisy_audio[150:]
        if mode=="FM":
            # The clean FM discriminator has a known constant frequency offset.
            clean_audio=clean_audio-np.mean(clean_audio)
            noisy_audio=noisy_audio-np.mean(noisy_audio)
        else:
            clean_audio=clean_audio-np.mean(clean_audio)
            noisy_audio=noisy_audio-np.mean(noisy_audio)
        signal=np.mean(clean_audio**2)
        error=np.mean((noisy_audio-clean_audio)**2)
        audio_snr=10*np.log10(signal/max(error,1e-20))
        # Preserve comparative amplitudes for listening, avoiding AGC.
        scale=max(np.max(abs(clean_audio)),np.max(abs(noisy_audio)),1e-12)
        clean_play=np.clip(clean_audio/scale*.8,-1,1)
        noisy_play=np.clip(noisy_audio/scale*.8,-1,1)
        result[mode]={"clean":clean_play,"noisy":noisy_play,
                      "audio_snr_db":float(audio_snr),
                      "input_snr_db":float(10*np.log10(signal_power/np.mean(abs(noise)**2))),
                      "clean_wav":wav_bytes(clean_play,rate),
                      "noisy_wav":wav_bytes(noisy_play,rate)}
    return result
