import json
import math
import pytest
from rf_lab.nec_reference import load_reference, compare_reference

def fixture():
    return {
        "solver":"NEC-2","solver_version":"test-fixture-not-a-NEC-run",
        "source":"SYNTHETIC TEST DATA — NOT A PHYSICAL BENCHMARK",
        "frequency_mhz":146.0,
        "lengths_m":[1.037,0.975,0.924],
        "positions_m":[0,0.411,0.719],
        "wire_radius_mm":2.0,"segments_per_element":5,
        "feed_impedance_real_ohm":50.0,
        "feed_impedance_imag_ohm":10.0,
        "directivity_dbi":5.0,
        "front_to_back_db":12.0,
        "azimuth_deg":[0,90,180,270,360],
        "azimuth_db":[0,-4,-12,-4,0]
    }

def test_parse_reference():
    ref=load_reference(json.dumps(fixture()))
    assert ref.feed_impedance_ohm==50+10j
    assert ref.azimuth_deg.shape==(5,)

def test_comparison_metrics_are_consistent():
    ref=load_reference(fixture())
    result=compare_reference(ref)
    assert result["impedance_absolute_error_ohm"]>=0
    assert result["impedance_relative_error"]>=0
    assert math.isfinite(result["directivity_error_db"])
    assert math.isfinite(result["azimuth_rms_error_db"])
    assert result["reference_source"].startswith("SYNTHETIC")

def test_optional_pattern():
    data=fixture()
    del data["azimuth_deg"]
    del data["azimuth_db"]
    ref=load_reference(data)
    assert compare_reference(ref)["azimuth_rms_error_db"] is None

@pytest.mark.parametrize("change",[
    {"solver":"unknown"},
    {"source":""},
    {"frequency_mhz":-1},
    {"lengths_m":[1,2]},
    {"positions_m":[0,2,1]},
    {"segments_per_element":6},
    {"feed_impedance_real_ohm":float("nan")},
    {"azimuth_deg":[0,180,90,360]},
    {"azimuth_db":[1,2]},
])
def test_reject_invalid_reference(change):
    data=fixture()
    data.update(change)
    with pytest.raises((ValueError,TypeError)):
        load_reference(data)
