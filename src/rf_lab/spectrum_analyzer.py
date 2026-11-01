"""Offline, bounded complex-IQ spectrum measurements.

PSD is expressed in dB relative to 1 sample-power unit per Hz (dB/Hz).
Measurements are estimates; absolute dBm requires receiver calibration.
"""
import math
import numpy as np
from rf_lab.sdr_lab import _validate_iq

def synthetic_spectrum_iq(rate=16000, duration=.5, tone_hz=1800,
                          second_hz=-2800, noise_db=-28, seed=42):
    if not isinstance(rate,(int,float)) or not math.isfinite(rate) or not 2000<=rate<=192000:
        raise ValueError("sample rate must be 2000–192000 Hz")
    if not isinstance(duration,(int,float)) or not math.isfinite(duration) or not .05<=duration<=2:
        raise ValueError("duration must be 0.05–2 s")
    n=int(round(rate*duration))
    if not 32<=n<=65536:
        raise ValueError("sample count must be 32–65536")
    if any(not isinstance(f,(int,float)) or not math.isfinite(f) or abs(f)>=rate/2
           for f in (tone_hz,second_hz)):
        raise ValueError("tones must be within Nyquist")
    if not isinstance(noise_db,(int,float)) or not math.isfinite(noise_db) or not -70<=noise_db<=0:
        raise ValueError("noise amplitude must be -70–0 dB")
    if type(seed)!=int or not 0<=seed<=2**32-1:
        raise ValueError("invalid seed")
    t=np.arange(n)/rate
    rng=np.random.default_rng(seed)
    noise=(rng.standard_normal(n)+1j*rng.standard_normal(n))/np.sqrt(2)
    return (np.exp(2j*np.pi*tone_hz*t)+.3*np.exp(2j*np.pi*second_hz*t)
            +10**(noise_db/20)*noise)

def analyze_spectrum(iq, sample_rate_hz, fft_size=1024, overlap_percent=50,
                     window="Hann", peak_threshold_db=10, max_peaks=8):
    x=_validate_iq(iq)
    if not isinstance(sample_rate_hz,(int,float)) or not math.isfinite(sample_rate_hz) or sample_rate_hz<=0:
        raise ValueError("invalid sample rate")
    if type(fft_size)!=int or fft_size not in (128,256,512,1024,2048,4096):
        raise ValueError("invalid FFT size")
    if fft_size>len(x):
        raise ValueError("FFT size exceeds recording length")
    if overlap_percent not in (0,50,75) or window not in ("Hann","Rectangular"):
        raise ValueError("invalid overlap or window")
    if not isinstance(peak_threshold_db,(int,float)) or not math.isfinite(peak_threshold_db) or not 0<=peak_threshold_db<=60:
        raise ValueError("invalid peak threshold")
    if type(max_peaks)!=int or not 1<=max_peaks<=20:
        raise ValueError("invalid maximum peaks")
    hop=max(1,int(fft_size*(100-overlap_percent)/100))
    starts=np.arange(0,len(x)-fft_size+1,hop)
    if len(starts)>256:
        starts=starts[np.linspace(0,len(starts)-1,256,dtype=int)]
    w=np.hanning(fft_size) if window=="Hann" else np.ones(fft_size)
    scale=sample_rate_hz*np.sum(w*w)
    # Welch: average linear power, then convert to dB.
    power=np.zeros(fft_size,dtype=float)
    for s in starts:
        transformed=np.fft.fft(x[s:s+fft_size]*w)
        power+=np.abs(transformed)**2/scale
    power/=len(starts)
    power=np.fft.fftshift(power)
    freq=np.fft.fftshift(np.fft.fftfreq(fft_size,d=1/sample_rate_hz))
    db=10*np.log10(np.maximum(power,1e-20))
    # Median is a robust *display* noise-floor estimate, not a calibrated sensitivity.
    floor=float(np.median(db))
    candidates=[]
    for i in range(1,len(db)-1):
        if db[i]>floor+peak_threshold_db and db[i]>=db[i-1] and db[i]>db[i+1]:
            candidates.append(i)
    candidates.sort(key=lambda i:db[i],reverse=True)
    peaks=[{"frequency_hz":float(freq[i]),"level_db_hz":float(db[i]),
            "above_floor_db":float(db[i]-floor)} for i in candidates[:max_peaks]]
    # Occupied bandwidth: smallest contiguous interval between cumulative 0.5%
    # and 99.5% integrated power (99% power, not emission-mask bandwidth).
    cumulative=np.cumsum(power)
    total=float(cumulative[-1])
    if total<=0:
        low=high=0.
    else:
        lo=int(np.searchsorted(cumulative,.005*total))
        hi=int(np.searchsorted(cumulative,.995*total))
        low=float(freq[min(lo,len(freq)-1)])
        high=float(freq[min(hi,len(freq)-1)])
    return {"frequency_hz":freq,"psd_db_hz":db,"noise_floor_db_hz":floor,
            "peaks":peaks,"occupied_bandwidth_hz":high-low,
            "occupied_low_hz":low,"occupied_high_hz":high,
            "resolution_hz":float(sample_rate_hz/fft_size),
            "segments_averaged":len(starts)}
