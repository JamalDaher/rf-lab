"""Tests for receiver audio post-processing and WAV output."""
import io
import wave
import numpy as np
import pytest
from rf_lab.receiver_audio import (automatic_gain_control,deemphasis,audio_lowpass,
                                   resample_audio,prepare_audio,wav_bytes)
from rf_lab.receiver import synthetic_receiver_iq,receiver_pipeline

def test_wav_header_and_frames():
    data=wav_bytes(np.sin(np.arange(1600)*2*np.pi*200/8000),8000)
    with wave.open(io.BytesIO(data),"rb") as w:
        assert w.getnchannels()==1
        assert w.getsampwidth()==2
        assert w.getframerate()==8000
        assert w.getnframes()==1600

def test_agc_bounded():
    x=np.r_[np.zeros(100),np.full(2000,.01)]
    y=automatic_gain_control(x,16000)
    assert np.isfinite(y).all()
    assert np.max(abs(y))<=1
    assert np.mean(abs(y[-100:]))>np.mean(abs(x[-100:]))

def test_deemphasis_reduces_high_frequency():
    t=np.arange(4096)/16000
    high=np.sin(2*np.pi*5000*t)
    low=np.sin(2*np.pi*100*t)
    assert np.std(deemphasis(high,16000))<np.std(deemphasis(low,16000))

def test_audio_lowpass():
    t=np.arange(4096)/16000
    x=np.sin(2*np.pi*200*t)+np.sin(2*np.pi*4000*t)
    y=audio_lowpass(x,16000,1000)
    assert np.mean(abs(y[200:-200]-np.sin(2*np.pi*200*t[200:-200])))<.1

def test_resample():
    t=np.arange(1600)/16000
    y,rate=resample_audio(np.sin(2*np.pi*200*t),16000,8000)
    assert rate==8000 and len(y)==800
    assert np.max(abs(y-np.sin(2*np.pi*200*np.arange(800)/8000)))<.01

@pytest.mark.parametrize("mode",["AM","FM"])
def test_end_to_end_audio(mode):
    iq=synthetic_receiver_iq(mode,16000,.25,2000,200,.5)
    stages=receiver_pipeline(iq,16000,2000,1500,demodulation=mode)
    audio,rate=prepare_audio(stages["demodulated"],16000,mode,
                              use_deemphasis=mode=="FM",cutoff_hz=1500)
    assert rate==16000
    assert np.all(np.isfinite(audio))
    assert len(wav_bytes(audio,rate))>1000

@pytest.mark.parametrize("fn",[
    lambda: automatic_gain_control(np.ones(64),16000,target_rms=2),
    lambda: deemphasis(np.ones(64),16000,tau_us=20),
    lambda: audio_lowpass(np.ones(64),16000,9000),
    lambda: resample_audio(np.ones(64),16000,999),
    lambda: prepare_audio(np.ones(64),16000,"AM",use_deemphasis=True),
    lambda: wav_bytes(np.ones(64),16000.5),
    lambda: wav_bytes(np.array([np.nan]*64),16000),
])
def test_invalid_audio_parameters(fn):
    with pytest.raises(ValueError):
        fn()
