import io
import json
import zipfile
import pytest
from rf_lab.design_workbench import (
    make_design,validate_design,design_json,compare_designs,
    frequency_sweep,package_design)

def example(name="Example"):
    return make_design(name,146,[1,.95,.9],[0,.3,.55],2,5)

def test_roundtrip_and_package():
    design=example()
    assert validate_design(design_json(design))==design
    with zipfile.ZipFile(io.BytesIO(package_design(design))) as z:
        assert {"design.json","model.nec","dimensions.csv","LIMITATIONS.txt"}<=set(z.namelist())
        assert "GW 1 5" in z.read("model.nec").decode()

def test_comparison():
    rows=compare_designs([example("One"),example("Two")])
    assert len(rows)==2 and rows[0]["boom_mm"]==550
    with pytest.raises(ValueError):
        compare_designs([example(),example()])

@pytest.mark.parametrize("mutation",[
    {"schema":"unknown"},{"version":2},{"name":""},
    {"frequency_mhz":float("nan")},{"segments_per_element":6},
    {"lengths_m":[1,2]},{"positions_m":[0,.3,.2]},
])
def test_invalid_design(mutation):
    design=example()
    design.update(mutation)
    with pytest.raises((ValueError,TypeError)):
        validate_design(design)

def test_nonfinite_json_rejected():
    with pytest.raises(ValueError):
        validate_design(design_json(example()).replace("146.0","NaN"))

def test_sweep_with_stub(monkeypatch):
    def fake(freq,*args,**kwargs):
        return type("R",(),{"feed_impedance_ohm":complex(freq,1),
                            "swr_50":1.5})()
    monkeypatch.setattr("rf_lab.design_workbench.solve_yagi_mom",fake)
    rows=frequency_sweep(example(),140,150,3)
    assert [r["frequency_mhz"] for r in rows]==[140,145,150]
    with zipfile.ZipFile(io.BytesIO(package_design(example(),rows))) as z:
        assert "frequency_sweep.csv" in z.namelist()

def test_sweep_bounds():
    with pytest.raises(ValueError):
        frequency_sweep(example(),150,140,3)
    with pytest.raises(ValueError):
        frequency_sweep(example(),140,150,100)
