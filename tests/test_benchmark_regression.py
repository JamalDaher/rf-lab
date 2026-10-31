import copy
import hashlib
import json
import pytest
from rf_lab.benchmark_regression import check_regression,result_json

def sample():
    rows=[]
    for n in (7,9):
        z=complex(50+n,5)
        m=complex(48+n,6)
        error=abs(z-m)
        rows.append({"segments_per_element":n,"nec_real_ohm":z.real,
            "nec_imag_ohm":z.imag,"efie_real_ohm":m.real,
            "efie_imag_ohm":m.imag,"absolute_error_ohm":error,
            "relative_error":error/abs(z),
            "deck_sha256":hashlib.sha256(f"deck{n}".encode()).hexdigest(),
            "output_sha256":hashlib.sha256(f"output{n}".encode()).hexdigest()})
    return {"kind":"rf-lab-nec2c-mesh-benchmark","schema_version":1,
            "frequency_mhz":146,"lengths_m":[1,.9,.8],
            "positions_m":[0,.2,.4],"wire_radius_mm":2,
            "mesh_sizes":[7,9],"solver_version":"baseline","cases":rows}

def test_unchanged_passes():
    a=sample()
    result=check_regression(a,copy.deepcopy(a))
    assert result["passed"]
    assert len(result["cases"])==2
    assert json.loads(result_json(result))["passed"]

def test_detects_changed_nec_and_error():
    a=sample()
    b=copy.deepcopy(a)
    row=b["cases"][0]
    row["nec_real_ohm"]+=2
    row["absolute_error_ohm"]=abs(complex(row["efie_real_ohm"],row["efie_imag_ohm"])-
                                  complex(row["nec_real_ohm"],row["nec_imag_ohm"]))
    row["relative_error"]=row["absolute_error_ohm"]/abs(complex(row["nec_real_ohm"],row["nec_imag_ohm"]))
    result=check_regression(a,b)
    assert not result["passed"]
    assert not result["cases"][0]["checks"]["nec_impedance"]
    assert result["cases"][1]["passed"]

def test_rejects_bad_thresholds():
    a=sample()
    for limits in ({"max_nec_impedance_delta_ohm":float("nan")},
                   {"max_nec_impedance_delta_ohm":-1},
                   {"max_nec_impedance_delta_ohm":1,"max_efie_impedance_delta_ohm":1,
                    "max_absolute_error_delta_ohm":-1}):
        with pytest.raises(ValueError):
            check_regression(a,a,limits)

def test_rejects_incompatible_geometry():
    a=sample()
    b=copy.deepcopy(a)
    b["frequency_mhz"]=147
    with pytest.raises(ValueError,match="incompatible"):
        check_regression(a,b)
