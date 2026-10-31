"""Reference comparison framework for independently generated NEC results.

No bundled NEC simulation or unverified numerical benchmark is implied.
"""
from dataclasses import dataclass
import json
import math
from typing import Any
import numpy as np
from .mom import solve_yagi_mom

@dataclass(frozen=True)
class Reference:
    solver: str
    solver_version: str
    source: str
    frequency_mhz: float
    lengths_m: tuple[float,float,float]
    positions_m: tuple[float,float,float]
    wire_radius_mm: float
    segments_per_element: int
    feed_impedance_ohm: complex
    directivity_dbi: float
    front_to_back_db: float | None
    azimuth_deg: np.ndarray | None
    azimuth_db: np.ndarray | None

def load_reference(raw: str | bytes | dict[str,Any]) -> Reference:
    """Load an explicit, provenance-bearing, manually exported NEC benchmark."""
    data = json.loads(raw) if isinstance(raw,(str,bytes)) else raw
    if not isinstance(data,dict):
        raise ValueError("reference must be a JSON object")
    required=("solver","solver_version","source","frequency_mhz","lengths_m",
              "positions_m","wire_radius_mm","segments_per_element",
              "feed_impedance_real_ohm","feed_impedance_imag_ohm","directivity_dbi")
    if any(k not in data for k in required):
        raise ValueError("missing required reference fields")
    if data["solver"] not in ("NEC-2","NEC-4"):
        raise ValueError("reference solver must be NEC-2 or NEC-4")
    for key in ("solver_version","source"):
        if not isinstance(data[key],str) or not data[key].strip():
            raise ValueError(f"{key} must identify benchmark provenance")
    lengths=tuple(float(v) for v in data["lengths_m"])
    positions=tuple(float(v) for v in data["positions_m"])
    if len(lengths)!=3 or len(positions)!=3:
        raise ValueError("reference geometry must have three elements")
    scalar_keys=("frequency_mhz","wire_radius_mm","feed_impedance_real_ohm",
                 "feed_impedance_imag_ohm","directivity_dbi")
    if not all(math.isfinite(float(data[k])) for k in scalar_keys):
        raise ValueError("reference values must be finite")
    if not all(math.isfinite(x) for x in lengths+positions):
        raise ValueError("geometry must be finite")
    if data["frequency_mhz"]<=0 or data["wire_radius_mm"]<=0 or min(lengths)<=0:
        raise ValueError("frequency, radius and lengths must be positive")
    if not (positions[0]<positions[1]<positions[2]):
        raise ValueError("positions must be strictly increasing")
    count=data["segments_per_element"]
    if isinstance(count,bool) or not isinstance(count,int) or count<5 or count>31 or count%2!=1:
        raise ValueError("segments_per_element must be odd between 5 and 31")
    fb=data.get("front_to_back_db")
    if fb is not None and not math.isfinite(float(fb)):
        raise ValueError("front_to_back_db must be finite")
    angles=data.get("azimuth_deg")
    levels=data.get("azimuth_db")
    if (angles is None)!=(levels is None):
        raise ValueError("azimuth angles and levels must be supplied together")
    if angles is not None:
        angles=np.asarray(angles,dtype=float)
        levels=np.asarray(levels,dtype=float)
        if (angles.ndim!=1 or levels.shape!=angles.shape or len(angles)<2
                or not np.all(np.isfinite(angles)) or not np.all(np.isfinite(levels))
                or np.any(np.diff(angles)<=0) or angles[0]<0 or angles[-1]>360):
            raise ValueError("invalid azimuth pattern")
    return Reference(data["solver"],data["solver_version"],data["source"],
        float(data["frequency_mhz"]),lengths,positions,float(data["wire_radius_mm"]),
        count,complex(data["feed_impedance_real_ohm"],data["feed_impedance_imag_ohm"]),
        float(data["directivity_dbi"]),None if fb is None else float(fb),angles,levels)

def compare_reference(reference: Reference):
    """Compare like-for-like geometry; return signed errors, not a pass certificate."""
    result=solve_yagi_mom(reference.frequency_mhz,reference.lengths_m,
                          reference.positions_m,wire_radius_mm=reference.wire_radius_mm,
                          segments_per_element=reference.segments_per_element)
    z_error=result.feed_impedance_ohm-reference.feed_impedance_ohm
    relative=abs(z_error)/max(abs(reference.feed_impedance_ohm),1e-12)
    comparison={
        "reference_solver":reference.solver,
        "reference_version":reference.solver_version,
        "reference_source":reference.source,
        "reference_impedance_ohm":reference.feed_impedance_ohm,
        "model_impedance_ohm":result.feed_impedance_ohm,
        "impedance_absolute_error_ohm":float(abs(z_error)),
        "impedance_relative_error":float(relative),
        "resistance_error_ohm":float(z_error.real),
        "reactance_error_ohm":float(z_error.imag),
        "directivity_error_db":float(result.directivity_dbi-reference.directivity_dbi),
        "front_to_back_error_db":None if reference.front_to_back_db is None else
            float(result.front_to_back_db-reference.front_to_back_db),
        "azimuth_rms_error_db":None,
        "azimuth_model_db":None,
        "azimuth_reference_db":None,
        "azimuth_angles_deg":None,
    }
    if reference.azimuth_deg is not None:
        predicted=np.interp(reference.azimuth_deg,result.azimuth_deg,result.azimuth_db)
        difference=predicted-reference.azimuth_db
        comparison["azimuth_rms_error_db"]=float(np.sqrt(np.mean(difference**2)))
        comparison["azimuth_model_db"]=predicted
        comparison["azimuth_reference_db"]=reference.azimuth_db
        comparison["azimuth_angles_deg"]=reference.azimuth_deg
    return comparison
