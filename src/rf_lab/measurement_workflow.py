"""Unified measurement/tuning workflow helpers for S1P antenna measurements.

All resonance estimates are based on reactance-zero crossings, not SWR minima.
"""
import math
from rf_lab.measurements import parse_s1p, swr_from_gamma
from rf_lab.tuning import tuning_advice, tuning_comparison
from rf_lab.workbench import summarize_sweep


def parse_measurement_bytes(raw: bytes):
    """Decode UTF-8 Touchstone files and reject oversized uploads."""
    if not isinstance(raw, bytes) or len(raw) > 2_000_000:
        raise ValueError("S1P file must be at most 2 MB")
    try:
        return parse_s1p(raw.decode("utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise ValueError("S1P file must be UTF-8 text") from exc


def measurement_snapshot(sweep, target_mhz):
    """Report distinct best-match and resonance frequencies."""
    if not math.isfinite(target_mhz) or target_mhz <= 0:
        raise ValueError("Target frequency must be positive and finite")
    summary = summarize_sweep("measurement", sweep)
    resonance = (min(summary.resonances_mhz, key=lambda f: abs(f-target_mhz))
                 if summary.resonances_mhz else None)
    return {
        "points": len(sweep.frequencies_hz),
        "reference_ohm": sweep.reference_ohm,
        "best_match_mhz": summary.best_match_mhz,
        "minimum_swr": summary.minimum_swr,
        "resonance_mhz": resonance,
        "target_covered": sweep.frequencies_hz[0]/1e6 <= target_mhz <= sweep.frequencies_hz[-1]/1e6,
    }


def measurement_workflow(before, target_mhz, element_length_mm,
                         after=None, tolerance_mhz=0.05):
    """Consolidate pre/post measurement statistics and first-order guidance."""
    first = measurement_snapshot(before, target_mhz)
    guidance = tuning_advice(before, target_mhz, element_length_mm, tolerance_mhz)
    result = {"before": first, "advice": guidance, "after": None, "comparison": None}
    if after is not None:
        if not math.isclose(before.reference_ohm, after.reference_ohm,
                            rel_tol=0, abs_tol=1e-9):
            raise ValueError("Before/after reference impedances differ; "
                             "use matching calibrated S1P exports")
        result["after"] = measurement_snapshot(after, target_mhz)
        result["comparison"] = tuning_comparison(before, after, target_mhz)
    return result
