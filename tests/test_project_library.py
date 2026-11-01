"""Project library serialization, input validation and measurement retention."""
import json
from io import BytesIO
from zipfile import ZipFile
import pytest
from rf_lab.project_library import (
    new_project,validate_project,save_library,load_library,add_measurement,
    measurement_sweep,library_zip,
)
from rf_lab.measurements import S1P
from rf_lab.design_workbench import make_design

def test_roundtrip_and_attachments():
    p=new_project("Portable Yagi",146,"Field notes")
    p["design"]=make_design("Yagi",146,[1.02,.98,.92],[0,.4,.7])
    p["construction_checks"]=[True,False,True]
    sweep=S1P((145e6,146e6),(.2-.1j,.1+0j),50)
    p=add_measurement(p,"before.s1p",sweep)
    p["tuning_history"]=[]
    restored=load_library(save_library([p]))
    assert restored==[p]
    m=measurement_sweep(restored[0]["measurements"][0])
    assert m.gamma==sweep.gamma
    assert m.frequencies_hz==sweep.frequencies_hz

def test_backup_zip_contains_importable_json():
    p=new_project("Yagi",146)
    with ZipFile(BytesIO(library_zip([p]))) as z:
        assert load_library(z.read("antenna-project-library.json"))==[p]

def test_duplicate_ids_rejected():
    p=new_project("Yagi",146)
    with pytest.raises(ValueError,match="Duplicate"):
        save_library([p,p])

@pytest.mark.parametrize("invalid",[
    {"schema_version":2,"projects":[]},
    {"schema_version":1,"projects":"oops"},
    {"schema_version":1,"projects":[{"name":"partial"}]},
])
def test_bad_import_rejected(invalid):
    with pytest.raises((ValueError,TypeError,KeyError)):
        load_library(json.dumps(invalid))

def test_corrupted_sweep_rejected():
    p=new_project("Yagi",146)
    p["measurements"]=[{"name":"x","reference_ohm":50,
        "frequencies_hz":[146e6,145e6],"gamma_ri":[[0,0],[0,0]]}]
    with pytest.raises(ValueError,match="frequencies"):
        validate_project(p)

def test_nonfinite_and_invalid_fields_rejected():
    with pytest.raises(ValueError):
        new_project("Yagi",float("nan"))
    p=new_project("Yagi",146)
    p["construction_checks"]=[1]
    with pytest.raises(ValueError):
        validate_project(p)

def test_large_backup_rejected():
    with pytest.raises(ValueError,match="8 MB"):
        load_library(b"x"*8_000_001)
