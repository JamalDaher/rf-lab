"""Receiver DSP validation and regression tests."""
import numpy as np
import pytest
from rf_lab.receiver import (frequency_shift,fir_filter,bandpass,am_demodulate,
                             fm_demodulate,export_complex64,synthetic_receiver_iq,
                             receiver_pipeline)
from rf_lab.sdr_lab import read_iq_bytes

def test_tuning_moves_carrier_to_dc():
    rate=16000
    n=np.arange(1600)
    x=np.exp(2j*np.pi*2000*n/rate)
    shifted=frequency_shift(x,rate,2000)
    assert np.max(abs(shifted-1))<1e-10

def test_am_demod_recovers_tone():
    rate=16000
    x=synthetic_receiver_iq("AM",rate,.5,2000,200,.5)
    out=receiver_pipeline(x,rate,2000,1500,demodulation="AM")["demodulated"]
    freq=np.fft.rfftfreq(len(out),1/rate)
    peak=freq[np.argmax(abs(np.fft.rfft(out)))]
    assert peak==pytest.approx(200,abs=3)

def test_fm_demod_recovers_frequency():
    rate=16000
    x=synthetic_receiver_iq("FM",rate,.5,2000,200,.5)
    out=receiver_pipeline(x,rate,2000,1500,demodulation="FM")["demodulated"]
    assert np.std(out[200:-200])>20
    assert abs(np.mean(out[200:-200]))<3

def test_fir_suppresses_high_tone():
    rate=16000
    t=np.arange(4096)/rate
    x=np.exp(2j*np.pi*100*t)+np.exp(2j*np.pi*3000*t)
    y=fir_filter(x,rate,500)
    assert np.mean(abs(y[200:-200]-np.exp(2j*np.pi*100*t[200:-200])))<.1

def test_bandpass_suppresses_out_of_band():
    rate=16000
    t=np.arange(4096)/rate
    x=np.exp(2j*np.pi*100*t)+np.exp(2j*np.pi*2000*t)
    y=bandpass(x,rate,1500,2500)
    assert np.mean(abs(y[200:-200]-np.exp(2j*np.pi*2000*t[200:-200])))<.1

def test_export_roundtrip():
    x=synthetic_receiver_iq("AM",16000,.1,2000,200,.5)
    restored=read_iq_bytes(export_complex64(x))
    assert np.allclose(x,restored,atol=1e-6)

@pytest.mark.parametrize("call",[
    lambda: frequency_shift(np.ones(64),16000,9000),
    lambda: fir_filter(np.ones(64),16000,9000),
    lambda: fir_filter(np.ones(64),16000,1000,taps=100),
    lambda: bandpass(np.ones(64),16000,2000,1000),
    lambda: synthetic_receiver_iq("FM",16000,.2,7900,200,1),
    lambda: receiver_pipeline(np.ones(64),16000,demodulation="SSB"),
])
def test_invalid_parameters(call):
    with pytest.raises(ValueError):
        call()
