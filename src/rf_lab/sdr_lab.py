"""Synthetic complex-baseband digital modulation and bounded IQ imports.

No SDR device, transmitter or hardware integration is involved.
"""
import io
import math
import numpy as np

MAX_SYMBOLS=8192
MAX_IQ_SAMPLES=65536
MAX_FILE_BYTES=524288

def constellation(modulation):
    if modulation=="BPSK":
        return np.array([-1+0j,1+0j])
    if modulation=="QPSK":
        return np.array([-1-1j,-1+1j,1-1j,1+1j])/np.sqrt(2)
    if modulation=="16-QAM":
        return np.array([complex(i,q) for i in (-3,-1,1,3)
                         for q in (-3,-1,1,3)])/np.sqrt(10)
    raise ValueError("unsupported modulation")

def simulate(modulation="QPSK",symbols=1000,snr_db=20.0,seed=42):
    if type(symbols)!=int or not 16<=symbols<=MAX_SYMBOLS:
        raise ValueError("symbols must be 16–8192")
    if not isinstance(snr_db,(int,float)) or not math.isfinite(snr_db) or not -10<=snr_db<=60:
        raise ValueError("SNR must be finite and between -10 and 60 dB")
    points=constellation(modulation)
    rng=np.random.default_rng(seed)
    labels=rng.integers(0,len(points),size=symbols)
    transmitted=points[labels]
    noise=(rng.standard_normal(symbols)+1j*rng.standard_normal(symbols))*10**(-snr_db/20)/np.sqrt(2)
    received=transmitted+noise
    decisions=np.argmin(abs(received[:,None]-points[None,:])**2,axis=1)
    bits=int(round(np.log2(len(points))))
    bit_errors=sum((int(a)^int(b)).bit_count() for a,b in zip(labels,decisions))
    error_vector=received-transmitted
    evm=float(np.sqrt(np.mean(abs(error_vector)**2)/np.mean(abs(transmitted)**2))*100)
    return {"transmitted":transmitted,"received":received,"labels":labels,
            "decisions":decisions,"ber":bit_errors/(symbols*bits),
            "ser":float(np.mean(labels!=decisions)),"evm_percent":evm,
            "measured_snr_db":float(10*np.log10(np.mean(abs(transmitted)**2)/
                                               np.mean(abs(error_vector)**2)))}

def iq_spectrum(samples,sample_rate_hz):
    x=_validate_iq(samples)
    if not isinstance(sample_rate_hz,(int,float)) or not math.isfinite(sample_rate_hz) or sample_rate_hz<=0:
        raise ValueError("invalid sample rate")
    window=np.hanning(len(x))
    values=np.fft.fftshift(np.fft.fft(x*window))
    frequency=np.fft.fftshift(np.fft.fftfreq(len(x),1/sample_rate_hz))
    db=20*np.log10(np.maximum(abs(values)/np.sum(window),1e-12))
    return frequency,db

def waterfall(samples,sample_rate_hz,fft_size=256,hop=128):
    x=_validate_iq(samples)
    if fft_size not in (128,256,512,1024) or type(hop)!=int or hop<=0:
        raise ValueError("invalid STFT configuration")
    if len(x)<fft_size:
        raise ValueError("not enough IQ samples")
    starts=np.arange(0,len(x)-fft_size+1,hop)
    if len(starts)>512:
        starts=starts[np.linspace(0,len(starts)-1,512,dtype=int)]
    window=np.hanning(fft_size)
    segments=np.stack([x[s:s+fft_size] for s in starts])
    transformed=np.fft.fftshift(np.fft.fft(segments*window,axis=1),axes=1)
    db=20*np.log10(np.maximum(abs(transformed)/np.sum(window),1e-12))
    frequencies=np.fft.fftshift(np.fft.fftfreq(fft_size,1/sample_rate_hz))
    return starts/sample_rate_hz,frequencies,db.T

def _validate_iq(samples):
    x=np.asarray(samples,dtype=complex)
    if x.ndim!=1 or not 32<=len(x)<=MAX_IQ_SAMPLES or not np.all(np.isfinite(x)):
        raise ValueError("IQ must contain 32–65536 finite complex samples")
    return x

def read_iq_bytes(data,format="complex64"):
    """Read little-endian interleaved float32 I,Q or signed 8-bit I,Q."""
    if not isinstance(data,bytes) or not 0<len(data)<=MAX_FILE_BYTES:
        raise ValueError("IQ file must be nonempty and at most 512 KiB")
    if format=="complex64":
        if len(data)%8:
            raise ValueError("complex64 file size must be divisible by 8")
        x=np.frombuffer(data,dtype="<f4").reshape(-1,2)
        samples=x[:,0].astype(float)+1j*x[:,1].astype(float)
    elif format=="cs8":
        if len(data)%2:
            raise ValueError("signed 8-bit IQ file size must be divisible by 2")
        x=np.frombuffer(data,dtype=np.int8).reshape(-1,2)
        samples=x[:,0].astype(float)/128+1j*x[:,1].astype(float)/128
    else:
        raise ValueError("unsupported IQ format")
    return _validate_iq(samples).copy()
