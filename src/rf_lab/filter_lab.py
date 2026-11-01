"""Windowed-sinc FIR filters for offline complex-baseband experiments."""
import math
import numpy as np
from rf_lab.sdr_lab import _validate_iq

KINDS=("Low-pass","High-pass","Band-pass","Notch")

def _lowpass(cutoff,rate,taps):
    n=np.arange(taps)-(taps-1)/2
    h=2*cutoff/rate*np.sinc(2*cutoff*n/rate)*np.hamming(taps)
    return h/h.sum()

def design_filter(kind,rate,low_hz,high_hz=None,taps=101):
    if kind not in KINDS:
        raise ValueError("unsupported filter type")
    if not isinstance(rate,(int,float)) or not math.isfinite(rate) or rate<=0:
        raise ValueError("sample rate must be finite and positive")
    if type(taps)!=int or taps<11 or taps>501 or taps%2!=1:
        raise ValueError("tap count must be odd and between 11 and 501")
    if not isinstance(low_hz,(int,float)) or not math.isfinite(low_hz) or not 0<low_hz<rate/2:
        raise ValueError("cutoff must be inside Nyquist")
    if kind in ("Band-pass","Notch"):
        if not isinstance(high_hz,(int,float)) or not math.isfinite(high_hz) or not low_hz<high_hz<rate/2:
            raise ValueError("band edges must be increasing and below Nyquist")
    impulse=np.zeros(taps)
    impulse[taps//2]=1.0
    if kind=="Low-pass":
        h=_lowpass(low_hz,rate,taps)
    elif kind=="High-pass":
        h=impulse-_lowpass(low_hz,rate,taps)
    else:
        band=_lowpass(high_hz,rate,taps)-_lowpass(low_hz,rate,taps)
        h=band if kind=="Band-pass" else impulse-band
    return np.asarray(h,dtype=float)

def frequency_response(taps,rate,points=2048):
    h=np.asarray(taps,dtype=float)
    if h.ndim!=1 or len(h)<11 or not np.all(np.isfinite(h)):
        raise ValueError("invalid filter coefficients")
    if not isinstance(rate,(int,float)) or not math.isfinite(rate) or rate<=0:
        raise ValueError("invalid sample rate")
    if type(points)!=int or not 512<=points<=8192:
        raise ValueError("invalid response resolution")
    response=np.fft.fftshift(np.fft.fft(h,points))
    freq=np.fft.fftshift(np.fft.fftfreq(points,1/rate))
    return {"frequency_hz":freq,
            "gain_db":20*np.log10(np.maximum(np.abs(response),1e-12)),
            "phase_rad":np.angle(response),
            "group_delay_samples":(len(h)-1)/2}

def apply_filter(iq,taps):
    x=_validate_iq(iq)
    h=np.asarray(taps,dtype=float)
    if h.ndim!=1 or len(h)<11 or len(h)>501 or len(h)%2!=1 or not np.all(np.isfinite(h)):
        raise ValueError("invalid filter taps")
    # Centered convolution compensates FIR group delay, with zero-padded boundaries.
    return np.convolve(x,h,mode="same") if len(x)>=len(h) else np.convolve(x,h,mode="full")[(len(h)-1)//2:(len(h)-1)//2+len(x)]

def filter_report(kind,rate,low_hz,high_hz,taps,response):
    return {"schema_version":1,"type":kind,"sample_rate_hz":float(rate),
            "lower_edge_hz":float(low_hz),
            "upper_edge_hz":float(high_hz) if high_hz is not None else None,
            "taps":int(len(taps)),"group_delay_samples":float(response["group_delay_samples"]),
            "coefficients":[float(v) for v in taps],
            "limitations":"FIR windowed-sinc approximation; transition width and stopband attenuation depend on tap count."}
