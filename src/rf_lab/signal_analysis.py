"""Deterministic, educational AM/FM signal and spectrum analysis.

All waveforms are synthetic baseband/IF examples, not SDR measurements.
"""
import math
import numpy as np

MAX_SAMPLES = 65536

def generate_signal(modulation="AM",carrier_hz=1000.0,tone_hz=100.0,
                    sample_rate_hz=10000.0,duration_s=0.1,depth=0.5,
                    noise_snr_db=None,seed=42):
    if modulation not in ("AM","FM","CW"):
        raise ValueError("modulation must be AM, FM or CW")
    values=(carrier_hz,tone_hz,sample_rate_hz,duration_s,depth)
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in values):
        raise ValueError("signal parameters must be finite")
    if not (0<carrier_hz<sample_rate_hz/2 and 0<tone_hz<sample_rate_hz/2
            and 0<duration_s and 0<=depth<=1):
        raise ValueError("invalid frequency, duration or modulation depth")
    if modulation=="FM" and carrier_hz+depth*tone_hz>=sample_rate_hz/2:
        raise ValueError("FM deviation would exceed Nyquist")
    n=round(sample_rate_hz*duration_s)
    if not 32<=n<=MAX_SAMPLES:
        raise ValueError("sample count must be between 32 and 65536")
    t=np.arange(n,dtype=float)/sample_rate_hz
    phase=2*np.pi*carrier_hz*t
    if modulation=="AM":
        clean=(1+depth*np.cos(2*np.pi*tone_hz*t))*np.cos(phase)
    elif modulation=="FM":
        # depth is the modulation index beta; peak deviation = beta*tone_hz.
        clean=np.cos(phase+depth*np.sin(2*np.pi*tone_hz*t))
    else:
        clean=np.cos(phase)
    signal=clean.copy()
    if noise_snr_db is not None:
        if type(noise_snr_db) not in (int,float) or not math.isfinite(noise_snr_db) or not -20<=noise_snr_db<=100:
            raise ValueError("SNR must be between -20 and 100 dB")
        rng=np.random.default_rng(seed)
        noise=rng.normal(size=n)
        noise-=np.mean(noise)
        rms=np.sqrt(np.mean(noise**2))
        noise*=np.sqrt(np.mean(clean**2))/(10**(noise_snr_db/20)*rms)
        signal+=noise
    return t,signal,clean

def spectrum(signal,sample_rate_hz,window="hann"):
    y=np.asarray(signal,dtype=float)
    if y.ndim!=1 or not 32<=y.size<=MAX_SAMPLES or not np.all(np.isfinite(y)):
        raise ValueError("signal must be a finite 1D vector of 32–65536 samples")
    if type(sample_rate_hz) not in (float,int) or not math.isfinite(sample_rate_hz) or sample_rate_hz<=0:
        raise ValueError("invalid sample rate")
    if window not in ("hann","rectangular"):
        raise ValueError("unsupported window")
    w=np.hanning(len(y)) if window=="hann" else np.ones(len(y))
    fft=np.fft.rfft(y*w)
    amplitude=np.abs(fft)*2/np.sum(w)
    amplitude[0]*=0.5
    if len(y)%2==0:
        amplitude[-1]*=0.5
    freq=np.fft.rfftfreq(len(y),1/sample_rate_hz)
    db=20*np.log10(np.maximum(amplitude,1e-12))
    return freq,amplitude,db

def analyze_signal(signal,sample_rate_hz,window="hann"):
    y=np.asarray(signal,dtype=float)
    f,amplitude,db=spectrum(y,sample_rate_hz,window)
    peak=int(np.argmax(amplitude[1:])+1)
    rms=float(np.sqrt(np.mean(y**2)))
    return {"sample_count":len(y),"sample_rate_hz":float(sample_rate_hz),
            "rms":rms,"peak":float(np.max(np.abs(y))),
            "dominant_frequency_hz":float(f[peak]),
            "frequency_resolution_hz":float(sample_rate_hz/len(y))}

def lowpass(signal,sample_rate_hz,cutoff_hz):
    """Windowed-sinc FIR filter; educational, not a calibrated receiver."""
    y=np.asarray(signal,dtype=float)
    if y.ndim!=1 or not 32<=len(y)<=MAX_SAMPLES or not np.all(np.isfinite(y)):
        raise ValueError("invalid signal")
    if not math.isfinite(sample_rate_hz) or not math.isfinite(cutoff_hz) or not 0<cutoff_hz<sample_rate_hz/2:
        raise ValueError("cutoff must be below Nyquist")
    taps=101
    k=np.arange(taps)-(taps-1)/2
    h=2*cutoff_hz/sample_rate_hz*np.sinc(2*cutoff_hz/sample_rate_hz*k)*np.hamming(taps)
    h/=np.sum(h)
    return np.convolve(y,h,mode="same")
