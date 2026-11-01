"""Waterfall numerical and navigation regression coverage."""
import numpy as np
import pytest
from rf_lab.waterfall_detection import synthetic_activity_iq,analyze_waterfall
from rf_lab.dashboard import WORKSPACES

def test_waterfall_dimensions_and_events():
    x=synthetic_activity_iq()
    r=analyze_waterfall(x,16000,256,50,"Hann",12)
    assert r["power_db_hz"].shape==(256,len(r["time_s"]))
    assert len(r["frequency_hz"])==256
    assert np.isfinite(r["power_db_hz"]).all()
    assert r["events"]
    assert all(0<=e["start_s"]<e["end_s"]<=1 for e in r["events"])
    assert any(abs(e["frequency_hz"]-1920)<130 for e in r["events"])

def test_repeatability():
    x=synthetic_activity_iq(seed=8)
    assert np.array_equal(x,synthetic_activity_iq(seed=8))
    assert analyze_waterfall(x,16000)["events"]==analyze_waterfall(x,16000)["events"]

def test_quiet_signal_no_events():
    r=analyze_waterfall(np.zeros(2048,dtype=complex),16000)
    assert r["events"]==[]
    assert r["activity_frames"]==0

def test_navigation():
    assert "RF Waterfall & Signal Detection" in WORKSPACES["Signal analysis"]

@pytest.mark.parametrize("kwargs",[
    {"rate":0},{"duration":10},{"noise_db":1},{"seed":-1},
])
def test_synthetic_validation(kwargs):
    with pytest.raises(ValueError):
        synthetic_activity_iq(**kwargs)

@pytest.mark.parametrize("kwargs",[
    {"rate":0},{"fft_size":2048},{"overlap":30},
    {"window":"Blackman"},{"threshold_db":float("nan")},{"max_events":0},
])
def test_analysis_validation(kwargs):
    options={"iq":np.ones(1024,dtype=complex),"rate":16000}
    options.update(kwargs)
    with pytest.raises(ValueError):
        analyze_waterfall(**options)
