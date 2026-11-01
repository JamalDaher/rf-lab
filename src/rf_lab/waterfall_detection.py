"""Bounded, reproducible time-frequency detection for offline complex IQ."""
import math
import numpy as np
from rf_lab.sdr_lab import _validate_iq

def synthetic_activity_iq(rate=16000,duration=1.0,noise_db=-32,seed=42):
    if not isinstance(rate,(int,float)) or not math.isfinite(rate) or not 4000<=rate<=48000:
        raise ValueError("sample rate must be 4000–48000 Hz")
    if not isinstance(duration,(int,float)) or not math.isfinite(duration) or not .1<=duration<=2:
        raise ValueError("duration must be 0.1–2 s")
    n=round(rate*duration)
    if not 128<=n<=65536:
        raise ValueError("sample count must be 128–65536")
    if not isinstance(noise_db,(int,float)) or not math.isfinite(noise_db) or not -70<=noise_db<=0:
        raise ValueError("noise amplitude must be -70–0 dB")
    if type(seed)!=int or not 0<=seed<=2**32-1:
        raise ValueError("invalid seed")
    t=np.arange(n)/rate
    rng=np.random.default_rng(seed)
    noise=(rng.standard_normal(n)+1j*rng.standard_normal(n))/np.sqrt(2)
    # Two gated transmitters plus a chirp, all strictly within Nyquist.
    gate1=((t>=.15*duration)&(t<.55*duration)).astype(float)
    gate2=((t>=.55*duration)&(t<.9*duration)).astype(float)
    chirp_gate=((t>=.25*duration)&(t<.8*duration)).astype(float)
    chirp_phase=2*np.pi*(-rate*.2*t+rate*.3*t*t/(2*duration))
    return (gate1*np.exp(2j*np.pi*rate*.12*t)
            +.65*gate2*np.exp(-2j*np.pi*rate*.28*t)
            +.35*chirp_gate*np.exp(1j*chirp_phase)
            +10**(noise_db/20)*noise)

def analyze_waterfall(iq,rate,fft_size=256,overlap=50,window="Hann",
                      threshold_db=12,max_events=200):
    x=_validate_iq(iq)
    if not isinstance(rate,(int,float)) or not math.isfinite(rate) or rate<=0:
        raise ValueError("invalid sample rate")
    if type(fft_size)!=int or fft_size not in (128,256,512,1024,2048) or fft_size>len(x):
        raise ValueError("invalid FFT size")
    if overlap not in (0,50,75) or window not in ("Hann","Rectangular"):
        raise ValueError("invalid overlap or window")
    if not isinstance(threshold_db,(int,float)) or not math.isfinite(threshold_db) or not 3<=threshold_db<=60:
        raise ValueError("invalid detection threshold")
    if type(max_events)!=int or not 1<=max_events<=500:
        raise ValueError("invalid event limit")
    hop=max(1,fft_size*(100-overlap)//100)
    starts=np.arange(0,len(x)-fft_size+1,hop)
    if len(starts)>256:
        starts=starts[np.linspace(0,len(starts)-1,256,dtype=int)]
    w=np.hanning(fft_size) if window=="Hann" else np.ones(fft_size)
    scale=rate*np.sum(w*w)
    segments=np.stack([x[s:s+fft_size] for s in starts])
    power=np.abs(np.fft.fftshift(np.fft.fft(segments*w,axis=1),axes=1))**2/scale
    db=10*np.log10(np.maximum(power,1e-20))
    freq=np.fft.fftshift(np.fft.fftfreq(fft_size,1/rate))
    times=(starts+fft_size/2)/rate
    # Robust global median floor; threshold applies to local time-frequency maxima.
    floor=float(np.median(db))
    above=db>=floor+threshold_db
    # Require local spectral maximum and reject isolated single-frame noise hits.
    maxima=np.zeros_like(above,dtype=bool)
    maxima[:,1:-1]=(above[:,1:-1] & (db[:,1:-1]>=db[:,:-2])
                     & (db[:,1:-1]>db[:,2:]))
    # Group consecutive time slices at nearby bins into one activity event.
    active={}
    events=[]
    for ti in range(len(times)):
        indices=np.flatnonzero(maxima[ti])
        matched=set()
        for fi in indices:
            possible=[k for k,v in active.items() if abs(v["bin"]-int(fi))<=2 and k not in matched]
            if possible:
                k=min(possible,key=lambda k:abs(active[k]["bin"]-int(fi)))
                event=active[k]
                event["last"]=ti
                if db[ti,fi]>event["peak_db_hz"]:
                    event["peak_db_hz"]=float(db[ti,fi])
                    event["bin"]=int(fi)
                matched.add(k)
            else:
                k=(ti,int(fi))
                active[k]={"first":ti,"last":ti,"bin":int(fi),
                           "peak_db_hz":float(db[ti,fi])}
                matched.add(k)
        for k in list(active):
            if k not in matched:
                event=active.pop(k)
                if event["last"]>event["first"]:
                    events.append(event)
    events.extend(e for e in active.values() if e["last"]>e["first"])
    events.sort(key=lambda e:e["peak_db_hz"],reverse=True)
    out=[{"frequency_hz":float(freq[e["bin"]]),
          "start_s":float(max(0,times[e["first"]]-fft_size/(2*rate))),
          "end_s":float(min(len(x)/rate,times[e["last"]]+fft_size/(2*rate))),
          "peak_db_hz":e["peak_db_hz"],
          "above_floor_db":float(e["peak_db_hz"]-floor)}
         for e in events[:max_events]]
    return {"time_s":times,"frequency_hz":freq,"power_db_hz":db.T,
            "noise_floor_db_hz":floor,"events":out,
            "activity_frames":int(np.count_nonzero(np.any(above,axis=1))),
            "total_frames":len(times),"resolution_hz":float(rate/fft_size)}
