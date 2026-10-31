"""Numerical regression gates for reproducible NEC/EFIE benchmarks.

Regression limits are maintenance thresholds, NOT physical accuracy claims.
"""
import json
import math
from .benchmark_reports import compare_summaries,validate_summary

DEFAULT_LIMITS={
    "max_nec_impedance_delta_ohm":0.5,
    "max_efie_impedance_delta_ohm":0.5,
    "max_absolute_error_delta_ohm":0.5,
}

def check_regression(baseline,candidate,limits=None):
    comparison=compare_summaries(baseline,candidate)
    limits=DEFAULT_LIMITS if limits is None else limits
    if set(limits)!=set(DEFAULT_LIMITS):
        raise ValueError("regression limits must include exactly the supported keys")
    for key,value in limits.items():
        if type(value) not in (float,int) or not math.isfinite(value) or value<0:
            raise ValueError(f"invalid threshold {key}")
    results=[]
    for row in comparison["changes"]:
        checks={
            "nec_impedance":row["nec_impedance_change_ohm"]<=limits["max_nec_impedance_delta_ohm"],
            "efie_impedance":row["efie_impedance_change_ohm"]<=limits["max_efie_impedance_delta_ohm"],
            "absolute_error":abs(row["impedance_error_change_ohm"])<=limits["max_absolute_error_delta_ohm"]
        }
        results.append({"segments_per_element":row["segments_per_element"],
                        "checks":checks,"passed":all(checks.values()),
                        "metrics":row})
    return {"schema_version":1,"kind":"rf-lab-regression-result",
            "passed":all(row["passed"] for row in results),
            "limits":dict(limits),"cases":results,
            "baseline_solver_version":comparison["baseline_solver_version"],
            "candidate_solver_version":comparison["candidate_solver_version"],
            "interpretation":"Numerical stability regression gate; not physical accuracy validation"}

def result_json(result):
    return json.dumps(result,indent=2,allow_nan=False)+"\n"
