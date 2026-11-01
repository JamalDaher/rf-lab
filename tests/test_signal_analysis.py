"""Signal generator, spectral analysis, filtering and validation tests."""
import numpy as np
import pytest
from rf_lab.signal_analysis import generate_signal,spectrum,analyze_signal,lowpass

def test_cw_fft_peak():
    t,y,clean=generate_signal("CW",1000,100,8000,0.25)
    f,a,db=spectrum(y,8000,"rectangular")
    assert f[np.argmax(a[1:])+1]==pytest.approx(1000)
    assert np.max(a)==pytest.approx(1,abs=.02)
    assert np.array_equal(y,clean)

def test_am_has_sidebands():
    _,y,_=generate_signal("AM",1000,100,8000,0.5,0.6)
    f,a,_=spectrum(y,8000,"rectangular")
    for target in (900,1000,1100):
        assert a[np.argmin(abs(f-target))]>.1

def test_fm_changes_waveform_and_is_bounded():
    _,fm,_=generate_signal("FM",1000,100,8000,.2,.8)
    _,cw,_=generate_signal("CW",1000,100,8000,.2,.8)
    assert not np.allclose(fm,cw)
    assert np.max(np.abs(fm))<=1+1e-12

def test_noise_is_reproducible():
    _,a,_=generate_signal("AM",1000,100,8000,.2,.5,20)
    _,b,_=generate_signal("AM",1000,100,8000,.2,.5,20)
    assert np.array_equal(a,b)

def test_fir_reduces_high_frequency():
    t=np.arange(8000)/8000
    y=np.sin(2*np.pi*100*t)+np.sin(2*np.pi*1800*t)
    filtered=lowpass(y,8000,300)
    assert np.std(filtered[100:-100]-np.sin(2*np.pi*100*t[100:-100]))<.05

@pytest.mark.parametrize("kwargs",[
    {"carrier_hz":5000,"sample_rate_hz":8000},
    {"depth":-1},
    {"duration_s":100},
    {"modulation":"SSB"},
    {"noise_snr_db":float("nan")},
    {"modulation":"FM","carrier_hz":3900,"tone_hz":200,"depth":1,"sample_rate_hz":8000},
])
def test_invalid_generator_rejected(kwargs):
    with pytest.raises(ValueError):
        generate_signal(**kwargs)

def test_spectrum_rejects_invalid_vectors():
    with pytest.raises(ValueError):
        spectrum([float("nan")]*64,8000)
    with pytest.raises(ValueError):
        spectrum(np.ones((64,2)),8000)
    with pytest.raises(ValueError):
        spectrum(np.ones(64),8000,"invalid")

def test_measurements():
    _,y,_=generate_signal("CW",1000,100,8000,.2)
    result=analyze_signal(y,8000)
    assert result["sample_count"]==1600
    assert result["frequency_resolution_hz"]==pytest.approx(5)
    assert result["rms"]==pytest.approx(2**-.5,abs=.01)
