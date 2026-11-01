"""Spectrum analyzer correctness, limits and integration."""
import numpy as np
import pytest
from rf_lab.spectrum_analyzer import analyze_spectrum,synthetic_spectrum_iq
from rf_lab.dashboard import WORKSPACES

def test_peak_locations_and_bandwidth():
    x=synthetic_spectrum_iq(noise_db=-60)
    result=analyze_spectrum(x,16000,1024,50,"Hann",15)
    found=[p["frequency_hz"] for p in result["peaks"]]
    assert any(abs(f-1800)<20 for f in found)
    assert any(abs(f+2800)<20 for f in found)
    assert 0<result["occupied_bandwidth_hz"]<16000
    assert result["segments_averaged"]>1

def test_noise_floor_increases_with_noise():
    quiet=analyze_spectrum(synthetic_spectrum_iq(noise_db=-60),16000)
    loud=analyze_spectrum(synthetic_spectrum_iq(noise_db=-10),16000)
    assert loud["noise_floor_db_hz"]>quiet["noise_floor_db_hz"]+20

def test_repeatable_and_finite():
    a=synthetic_spectrum_iq(seed=13)
    b=synthetic_spectrum_iq(seed=13)
    assert np.array_equal(a,b)
    r=analyze_spectrum(a,16000)
    assert np.isfinite(r["psd_db_hz"]).all()
    assert np.isfinite(r["noise_floor_db_hz"])

def test_zero_signal():
    r=analyze_spectrum(np.zeros(2048,dtype=complex),16000)
    assert r["occupied_bandwidth_hz"]==0
    assert not r["peaks"]

def test_navigation():
    assert "RF Spectrum Analyzer" in WORKSPACES["Signal analysis"]

@pytest.mark.parametrize("kwargs",[
    {"fft_size":100},{"fft_size":4096,"overlap_percent":40},
    {"window":"invalid"},{"peak_threshold_db":float("nan")},
    {"max_peaks":0},{"sample_rate_hz":0},
])
def test_bad_analysis_options(kwargs):
    options={"iq":np.ones(4096,dtype=complex),"sample_rate_hz":16000}
    options.update(kwargs)
    with pytest.raises(ValueError):
        analyze_spectrum(**options)

@pytest.mark.parametrize("kwargs",[
    {"rate":0},{"tone_hz":9000},{"noise_db":float("inf")},
    {"seed":-1},{"duration":5},
])
def test_bad_synthetic_options(kwargs):
    with pytest.raises(ValueError):
        synthetic_spectrum_iq(**kwargs)
