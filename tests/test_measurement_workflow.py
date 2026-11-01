"""Regression tests for the unified measurement and tuning workflow."""
import pytest
from rf_lab.measurement_workflow import (
    parse_measurement_bytes, measurement_snapshot, measurement_workflow,
)
from rf_lab.measurements import S1P

def sweep(z0=50.0):
    # Crossing of imaginary impedance near 146 MHz, with passive reflection.
    return S1P((145e6,146e6,147e6),
               (complex(.2,-.2),complex(.1,0),complex(.2,.2)),z0)

def test_snapshot_separates_best_match_and_resonance():
    result=measurement_snapshot(sweep(),146)
    assert result["points"]==3
    assert result["target_covered"]
    assert result["resonance_mhz"]==pytest.approx(146)
    assert result["best_match_mhz"]==pytest.approx(146)

def test_workflow_with_and_without_after():
    first=measurement_workflow(sweep(),146,1000)
    assert first["after"] is None
    assert first["advice"].direction=="on target"
    both=measurement_workflow(sweep(),146,1000,sweep())
    assert both["comparison"] is not None
    assert both["comparison"]["minimum_swr_change"]==pytest.approx(0)

def test_reference_impedance_mismatch_rejected():
    with pytest.raises(ValueError,match="reference impedances"):
        measurement_workflow(sweep(50),146,1000,sweep(75))

def test_target_outside_sweep():
    assert not measurement_snapshot(sweep(),150)["target_covered"]

def test_s1p_file_limits_and_encoding():
    s=b"# MHz S RI R 50\n145 .2 -.2\n146 .1 0\n147 .2 .2\n"
    assert parse_measurement_bytes(s).reference_ohm==50
    for bad in (b"\xff",b"x"*2_000_001):
        with pytest.raises(ValueError):
            parse_measurement_bytes(bad)
