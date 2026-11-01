"""Tests for aligned before/after offline signal analysis."""
import json
import numpy as np
import pytest
from rf_lab.signal_classification import synthetic_classification_iq
from rf_lab.signal_comparison import compare_recordings,comparison_report
from rf_lab.dashboard import WORKSPACES

def test_identical_recordings_have_zero_difference():
    x=synthetic_classification_iq("AM-like",rate=16000)
    r=compare_recordings(x,x,16000,16000)
    assert np.max(np.abs(r["delta_db"]))<1e-10
    assert r["metrics"]["bandwidth_change_hz"]==0
    assert r["metrics"]["classification_before"]==r["metrics"]["classification_after"]

def test_different_sample_rates_use_common_hz_axis():
    a=synthetic_classification_iq(rate=8000)
    b=synthetic_classification_iq(rate=16000)
    r=compare_recordings(a,b,8000,16000)
    assert len(r["frequency_hz"])==512
    assert np.all(np.diff(r["frequency_hz"])>0)
    assert np.max(np.abs(r["frequency_hz"]))<4000
    assert np.all(np.isfinite(r["delta_db"]))

def test_export_has_no_raw_iq():
    x=synthetic_classification_iq()
    r=compare_recordings(x,x,16000,16000)
    report=comparison_report(r)
    assert report["schema_version"]==1
    assert "iq" not in report
    assert "frequency_hz" not in report
    json.dumps(report)

@pytest.mark.parametrize("rates",[(0,16000),(16000,-1),(float("nan"),16000)])
def test_invalid_rates(rates):
    x=synthetic_classification_iq()
    with pytest.raises(ValueError):
        compare_recordings(x,x,*rates)

def test_navigation():
    assert "RF Signal Recording Comparison" in WORKSPACES["Signal analysis"]
