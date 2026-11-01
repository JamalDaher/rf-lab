"""Explainable heuristic signal-shape analysis, not a modulation decoder."""
import math
import numpy as np
from rf_lab.sdr_lab import _validate_iq

KINDS=("CW / narrow carrier","AM-like","FM-like","Digital-like")

def synthetic_classification_iq(kind="AM-like",rate=16000,duration=.5,snr_db=30,seed=42):
    if kind not in KINDS:
        raise ValueError("unknown signal type")
    if not isinstance(rate,(int,float)) or not math.isfinite(rate) or not 4000<=rate<=96000:
        raise ValueError("invalid sample rate")
    if not isinstance(duration,(int,float)) or not math.isfinite(duration) or not .1<=duration<=2:
        raise ValueError("invalid duration")
    n=int(rate*duration)
    if not 128<=n<=65536:
        raise ValueError("invalid sample count")
    if not isinstance(snr_db,(int,float)) or not math.isfinite(snr_db) or not -5<=snr_db<=60:
        raise ValueError("invalid SNR")
    if type(seed)!=int or not 0<=seed<=2**32-1:
        raise ValueError("invalid seed")
    t=np.arange(n)/rate
    if kind=="CW / narrow carrier":
        x=np.exp(2j*np.pi*.1*rate*t)
    elif kind=="AM-like":
        x=(1+.65*np.cos(2*np.pi*.008*rate*t))*np.exp(2j*np.pi*.1*rate*t)
    elif kind=="FM-like":
        x=np.exp(1j*(2*np.pi*.1*rate*t+4*np.sin(2*np.pi*.008*rate*t)))
    else:
        rng=np.random.default_rng(seed+1)
        symbol_rate=rate/64
        symbols=rng.choice([-1,1],size=int(np.ceil(n/64)))
        x=np.repeat(symbols,64)[:n].astype(complex)*np.exp(2j*np.pi*.1*rate*t)
    rng=np.random.default_rng(seed)
    noise=(rng.standard_normal(n)+1j*rng.standard_normal(n))/np.sqrt(2)
    return x+10**(-snr_db/20)*noise

def extract_features(iq,rate):
    x=_validate_iq(iq)
    if not isinstance(rate,(int,float)) or not math.isfinite(rate) or rate<=0:
        raise ValueError("invalid sample rate")
    power=np.abs(x)**2
    if np.mean(power)<1e-18:
        raise ValueError("signal power too low to classify")
    amplitude=np.abs(x)
    amp_cv=float(np.std(amplitude)/max(np.mean(amplitude),1e-12))
    # Phase increments measure frequency modulation after eliminating carrier offset.
    phase=np.angle(x[1:]*np.conj(x[:-1]))
    phase=np.unwrap(phase)
    freq_inst=phase*rate/(2*np.pi)
    freq_spread=float(np.std(freq_inst))
    n=min(4096,len(x))
    w=np.hanning(n)
    psd=np.abs(np.fft.fftshift(np.fft.fft(x[:n]*w)))**2
    freqs=np.fft.fftshift(np.fft.fftfreq(n,1/rate))
    total=float(np.sum(psd))
    p=psd/max(total,1e-30)
    peak_bin=int(np.argmax(psd))
    peak_fraction=float(np.max(p))
    cdf=np.cumsum(p)
    lo=int(np.searchsorted(cdf,.005))
    hi=int(np.searchsorted(cdf,.995))
    bandwidth=float(freqs[min(hi,n-1)]-freqs[min(lo,n-1)])
    centroid=float(np.sum(freqs*p))
    drift=float(np.std(np.diff(np.unwrap(np.angle(x))))*rate/(2*np.pi))
    return {"amplitude_cv":amp_cv,"instantaneous_frequency_std_hz":freq_spread,
            "occupied_bandwidth_hz":bandwidth,"spectral_peak_fraction":peak_fraction,
            "spectral_centroid_hz":centroid,"phase_step_spread_hz":drift,
            "frequency_resolution_hz":rate/n}

def classify_signal(iq,rate):
    f=extract_features(iq,rate)
    # Relative evidence scores; not statistical probabilities.
    cv=f["amplitude_cv"]
    spread=f["instantaneous_frequency_std_hz"]/rate
    bw=f["occupied_bandwidth_hz"]/rate
    concentration=f["spectral_peak_fraction"]
    evidence={
        "CW / narrow carrier":max(0,1-min(1,cv/.18))*max(0,1-min(1,spread/.03))*concentration,
        "AM-like":min(1,cv/.28)*max(0,1-min(1,spread/.07))*min(1,concentration*4),
        "FM-like":max(0,1-min(1,cv/.2))*min(1,spread/.025)*min(1,bw/.03),
        "Digital-like":min(1,max(0,spread-.02)/.08)*min(1,bw/.06)
    }
    total=sum(evidence.values())
    scores={k:float(v/total) if total>1e-12 else .25 for k,v in evidence.items()}
    ranked=sorted(scores,key=scores.get,reverse=True)
    explanations={
        "CW / narrow carrier":"Stable envelope and concentrated spectral energy support a carrier-like signal.",
        "AM-like":"Envelope variation with comparatively stable phase increments supports amplitude modulation.",
        "FM-like":"A nearly constant envelope with changing instantaneous frequency supports frequency modulation.",
        "Digital-like":"Broad spectral occupancy and abrupt phase/frequency variation can suggest digital modulation."
    }
    return {"label":ranked[0],"scores":scores,"features":f,
            "explanation":explanations[ranked[0]],
            "uncertain":scores[ranked[0]]<.55 or scores[ranked[0]]-scores[ranked[1]]<.15}
