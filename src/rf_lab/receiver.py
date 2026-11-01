"""Bounded, offline SDR receiver DSP building blocks.

All frequencies are baseband offsets, not absolute RF frequencies.
"""
import math
import numpy as np
from rf_lab.sdr_lab import _validate_iq, MAX_IQ_SAMPLES

def _rate(rate):
    if not isinstance(rate,(int,float)) or not math.isfinite(rate) or rate<=0:
        raise ValueError("sample rate must be positive and finite")
    return float(rate)

def frequency_shift(iq,sample_rate_hz,shift_hz):
    x=_validate_iq(iq)
    rate=_rate(sample_rate_hz)
    if not isinstance(shift_hz,(int,float)) or not math.isfinite(shift_hz) or abs(shift_hz)>=rate/2:
        raise ValueError("frequency shift must be inside Nyquist")
    return x*np.exp(-2j*np.pi*shift_hz*np.arange(len(x))/rate)

def fir_filter(iq,sample_rate_hz,cutoff_hz,mode="lowpass",taps=101):
    x=_validate_iq(iq)
    rate=_rate(sample_rate_hz)
    if not isinstance(cutoff_hz,(int,float)) or not math.isfinite(cutoff_hz) or not 0<cutoff_hz<rate/2:
        raise ValueError("cutoff must be inside Nyquist")
    if mode not in ("lowpass","highpass") or type(taps)!=int or taps<3 or taps>501 or taps%2!=1:
        raise ValueError("invalid filter mode or tap count")
    k=np.arange(taps)-(taps-1)//2
    h=2*cutoff_hz/rate*np.sinc(2*cutoff_hz/rate*k)*np.hamming(taps)
    h/=h.sum()
    if mode=="highpass":
        h=-h
        h[taps//2]+=1
    # Crop the full convolution to the original sample count even for short recordings.
    full=np.convolve(x,h,mode="full")
    start=(taps-1)//2
    return full[start:start+len(x)]

def bandpass(iq,sample_rate_hz,low_hz,high_hz,taps=101):
    rate=_rate(sample_rate_hz)
    if not isinstance(low_hz,(int,float)) or not isinstance(high_hz,(int,float)) or not 0<low_hz<high_hz<rate/2:
        raise ValueError("band edges must satisfy 0 < low < high < Nyquist")
    return fir_filter(iq,rate,high_hz,taps=taps)-fir_filter(iq,rate,low_hz,taps=taps)

def am_demodulate(iq):
    x=_validate_iq(iq)
    envelope=np.abs(x)
    return envelope-np.mean(envelope)

def fm_demodulate(iq,sample_rate_hz):
    x=_validate_iq(iq)
    rate=_rate(sample_rate_hz)
    phase=np.angle(x[1:]*np.conj(x[:-1]))
    return np.r_[0.,phase*rate/(2*np.pi)]

def export_complex64(iq):
    x=_validate_iq(iq)
    packed=np.column_stack((x.real,x.imag)).astype("<f4")
    if not np.all(np.isfinite(packed)):
        raise ValueError("IQ exceeds float32 range")
    return packed.tobytes()

def synthetic_receiver_iq(mode="AM",sample_rate_hz=16000,duration_s=.25,
                          carrier_offset_hz=2000,audio_hz=200,depth=.5):
    rate=_rate(sample_rate_hz)
    if mode not in ("AM","FM") or not isinstance(duration_s,(int,float)) or not math.isfinite(duration_s):
        raise ValueError("invalid synthetic mode or duration")
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (carrier_offset_hz,audio_hz,depth)):
        raise ValueError("parameters must be finite")
    n=round(rate*duration_s)
    if not 32<=n<=MAX_IQ_SAMPLES or not 0<audio_hz<rate/2 or not 0<=depth<=1 or abs(carrier_offset_hz)>=rate/2:
        raise ValueError("invalid synthetic signal parameters")
    t=np.arange(n)/rate
    if mode=="AM":
        return (1+depth*np.cos(2*np.pi*audio_hz*t))*np.exp(2j*np.pi*carrier_offset_hz*t)
    if abs(carrier_offset_hz)+depth*audio_hz>=rate/2:
        raise ValueError("FM excursion would exceed Nyquist")
    return np.exp(1j*(2*np.pi*carrier_offset_hz*t+depth*np.sin(2*np.pi*audio_hz*t)))

def receiver_pipeline(iq,sample_rate_hz,tune_hz=0,cutoff_hz=None,filter_mode="lowpass",
                      demodulation="AM"):
    rate=_rate(sample_rate_hz)
    stages={"input":_validate_iq(iq).copy()}
    stages["tuned"]=frequency_shift(stages["input"],rate,tune_hz)
    stages["filtered"]=(fir_filter(stages["tuned"],rate,cutoff_hz,filter_mode)
                         if cutoff_hz is not None else stages["tuned"].copy())
    if demodulation=="AM":
        audio=am_demodulate(stages["filtered"])
    elif demodulation=="FM":
        audio=fm_demodulate(stages["filtered"],rate)
    else:
        raise ValueError("demodulation must be AM or FM")
    stages["demodulated"]=audio
    return stages
