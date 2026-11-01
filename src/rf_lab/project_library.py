"""Portable, schema-validated, in-memory antenna project library."""
from datetime import datetime, timezone
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import json
import math
import re
import uuid

MAX_PROJECTS=50
MAX_MEASUREMENTS=10
MAX_POINTS=20000
MAX_BYTES=8_000_000

def _valid_number(value, positive=False):
    return type(value) in (float,int) and math.isfinite(value) and (not positive or value>0)

def new_project(name,frequency_mhz,notes=""):
    if not isinstance(name,str) or not name.strip() or len(name)>80:
        raise ValueError("Project name must be 1–80 characters")
    if not _valid_number(frequency_mhz,True):
        raise ValueError("Frequency must be positive and finite")
    if not isinstance(notes,str) or len(notes)>2000:
        raise ValueError("Notes must be at most 2000 characters")
    return {"id":str(uuid.uuid4()),"name":name.strip(),"frequency_mhz":frequency_mhz,
            "notes":notes,"created_at":datetime.now(timezone.utc).isoformat(),
            "design":None,"construction_checks":[],
            "measurements":[],"tuning_history":[]}

def validate_project(p):
    if not isinstance(p,dict) or set(p)!={"id","name","frequency_mhz","notes","created_at",
                                           "design","construction_checks","measurements","tuning_history"}:
        raise ValueError("Invalid project fields")
    try:
        uuid.UUID(p["id"])
        datetime.fromisoformat(p["created_at"])
    except (ValueError,TypeError,KeyError) as exc:
        raise ValueError("Invalid project ID or timestamp") from exc
    if not isinstance(p["name"],str) or not 0<len(p["name"])<=80:
        raise ValueError("Invalid project name")
    if not _valid_number(p["frequency_mhz"],True):
        raise ValueError("Invalid project frequency")
    if not isinstance(p["notes"],str) or len(p["notes"])>2000:
        raise ValueError("Invalid project notes")
    if p["design"] is not None:
        from rf_lab.design_workbench import validate_design
        validate_design(json.dumps(p["design"],allow_nan=False))
    if not isinstance(p["construction_checks"],list) or len(p["construction_checks"])>100 or any(
        type(x) is not bool for x in p["construction_checks"]):
        raise ValueError("Invalid construction checklist")
    if not isinstance(p["measurements"],list) or len(p["measurements"])>MAX_MEASUREMENTS:
        raise ValueError("Too many measurements")
    for m in p["measurements"]:
        if not isinstance(m,dict) or set(m)!={"name","frequencies_hz","gamma_ri","reference_ohm"}:
            raise ValueError("Invalid measurement fields")
        if not isinstance(m["name"],str) or not 0<len(m["name"])<=100:
            raise ValueError("Invalid measurement name")
        fs,gs=m["frequencies_hz"],m["gamma_ri"]
        if not isinstance(fs,list) or not isinstance(gs,list) or not 1<=len(fs)<=MAX_POINTS or len(fs)!=len(gs):
            raise ValueError("Invalid measurement point count")
        if not _valid_number(m["reference_ohm"],True):
            raise ValueError("Invalid reference impedance")
        if any(not _valid_number(f,True) for f in fs) or any(b<=a for a,b in zip(fs,fs[1:])):
            raise ValueError("Invalid measurement frequencies")
        if any(not isinstance(g,list) or len(g)!=2 or not all(_valid_number(v) for v in g)
               for g in gs):
            raise ValueError("Invalid reflection coefficients")
    from rf_lab.tuning import history_json,load_history
    load_history(history_json(p["tuning_history"]))
    return p

def save_library(projects):
    if not isinstance(projects,list) or len(projects)>MAX_PROJECTS:
        raise ValueError("Too many projects")
    for p in projects:
        validate_project(p)
    ids=[p["id"] for p in projects]
    if len(set(ids))!=len(ids):
        raise ValueError("Duplicate project IDs")
    return json.dumps({"schema_version":1,"projects":projects},allow_nan=False,indent=2)

def load_library(raw):
    if isinstance(raw,bytes):
        if len(raw)>MAX_BYTES:
            raise ValueError("Library file exceeds 8 MB")
        raw=raw.decode("utf-8-sig")
    if not isinstance(raw,str) or len(raw.encode("utf-8"))>MAX_BYTES:
        raise ValueError("Library file exceeds 8 MB")
    data=json.loads(raw)
    if not isinstance(data,dict) or set(data)!={"schema_version","projects"} or data["schema_version"]!=1:
        raise ValueError("Unsupported project library format")
    save_library(data["projects"])
    return data["projects"]

def add_measurement(project,name,sweep):
    from rf_lab.measurements import S1P
    if not isinstance(sweep,S1P) or not isinstance(name,str):
        raise ValueError("Invalid measurement")
    p=json.loads(json.dumps(project,allow_nan=False))
    p["measurements"].append({"name":name[:100],
        "frequencies_hz":list(sweep.frequencies_hz),
        "gamma_ri":[[g.real,g.imag] for g in sweep.gamma],
        "reference_ohm":sweep.reference_ohm})
    validate_project(p)
    return p

def measurement_sweep(m):
    from rf_lab.measurements import S1P
    return S1P(tuple(m["frequencies_hz"]),
               tuple(complex(*g) for g in m["gamma_ri"]),m["reference_ohm"])

def library_zip(projects):
    payload=save_library(projects)
    out=BytesIO()
    with ZipFile(out,"w",ZIP_DEFLATED) as archive:
        archive.writestr("antenna-project-library.json",payload)
        archive.writestr("README.txt","RF Lab project library v1. Import the JSON file in Project Library. "
                         "Measurement files are stored as numeric S11 samples; this is not a database backup.")
    return out.getvalue()
