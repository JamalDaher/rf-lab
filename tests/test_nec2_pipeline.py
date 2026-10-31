import json
from unittest.mock import patch
import pytest
from rf_lab.nec2_pipeline import compare_impedance,run_benchmark,report_json
from rf_lab.nec2_runner import NEC2Run

def test_impedance_error():
    result=compare_impedance(55+12j,50+10j)
    assert result["resistance_error_ohm"]==5
    assert result["reactance_error_ohm"]==2
    assert result["absolute_error_ohm"]==pytest.approx(29**.5)
    assert result["relative_error"]==pytest.approx((29/2600)**.5)

def test_bad_impedance():
    with pytest.raises(ValueError):
        compare_impedance(complex(float("nan"),0),50+0j)

def test_version_required():
    with pytest.raises(ValueError,match="solver_version"):
        run_benchmark(146,[1,.98,.95],[0,.2,.35],"/bin/false","")

def test_nonzero_solver_exit_is_error():
    with patch("rf_lab.nec2_pipeline.run_nec2",
               return_value=NEC2Run("deck","failure",1)):
        with pytest.raises(RuntimeError,match="status 1"):
            run_benchmark(146,[1,.98,.95],[0,.2,.35],"dummy","test")

def test_unparseable_output_never_becomes_fake_reference():
    with patch("rf_lab.nec2_pipeline.run_nec2",
               return_value=NEC2Run("deck","unrecognized output",0)):
        with pytest.raises(ValueError,match="input-parameters"):
            run_benchmark(146,[1,.98,.95],[0,.2,.35],"dummy","test")

def test_successful_pipeline_uses_parsed_values():
    # This is a synthetic mocked solver response, not NEC validation.
    with patch("rf_lab.nec2_pipeline.run_nec2",
               return_value=NEC2Run("deck","MOCK OUTPUT",0)),patch(
               "rf_lab.nec2_pipeline.parse_nec2_input_impedance",
               return_value=50+10j):
        result=run_benchmark(146,[1,.98,.95],[0,.2,.35],"dummy","mocked")
    report=json.loads(report_json(result))
    assert report["manifest"]["solver_version"]=="mocked"
    assert report["manifest"]["validation_status"].startswith("UNVALIDATED")
    assert report["comparison"]["nec_real_ohm"]==50
    assert len(report["manifest"]["deck_sha256"])==64
    assert report["manifest"]["pattern_metrics_available"] is False
