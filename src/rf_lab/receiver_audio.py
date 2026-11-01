"""Audio post-processing and WAV export for bounded offline receiver samples."""
import io
import math
import wave
import numpy as np

def _audio(samples,rate):
    x=np.asarray(samples,dtype=float)
    if x.ndim!=1 or not 32<=len(x)<=65536 or not np.all(np.isfinite(x)):
        raise ValueError("audio must contain 32–65536 finite samples")
    if not isinstance(rate,(int,float)) or not math.isfinite(rate) or not 1000<=rate<=192000:
        raise ValueError("audio sample rate must be 1000–192000 Hz")
    return x,float(rate)

def automatic_gain_control(samples,rate,target_rms=.2,attack_ms=10,release_ms=150):
    """Causal envelope follower; slowly adapts gain with a bounded maximum."""
    x,rate=_audio(samples,rate)
    if not 0<target_rms<=.8 or not 0<attack_ms<=1000 or not 0<release_ms<=5000:
        raise ValueError("invalid AGC settings")
    attack=math.exp(-1/(rate*attack_ms/1000))
    release=math.exp(-1/(rate*release_ms/1000))
    envelope=0.
    output=np.empty_like(x)
    for i,s in enumerate(x):
        level=abs(s)
        alpha=attack if level>envelope else release
        envelope=alpha*envelope+(1-alpha)*level
        gain=min(20.,target_rms/max(envelope,1e-6))
        output[i]=s*gain
    return np.clip(output,-1.,1.)

def deemphasis(samples,rate,tau_us=75):
    """One-pole FM de-emphasis low-pass, 75 us or 50 us."""
    x,rate=_audio(samples,rate)
    if tau_us not in (50,75):
        raise ValueError("de-emphasis must be 50 or 75 microseconds")
    alpha=1-math.exp(-1/(rate*tau_us*1e-6))
    y=np.empty_like(x)
    prev=0.
    for i,v in enumerate(x):
        prev+=alpha*(v-prev)
        y[i]=prev
    return y

def audio_lowpass(samples,rate,cutoff_hz=3000,taps=101):
    x,rate=_audio(samples,rate)
    if not isinstance(cutoff_hz,(int,float)) or not math.isfinite(cutoff_hz) or not 0<cutoff_hz<rate/2:
        raise ValueError("audio cutoff must be inside Nyquist")
    if type(taps)!=int or not 3<=taps<=501 or taps%2!=1:
        raise ValueError("invalid audio FIR tap count")
    k=np.arange(taps)-(taps-1)//2
    h=2*cutoff_hz/rate*np.sinc(2*cutoff_hz/rate*k)*np.hamming(taps)
    h/=h.sum()
    full=np.convolve(x,h,mode="full")
    start=(taps-1)//2
    return full[start:start+len(x)]

def resample_audio(samples,input_rate,output_rate=16000):
    """Linear interpolation for offline listening; not a bandlimited resampler."""
    x,input_rate=_audio(samples,input_rate)
    if type(output_rate)!=int or not 1000<=output_rate<=48000:
        raise ValueError("output sample rate must be 1000–48000 Hz")
    count=int(round(len(x)*output_rate/input_rate))
    if not 32<=count<=262144:
        raise ValueError("resampled audio length out of bounds")
    times=np.arange(count)/output_rate
    return np.interp(times,np.arange(len(x))/input_rate,x),output_rate

def prepare_audio(samples,rate,modulation="AM",use_deemphasis=False,
                  use_agc=True,cutoff_hz=None,output_rate=16000):
    x,rate=_audio(samples,rate)
    if modulation not in ("AM","FM"):
        raise ValueError("unsupported demodulation")
    if use_deemphasis and modulation!="FM":
        raise ValueError("de-emphasis applies to FM only")
    x=x-np.mean(x)
    if use_deemphasis:
        x=deemphasis(x,rate)
    if cutoff_hz is not None:
        x=audio_lowpass(x,rate,cutoff_hz)
    # Normalize FM frequency-deviation units before applying optional AGC.
    peak=float(np.max(np.abs(x)))
    if peak>0:
        x=x/max(peak,1e-12)*.6
    if use_agc:
        x=automatic_gain_control(x,rate)
    x,playback_rate=resample_audio(x,rate,output_rate)
    return np.clip(x,-1.,1.),playback_rate

def wav_bytes(samples,rate):
    x,rate=_audio(samples,rate)
    if int(rate)!=rate or not 1000<=rate<=48000:
        raise ValueError("WAV rate must be integer and 1000–48000 Hz")
    pcm=np.round(np.clip(x,-1,1)*32767).astype("<i2")
    out=io.BytesIO()
    with wave.open(out,"wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(int(rate))
        wav.writeframes(pcm.tobytes())
    return out.getvalue()
