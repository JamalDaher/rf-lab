"""Conservative antenna tuning guidance and portable tuning-session history."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import math

from rf_lab.measurements import S1P
from rf_lab.workbench import summarize_sweep


@dataclass(frozen=True)
class TuningAdvice:
    target_mhz: float
    resonance_mhz: float | None
    frequency_error_mhz: float | None
    direction: str
    estimated_change_mm: float | None
    message: str


def tuning_advice(sweep: S1P, target_mhz: float, element_length_mm: float,
                  tolerance_mhz: float = 0.05) -> TuningAdvice:
    """Estimate length change using f*L ~= constant.

    Only valid as a first-order estimate for a single adjustable resonant
    element. Multiple reactance-zero crossings are resolved by selecting the
    one nearest the target; the result is explicitly approximate.
    """
    for value, name in ((target_mhz, "target frequency"),
                        (element_length_mm, "element length")):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be positive and finite")
    if not math.isfinite(tolerance_mhz) or tolerance_mhz < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    roots = summarize_sweep("measurement", sweep).resonances_mhz
    if not roots:
        return TuningAdvice(target_mhz, None, None, "unknown", None,
                            "No zero-reactance crossing found in this sweep. "
                            "Expand the sweep or check calibration before adjusting.")
    resonance = min(roots, key=lambda f: abs(f-target_mhz))
    delta = resonance-target_mhz
    if abs(delta) <= tolerance_mhz:
        return TuningAdvice(target_mhz, resonance, delta, "on target", 0.0,
                            "Estimated resonance is within the chosen tolerance.")
    new_length = element_length_mm * resonance / target_mhz
    change = new_length-element_length_mm
    direction = "shorten" if change < 0 else "lengthen"
    return TuningAdvice(target_mhz, resonance, delta, direction, change,
                        "First-order f×L estimate only. Adjust in small steps, "
                        "remeasure, and account for matching, coupling and feed geometry.")


def tuning_comparison(before: S1P, after: S1P, target_mhz: float) -> dict:
    """Compare nearest resonance error and minimum SWR on native sweeps."""
    if not math.isfinite(target_mhz) or target_mhz <= 0:
        raise ValueError("target frequency must be positive and finite")
    first = summarize_sweep("before", before)
    last = summarize_sweep("after", after)
    def nearest(summary):
        return min(summary.resonances_mhz, key=lambda f: abs(f-target_mhz)) if summary.resonances_mhz else None
    a, b = nearest(first), nearest(last)
    return {
        "before_resonance_mhz": a,
        "after_resonance_mhz": b,
        "before_min_swr": first.minimum_swr,
        "after_min_swr": last.minimum_swr,
        "resonance_error_improvement_mhz":
            abs(a-target_mhz)-abs(b-target_mhz) if a is not None and b is not None else None,
        "minimum_swr_change":
            last.minimum_swr-first.minimum_swr
            if first.minimum_swr is not None and last.minimum_swr is not None else None,
    }


def add_history_entry(entries: list[dict], label: str, advice: TuningAdvice,
                      length_mm: float, notes: str = "", timestamp: str | None = None) -> list[dict]:
    """Return a new list of JSON-safe tuning records, leaving the input untouched."""
    if not label.strip():
        raise ValueError("label is required")
    if not math.isfinite(length_mm) or length_mm <= 0:
        raise ValueError("length must be positive")
    record = {"timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
              "label": label[:100], "length_mm": length_mm,
              "notes": notes[:1000], **asdict(advice)}
    return [*entries, record]


def history_json(entries: list[dict]) -> str:
    return json.dumps({"schema_version": 1, "entries": entries}, indent=2, allow_nan=False)


def load_history(text: str) -> list[dict]:
    data = json.loads(text)
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("unsupported tuning history format")
    entries = data.get("entries")
    if not isinstance(entries, list) or len(entries) > 1000:
        raise ValueError("invalid tuning history entries")
    required = {"timestamp", "label", "length_mm", "target_mhz",
                "resonance_mhz", "frequency_error_mhz", "direction",
                "estimated_change_mm", "message", "notes"}
    for entry in entries:
        if not isinstance(entry, dict) or not required.issubset(entry):
            raise ValueError("invalid tuning history entry")
        if not isinstance(entry["label"], str) or not isinstance(entry["notes"], str):
            raise ValueError("invalid tuning history text")
        if not isinstance(entry["length_mm"], (float,int)) or not math.isfinite(entry["length_mm"]) or entry["length_mm"] <= 0:
            raise ValueError("invalid tuning history length")
    return entries
