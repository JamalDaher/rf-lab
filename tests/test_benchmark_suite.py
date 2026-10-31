"""Unit tests use fake benchmark runner; integration runs actual nec2c."""
import json
import math
import shutil
from types import SimpleNamespace
import pytest
from rf_lab import benchmark_suite as suite
from rf_lab.nec2_pipeline import PipelineResult

def fake_benchmark(*args,**kwargs):
    n=kwargs["segments_per_element"]
    deck=f"GW {n}\n"
    output=f"output {n}\n"
    return PipelineResult(deck,output,
        {"segments_per_element":n,"deck_sha256":"deck"+str(n),
         "output_sha256":"output"+str(n)},
        {"nec_real_ohm":40+n,"nec_imag_ohm":5,
         "model_real_ohm":30+n,"model_imag_ohm":7,
         "absolute_error_ohm":math.hypot(10,2),
         "relative_error":0.2})

def test_suite_mesh_differences_and_exports(monkeypatch,tmp_path):
    monkeypatch.setattr(suite,"run_benchmark",fake_benchmark)
    result=suite.run_suite(146,[1,.9,.8],[0,.2,.4],"nec2c","test",
                           meshes=(7,9,11))
    rows=result.summary["cases"]
    assert [r["segments_per_element"] for r in rows]==[7,9,11]
    assert rows[0]["nec_impedance_change_ohm"] is None
    assert rows[1]["nec_impedance_change_ohm"]==pytest.approx(2)
    assert rows[2]["efie_impedance_change_ohm"]==pytest.approx(2)
    assert len(result.cases)==3
    assert len(suite.suite_csv(result).splitlines())==4
    destination=suite.write_suite(result,tmp_path)
    assert json.loads((destination/"summary.json").read_text())["schema_version"]==1
    assert (destination/"mesh-07"/"model.nec").read_text()=="GW 7\n"
    assert (destination/"mesh-11"/"solver-output.txt").read_text()=="output 11\n"

@pytest.mark.parametrize("meshes",[(7,7),(9,7),(4,7),(7,8),(7,),tuple(range(5,23,2))])
def test_reject_invalid_meshes(meshes):
    with pytest.raises(ValueError):
        suite._validate_meshes(meshes)

@pytest.mark.skipif(shutil.which("nec2c") is None,reason="nec2c not installed")
def test_real_solver_benchmark_two_meshes(tmp_path):
    wavelength=299792458/(146e6)
    result=suite.run_suite(146,[.505*wavelength,.475*wavelength,.45*wavelength],
                           [0,.2*wavelength,.35*wavelength],
                           "nec2c","CI-installed nec2c",meshes=(7,9))
    destination=suite.write_suite(result,tmp_path)
    assert len(result.cases)==2
    assert all(math.isfinite(r["nec_real_ohm"]) for r in result.summary["cases"])
    assert (destination/"summary.csv").is_file()
