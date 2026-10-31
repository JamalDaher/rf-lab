"""Auditable local NEC-2 run pipeline and impedance-only comparisons.

The pipeline does not invent directivity or patterns when the solver output
cannot be parsed. A trusted solver executable must be installed separately.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from .nec2_runner import generate_yagi_nec2, run_nec2, parse_nec2_input_impedance
from .mom import solve_yagi_mom
from .nec2c_adapter import run_nec2c
from .nec2_patterns import parse_nec2_radiation_cut, compare_pattern_cut

@dataclass(frozen=True)
class PipelineResult:
    deck: str
    raw_output: str
    manifest: dict
    comparison: dict

def compare_impedance(model_z: complex, reference_z: complex) -> dict:
    if not all(math.isfinite(x) for x in (
        model_z.real,model_z.imag,reference_z.real,reference_z.imag)):
        raise ValueError("impedances must be finite")
    difference=model_z-reference_z
    return {
        "model_real_ohm":float(model_z.real),
        "model_imag_ohm":float(model_z.imag),
        "nec_real_ohm":float(reference_z.real),
        "nec_imag_ohm":float(reference_z.imag),
        "resistance_error_ohm":float(difference.real),
        "reactance_error_ohm":float(difference.imag),
        "absolute_error_ohm":float(abs(difference)),
        "relative_error":float(abs(difference)/max(abs(reference_z),1e-12))
    }

def run_benchmark(frequency_mhz, lengths_m, positions_m, executable,
                  solver_version, wire_radius_mm=2.0,
                  segments_per_element=9, timeout_seconds=30, adapter="generic"):
    """Run local solver; fail closed on nonzero status or unknown NEC format."""
    if not isinstance(solver_version,str) or not solver_version.strip():
        raise ValueError("solver_version is required for provenance")
    deck=generate_yagi_nec2(frequency_mhz,lengths_m,positions_m,
                            wire_radius_mm,segments_per_element)
    if adapter not in ("generic","nec2c"):
        raise ValueError("adapter must be generic or nec2c")
    run=(run_nec2c if adapter=="nec2c" else run_nec2)(
        deck,executable,timeout_seconds)
    if run.returncode!=0:
        raise RuntimeError(f"NEC solver exited with status {run.returncode}")
    if not run.output.strip():
        raise ValueError("NEC solver returned empty output")
    nec_z=parse_nec2_input_impedance(run.output)
    model=solve_yagi_mom(frequency_mhz,lengths_m,positions_m,
                         wire_radius_mm=wire_radius_mm,
                         segments_per_element=segments_per_element)
    comparison=compare_impedance(model.feed_impedance_ohm,nec_z)
    pattern_available=False
    try:
        cut=parse_nec2_radiation_cut(run.output)
        comparison.update(compare_pattern_cut(model.azimuth_deg,model.azimuth_db,cut))
        pattern_available=True
    except ValueError as exc:
        comparison["pattern_parse_warning"]=str(exc)
    manifest={
        "schema_version":1,
        "reference_solver":"NEC-2",
        "adapter":adapter,
        "solver_version":solver_version.strip(),
        "solver_executable":str(Path(executable).resolve()),
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "frequency_mhz":float(frequency_mhz),
        "lengths_m":[float(x) for x in lengths_m],
        "positions_m":[float(x) for x in positions_m],
        "wire_radius_mm":float(wire_radius_mm),
        "segments_per_element":segments_per_element,
        "deck_sha256":hashlib.sha256(deck.encode()).hexdigest(),
        "output_sha256":hashlib.sha256(run.output.encode()).hexdigest(),
        "feed_model_warning":"NEC excitation and RF Lab EFIE feed are not proven equivalent",
        "validation_status":"UNVALIDATED — numerical differences only",
        "pattern_metrics_available":pattern_available
    }
    return PipelineResult(deck,run.output,manifest,comparison)

def report_json(result: PipelineResult) -> str:
    """Portable report; preserve raw solver output separately."""
    return json.dumps({"manifest":result.manifest,"comparison":result.comparison},
                      indent=2,allow_nan=False)+"\n"
