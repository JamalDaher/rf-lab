"""Validate and compare uploaded RF Lab benchmark summaries.

The checks detect malformed/incompatible data, not physical accuracy.
"""
import hashlib
import json
import math

KIND="rf-lab-nec2c-mesh-benchmark"
FIELDS=("nec_real_ohm","nec_imag_ohm","efie_real_ohm","efie_imag_ohm",
        "absolute_error_ohm","relative_error")

def validate_summary(value):
    if isinstance(value,(str,bytes)):
        if len(value)>2_000_000:
            raise ValueError("summary exceeds 2 MB")
        value=json.loads(value,parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    if not isinstance(value,dict) or value.get("kind")!=KIND or value.get("schema_version")!=1:
        raise ValueError("unsupported benchmark summary")
    rows=value.get("cases")
    if not isinstance(rows,list) or not 2<=len(rows)<=8:
        raise ValueError("expected 2–8 cases")
    meshes=value.get("mesh_sizes")
    if not isinstance(meshes,list) or meshes!=[r.get("segments_per_element") for r in rows if isinstance(r,dict)]:
        raise ValueError("mesh list does not match cases")
    if any(type(n)!=int or n<5 or n>31 or n%2==0 for n in meshes) or meshes!=sorted(set(meshes)):
        raise ValueError("invalid mesh sequence")
    freq=value.get("frequency_mhz")
    radius=value.get("wire_radius_mm")
    if not all(type(x) in (int,float) and math.isfinite(x) and x>0 for x in (freq,radius)):
        raise ValueError("invalid frequency or radius")
    lengths=value.get("lengths_m")
    positions=value.get("positions_m")
    if not isinstance(lengths,list) or not isinstance(positions,list) or len(lengths)!=3 or len(positions)!=3:
        raise ValueError("invalid geometry")
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in lengths+positions):
        raise ValueError("nonfinite geometry")
    if min(lengths)<=0 or not positions[0]<positions[1]<positions[2]:
        raise ValueError("invalid geometry dimensions")
    if not isinstance(value.get("solver_version"),str) or not value["solver_version"].strip():
        raise ValueError("missing solver provenance")
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError("invalid case")
        for key in FIELDS:
            x=row.get(key)
            if type(x) not in (int,float) or not math.isfinite(x):
                raise ValueError(f"invalid {key}")
        if row["absolute_error_ohm"]<0 or row["relative_error"]<0:
            raise ValueError("negative error")
        actual=abs(complex(row["efie_real_ohm"],row["efie_imag_ohm"])-
                   complex(row["nec_real_ohm"],row["nec_imag_ohm"]))
        if not math.isclose(actual,row["absolute_error_ohm"],rel_tol=1e-6,abs_tol=1e-6):
            raise ValueError("inconsistent impedance error")
        expected=actual/max(abs(complex(row["nec_real_ohm"],row["nec_imag_ohm"])),1e-12)
        if not math.isclose(expected,row["relative_error"],rel_tol=1e-6,abs_tol=1e-6):
            raise ValueError("inconsistent relative error")
        for key in ("deck_sha256","output_sha256"):
            digest=row.get(key)
            if not isinstance(digest,str) or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError(f"invalid {key}")
    return value

def compare_summaries(before,after):
    """Compare compatible cases; reject geometry/frequency mismatches."""
    a=validate_summary(before)
    b=validate_summary(after)
    for key in ("frequency_mhz","lengths_m","positions_m","wire_radius_mm","mesh_sizes"):
        if a[key]!=b[key]:
            raise ValueError(f"incompatible benchmarks: {key}")
    changes=[]
    for old,new in zip(a["cases"],b["cases"]):
        changes.append({
            "segments_per_element":old["segments_per_element"],
            "impedance_error_change_ohm":new["absolute_error_ohm"]-old["absolute_error_ohm"],
            "nec_impedance_change_ohm":abs(complex(new["nec_real_ohm"],new["nec_imag_ohm"])-
                                           complex(old["nec_real_ohm"],old["nec_imag_ohm"])),
            "efie_impedance_change_ohm":abs(complex(new["efie_real_ohm"],new["efie_imag_ohm"])-
                                            complex(old["efie_real_ohm"],old["efie_imag_ohm"]))
        })
    return {"baseline_solver_version":a["solver_version"],
            "candidate_solver_version":b["solver_version"],
            "changes":changes,
            "interpretation":"Numerical differences only; not proof of accuracy"}

def verify_artifacts(summary,files):
    """Verify per-mesh deck and solver output bytes against manifest digests.

    files maps relative POSIX paths such as mesh-07/model.nec to bytes.
    A summary alone cannot prove its hashes correspond to actual files.
    """
    data=validate_summary(summary)
    checks=[]
    for row in data["cases"]:
        mesh=row["segments_per_element"]
        for filename,key in (("model.nec","deck_sha256"),("solver-output.txt","output_sha256")):
            path=f"mesh-{mesh:02d}/{filename}"
            content=files.get(path)
            ok=isinstance(content,bytes) and hashlib.sha256(content).hexdigest()==row[key]
            checks.append({"file":path,"verified":ok})
    return {"checks":checks,"all_verified":all(c["verified"] for c in checks)}
