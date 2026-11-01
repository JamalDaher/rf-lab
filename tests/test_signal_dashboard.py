"""Unified signal dashboard integration and safety tests."""
import json
import numpy as np
import pytest
from rf_lab.signal_dashboard import inspect_signal,report_rows
from rf_lab.signal_classification import synthetic_classification_iq
from rf_lab.dashboard import WORKSPACES

def test_combined_axes_and_marker():
    iq=synthetic_classification_iq("AM-like",rate=16000,duration=.5)
    result=inspect_signal(iq,16000,fft_size=256,marker_hz=1000)
    assert len(result["spectrum"]["frequency_hz"])==256
    assert result["waterfall"]["power_db_hz"].shape[0]==256
    assert abs(result["marker"]["frequency_hz"]-1000)<=16000/256
    assert result["classification"]["label"]
    assert np.isfinite(result["marker"]["psd_db_hz"])

def test_json_report_excludes_iq():
    iq=synthetic_classification_iq()
    report=report_rows(inspect_signal(iq,16000))
    assert report["sample_count"]==len(iq)
    assert "iq" not in report
    assert "peaks" in report["spectrum"]
    assert isinstance(json.dumps(report),str)

def test_silent_classification():
    result=inspect_signal(np.zeros(2048,dtype=complex),16000)
    assert result["classification"] is None

@pytest.mark.parametrize("rate,marker,fft",[(0,0,256),(16000,8000,256),
                                             (16000,-9000,256),(16000,float("nan"),256),
                                             (16000,0,12)])
def test_invalid_settings(rate,marker,fft):
    with pytest.raises(ValueError):
        inspect_signal(np.ones(4096,dtype=complex),rate,fft,marker_hz=marker)

def test_navigation():
    assert "RF Signal Analysis Dashboard" in WORKSPACES["Signal analysis"]
