"""Noise laboratory repeatability, signal quality and navigation tests."""
import numpy as np
import pytest
from rf_lab.noise_comparison import compare_noise
from rf_lab.dashboard import WORKSPACES

def test_comparison_returns_both_modes_and_wav():
    data=compare_noise()
    assert set(data)=={"AM","FM"}
    for mode in data:
        assert len(data[mode]["clean"])==len(data[mode]["noisy"])
        assert data[mode]["noisy_wav"][:4]==b"RIFF"
        assert np.isfinite(data[mode]["audio_snr_db"])

def test_noise_is_reproducible():
    a=compare_noise(10,300,.3,99)
    b=compare_noise(10,300,.3,99)
    assert all(a[k]["noisy_wav"]==b[k]["noisy_wav"] for k in ("AM","FM"))

def test_higher_snr_improves_recovery():
    low=compare_noise(0,300,.5,42)
    high=compare_noise(35,300,.5,42)
    for mode in ("AM","FM"):
        assert high[mode]["audio_snr_db"]>low[mode]["audio_snr_db"]+5

def test_navigation():
    assert "AM vs FM Noise Lab" in WORKSPACES["Signal analysis"]

@pytest.mark.parametrize("kwargs",[
    {"snr_db":float("nan")},{"snr_db":100},{"tone_hz":0},
    {"duration_s":10},{"seed":-1},{"seed":1.2},
])
def test_rejects_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        compare_noise(**kwargs)
