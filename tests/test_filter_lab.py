"""RF FIR filter design and application regression tests."""
import json
import numpy as np
import pytest
from rf_lab.filter_lab import KINDS,design_filter,frequency_response,apply_filter,filter_report
from rf_lab.dashboard import WORKSPACES

@pytest.mark.parametrize("kind",KINDS)
def test_fir_is_real_finite_symmetric(kind):
    h=design_filter(kind,16000,1000,3000,101)
    assert len(h)==101
    assert np.all(np.isfinite(h))
    assert np.allclose(h,h[::-1])
    r=frequency_response(h,16000)
    assert len(r["frequency_hz"])==2048
    assert r["group_delay_samples"]==50
    json.dumps(filter_report(kind,16000,1000,3000,h,r))

def test_lowpass_attenuates_high_frequency():
    h=design_filter("Low-pass",16000,1200,taps=201)
    n=np.arange(4096)
    x=np.exp(2j*np.pi*3000*n/16000)
    y=apply_filter(x,h)
    assert np.mean(np.abs(y[300:-300])**2)<.01

def test_highpass_attenuates_low_frequency():
    h=design_filter("High-pass",16000,1200,taps=201)
    n=np.arange(4096)
    x=np.exp(2j*np.pi*200*n/16000)
    y=apply_filter(x,h)
    assert np.mean(np.abs(y[300:-300])**2)<.01

def test_notch_removes_band():
    h=design_filter("Notch",16000,1500,2500,201)
    n=np.arange(4096)
    x=np.exp(2j*np.pi*2000*n/16000)
    assert np.mean(np.abs(apply_filter(x,h)[300:-300])**2)<.01

@pytest.mark.parametrize("kind,rate,low,high,taps",[
    ("Unknown",16000,1000,None,101),
    ("Low-pass",0,1000,None,101),
    ("Low-pass",16000,8000,None,101),
    ("Band-pass",16000,3000,2000,101),
    ("Notch",16000,1000,8000,101),
    ("Low-pass",16000,1000,None,100)])
def test_invalid_design(kind,rate,low,high,taps):
    with pytest.raises(ValueError):
        design_filter(kind,rate,low,high,taps)

def test_navigation():
    assert "RF Filter Design Laboratory" in WORKSPACES["Signal analysis"]
