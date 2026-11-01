"""Unified offline IQ inspection with a shared frequency reference."""
import math
import numpy as np
from rf_lab.sdr_lab import _validate_iq
from rf_lab.spectrum_analyzer import analyze_spectrum
from rf_lab.waterfall_detection import analyze_waterfall
from rf_lab.signal_classification import classify_signal

def inspect_signal(iq,rate,fft_size=256,threshold_db=12,marker_hz=0):
    x=_validate_iq(iq)
    if not isinstance(rate,(int,float)) or not math.isfinite(rate) or rate<=0:
        raise ValueError("invalid sample rate")
    if not isinstance(marker_hz,(int,float)) or not math.isfinite(marker_hz) or not -rate/2<=marker_hz<rate/2:
        raise ValueError("marker outside Nyquist interval")
    if type(fft_size)!=int or fft_size not in (128,256,512,1024,2048) or fft_size>len(x):
        raise ValueError("invalid FFT size")
    spectrum=analyze_spectrum(x,rate,fft_size=fft_size,peak_threshold_db=threshold_db)
    waterfall=analyze_waterfall(x,rate,fft_size=fft_size,threshold_db=threshold_db)
    classification=None
    try:
        classification=classify_signal(x,rate)
    except ValueError:
        pass  # Silence has no defensible modulation label.
    freq=spectrum["frequency_hz"]
    index=int(np.argmin(np.abs(freq-marker_hz)))
    return {"spectrum":spectrum,"waterfall":waterfall,"classification":classification,
            "marker":{"requested_hz":float(marker_hz),"frequency_hz":float(freq[index]),
                      "psd_db_hz":float(spectrum["psd_db_hz"][index])},
            "sample_rate_hz":float(rate),"samples":len(x)}

def report_rows(result):
    """Plain JSON-safe report data; do not include raw IQ or large chart arrays."""
    s=result["spectrum"]
    w=result["waterfall"]
    c=result["classification"]
    return {"schema_version":1,"sample_rate_hz":result["sample_rate_hz"],
            "sample_count":result["samples"],"marker":result["marker"],
            "spectrum":{"noise_floor_db_hz":s["noise_floor_db_hz"],
                        "occupied_bandwidth_hz":s["occupied_bandwidth_hz"],
                        "resolution_hz":s["resolution_hz"],"peaks":s["peaks"]},
            "waterfall":{"noise_floor_db_hz":w["noise_floor_db_hz"],
                         "activity_frames":w["activity_frames"],
                         "total_frames":w["total_frames"],"events":w["events"]},
            "classification":None if c is None else
                {"label":c["label"],"uncertain":c["uncertain"],
                 "scores":c["scores"],"features":c["features"],
                 "explanation":c["explanation"]},
            "limitations":"Offline relative-power estimates and heuristic labels; no calibrated dBm or verified modulation identification."}
