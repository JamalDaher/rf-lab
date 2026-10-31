"""Reproducible NEC-2c benchmark sweep and mesh-convergence diagnostics.

Runs a trusted locally installed solver; never fabricates NEC references.
No threshold is treated as proof of physical accuracy.
"""
from dataclasses import dataclass
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import numpy as np

from .nec2_pipeline import run_benchmark, report_json

DEFAULT_MESHES=(7,9,11,13)

@dataclass(frozen=True)
class BenchmarkSuite:
    cases: tuple
    summary: dict

def _validate_meshes(meshes):
    values=tuple(meshes)
    if len(values)<2 or len(values)>8 or len(set(values))!=len(values):
        raise ValueError("provide 2 to 8 distinct mesh sizes")
    if any(type(n) is not int or n<5 or n>31 or n%2==0 for n in values):
        raise ValueError("meshes must be odd integers from 5 to 31")
    if tuple(sorted(values))!=values:
        raise ValueError("meshes must be increasing")
    return values

def run_suite(frequency_mhz, lengths_m, positions_m, executable, solver_version,
              meshes=DEFAULT_MESHES, wire_radius_mm=2.0, timeout_seconds=30,
              adapter="nec2c"):
    """Run one NEC and experimental EFIE comparison per requested mesh."""
    meshes=_validate_meshes(meshes)
    cases=[]
    for mesh in meshes:
        result=run_benchmark(frequency_mhz,lengths_m,positions_m,executable,
                             solver_version,wire_radius_mm=wire_radius_mm,
                             segments_per_element=mesh,timeout_seconds=timeout_seconds,
                             adapter=adapter)
        cases.append(result)
    rows=[]
    for result in cases:
        m=result.manifest
        c=result.comparison
        rows.append({
            "segments_per_element":m["segments_per_element"],
            "nec_real_ohm":c["nec_real_ohm"],
            "nec_imag_ohm":c["nec_imag_ohm"],
            "efie_real_ohm":c["model_real_ohm"],
            "efie_imag_ohm":c["model_imag_ohm"],
            "absolute_error_ohm":c["absolute_error_ohm"],
            "relative_error":c["relative_error"],
            "pattern_rms_error_db":c.get("pattern_rms_error_db"),
            "deck_sha256":m["deck_sha256"],
            "output_sha256":m["output_sha256"]
        })
    for index,row in enumerate(rows):
        if index==0:
            row["nec_impedance_change_ohm"]=None
            row["efie_impedance_change_ohm"]=None
        else:
            previous=rows[index-1]
            row["nec_impedance_change_ohm"]=float(abs(complex(
                row["nec_real_ohm"],row["nec_imag_ohm"])-complex(
                previous["nec_real_ohm"],previous["nec_imag_ohm"])))
            row["efie_impedance_change_ohm"]=float(abs(complex(
                row["efie_real_ohm"],row["efie_imag_ohm"])-complex(
                previous["efie_real_ohm"],previous["efie_imag_ohm"])))
    summary={
        "schema_version":1,
        "kind":"rf-lab-nec2c-mesh-benchmark",
        "validation_status":"UNVALIDATED - numerical sensitivity and solver comparison only",
        "solver_version":solver_version,
        "frequency_mhz":float(frequency_mhz),
        "lengths_m":[float(x) for x in lengths_m],
        "positions_m":[float(x) for x in positions_m],
        "wire_radius_mm":float(wire_radius_mm),
        "mesh_sizes":list(meshes),
        "cases":rows,
        "caveats":[
            "No certified NEC reference or physical measurement used",
            "NEC and experimental EFIE feed models are not proven equivalent",
            "Mesh changes quantify sensitivity; they do not establish correctness",
            "Radiation gain and directivity must not be conflated"
        ]
    }
    return BenchmarkSuite(tuple(cases),summary)

def suite_json(suite):
    return json.dumps(suite.summary,indent=2,allow_nan=False)+"\n"

def suite_csv(suite):
    stream=io.StringIO()
    rows=suite.summary["cases"]
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()

def write_suite(suite, output_dir):
    """Write deterministic filenames and per-case provenance artifacts."""
    destination=Path(output_dir)
    destination.mkdir(parents=True,exist_ok=True)
    for case in suite.cases:
        mesh=case.manifest["segments_per_element"]
        folder=destination/f"mesh-{mesh:02d}"
        folder.mkdir(exist_ok=True)
        (folder/"model.nec").write_text(case.deck,encoding="utf-8")
        (folder/"solver-output.txt").write_text(case.raw_output,encoding="utf-8")
        (folder/"comparison.json").write_text(report_json(case),encoding="utf-8")
    (destination/"summary.json").write_text(suite_json(suite),encoding="utf-8")
    (destination/"summary.csv").write_text(suite_csv(suite),encoding="utf-8")
    return destination
