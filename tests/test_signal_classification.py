"""Classification validation, reproducibility and navigation tests."""
import numpy as np
import pytest
from rf_lab.signal_classification import KINDS,synthetic_classification_iq,extract_features,classify_signal
from rf_lab.dashboard import WORKSPACES

@pytest.mark.parametrize("kind",KINDS)
def test_synthetic_features_and_scores(kind):
    x=synthetic_classification_iq(kind,snr_db=50)
    result=classify_signal(x,16000)
    assert result["label"] in KINDS
    assert abs(sum(result["scores"].values())-1)<1e-9
    assert all(np.isfinite(v) for v in result["features"].values())
    assert result["features"]["occupied_bandwidth_hz"]>=0

def test_deterministic():
    x=synthetic_classification_iq("Digital-like",seed=13)
    assert np.array_equal(x,synthetic_classification_iq("Digital-like",seed=13))
    assert classify_signal(x,16000)==classify_signal(x,16000)

def test_clean_cw_label():
    x=synthetic_classification_iq("CW / narrow carrier",snr_db=60)
    assert classify_signal(x,16000)["label"]=="CW / narrow carrier"

def test_clean_am_label():
    x=synthetic_classification_iq("AM-like",snr_db=60)
    assert classify_signal(x,16000)["label"]=="AM-like"

def test_navigation():
    assert "RF Signal Classification" in WORKSPACES["Signal analysis"]

@pytest.mark.parametrize("kwargs",[
    {"kind":"unknown"},{"rate":0},{"duration":4},{"snr_db":float("nan")},{"seed":-1}
])
def test_bad_synthesis(kwargs):
    with pytest.raises(ValueError):
        synthetic_classification_iq(**kwargs)

def test_invalid_input():
    with pytest.raises(ValueError):
        extract_features(np.zeros(1024,dtype=complex),16000)
    with pytest.raises(ValueError):
        extract_features(np.ones(1024,dtype=complex),0)
