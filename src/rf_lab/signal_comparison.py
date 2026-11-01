"""Bounded, transparent comparison of two offline complex-IQ recordings."""
import math
import numpy as np
from rf_lab.signal_dashboard import inspect_signal

def compare_recordings(iq_before,iq_after,rate_before,rate_after,fft_size=256,threshold_db=12):
    """Compare physical frequency offsets; never equate bins from different sample rates."""
    if not all(isinstance(v,(int,float)) and math.isfinite(v) and v>0 for v in (rate_before,rate_after)):
        raise ValueError("sample rates must be finite and positive")
    before=inspect_signal(iq_before,rate_before,fft_size,threshold_db)
    after=inspect_signal(iq_after,rate_after,fft_size,threshold_db)
    bs,az=before["spectrum"],after["spectrum"]
    common=min(rate_before,rate_after)/2
    # Same frequencies in Hz, using interpolation on a shared grid.
    f=np.linspace(-common+common/256,common-common/256,512)
    b=np.interp(f,bs["frequency_hz"],bs["psd_db_hz"])
    a=np.interp(f,az["frequency_hz"],az["psd_db_hz"])
    delta=a-b
    cb=before["classification"]
    ca=after["classification"]
    return {"before":before,"after":after,"frequency_hz":f,
            "before_db_hz":b,"after_db_hz":a,"delta_db":delta,
            "metrics":{"bandwidth_before_hz":bs["occupied_bandwidth_hz"],
                       "bandwidth_after_hz":az["occupied_bandwidth_hz"],
                       "bandwidth_change_hz":az["occupied_bandwidth_hz"]-bs["occupied_bandwidth_hz"],
                       "noise_floor_change_db":az["noise_floor_db_hz"]-bs["noise_floor_db_hz"],
                       "peak_count_before":len(bs["peaks"]),"peak_count_after":len(az["peaks"]),
                       "event_count_before":len(before["waterfall"]["events"]),
                       "event_count_after":len(after["waterfall"]["events"]),
                       "classification_before":cb["label"] if cb else None,
                       "classification_after":ca["label"] if ca else None},
            "limitations":"Relative PSD only; different gains, sample rates, filters and capture conditions may invalidate physical comparisons."}

def comparison_report(result):
    """Small JSON-safe comparison summary, excluding raw IQ and full PSD arrays."""
    from rf_lab.signal_dashboard import report_rows
    return {"schema_version":1,"before":report_rows(result["before"]),
            "after":report_rows(result["after"]),"metrics":result["metrics"],
            "limitations":result["limitations"]}
