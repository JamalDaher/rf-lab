"""Strict extraction of NEC-2c radiation tables and normalized pattern cuts.

Angles follow NEC spherical coordinates: theta from +z, phi about z.
For a z-oriented Yagi, the theta=90 plane is the horizontal (x/y) cut.
This module does not equate NEC gain with directivity automatically.
"""
from dataclasses import dataclass
import math
import re
import numpy as np

NUMBER=r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?"
ROW=re.compile(r"^\s*("+NUMBER+r")\s+("+NUMBER+r")\s+("+NUMBER+r")\s+("+NUMBER+r")(?:\s|$)")

@dataclass(frozen=True)
class PatternCut:
    phi_deg: np.ndarray
    gain_dbi: np.ndarray
    relative_db: np.ndarray
    theta_deg: float

def parse_nec2_radiation_cut(output: str, theta_deg: float=90.0) -> PatternCut:
    """Parse the theta-constant cut from NEC's RADIATION PATTERNS table.

    NEC standard gain rows start THETA PHI VERT(dB) HORIZ(dB) TOTAL(dB)...
    We require the TOTAL DB header and take the *fifth* numeric field,
    not either polarization gain. Fail if the table is ambiguous.
    """
    if not math.isfinite(theta_deg) or not 0<=theta_deg<=180:
        raise ValueError("invalid theta")
    sections=re.split(r"RADIATION PATTERNS",output,flags=re.I)
    if len(sections)<2:
        raise ValueError("NEC radiation-pattern section not found")
    candidates=[]
    for section in sections[1:]:
        lines=section.splitlines()
        header_index=next((i for i,line in enumerate(lines)
                           if "THETA" in line.upper() and "PHI" in line.upper()),None)
        if header_index is None:
            continue
        rows=[]
        started=False
        for line in lines[header_index+1:]:
            if re.search(r"^(?:\s*(?:AVERAGE POWER GAIN|ANTENNA INPUT PARAMETERS|STRUCTURE|FREQUENCY|RADIATION PATTERNS))",line,re.I):
                if started:
                    break
            parts=line.replace("D+","E+").replace("D-","E-").split()
            if len(parts)<5:
                if started and not line.strip():
                    break
                continue
            try:
                theta,phi=float(parts[0]),float(parts[1])
                gain=float(parts[4])
            except ValueError:
                continue
            if not all(math.isfinite(v) for v in (theta,phi,gain)):
                raise ValueError("nonfinite NEC radiation gain")
            started=True
            if abs(theta-theta_deg)<1e-3:
                rows.append((phi,gain))
        if rows:
            candidates.append(rows)
    if len(candidates)!=1:
        raise ValueError("NEC radiation cut missing or ambiguous")
    rows=sorted(candidates[0])
    angles=np.array([x[0] for x in rows])
    gain=np.array([x[1] for x in rows])
    if len(angles)<3 or np.any(np.diff(angles)<=0):
        raise ValueError("NEC radiation cut requires distinct angles")
    return PatternCut(angles,gain,gain-np.max(gain),theta_deg)

def compare_pattern_cut(model_angles,model_relative_db,nec: PatternCut) -> dict:
    """Compare sampled normalized patterns only over common angular coverage."""
    a=np.asarray(model_angles,dtype=float)
    g=np.asarray(model_relative_db,dtype=float)
    if a.ndim!=1 or g.shape!=a.shape or len(a)<2 or not np.all(np.isfinite(a)) or not np.all(np.isfinite(g)) or np.any(np.diff(a)<=0):
        raise ValueError("invalid model pattern")
    if nec.phi_deg[0]<a[0] or nec.phi_deg[-1]>a[-1]:
        raise ValueError("NEC angles outside model range")
    predicted=np.interp(nec.phi_deg,a,g)
    delta=predicted-nec.relative_db
    return {"pattern_rms_error_db":float(np.sqrt(np.mean(delta**2))),
            "pattern_max_error_db":float(np.max(np.abs(delta))),
            "pattern_angles_deg":nec.phi_deg.tolist(),
            "nec_relative_db":nec.relative_db.tolist(),
            "model_relative_db":predicted.tolist()}
