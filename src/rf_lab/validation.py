"""Numerical validation diagnostics for RF Lab's experimental EFIE model.

A mesh sensitivity check is not an accuracy certificate. Analytical short-dipole
directivity is a separate integration sanity check, not a solver benchmark.
"""
from dataclasses import dataclass
import math
import numpy as np
from .mom import solve_yagi_mom

@dataclass(frozen=True)
class MeshRow:
    segments: int
    impedance_ohm: complex
    swr: float
    directivity_dbi: float
    front_to_back_db: float
    condition_number: float
    relative_impedance_change: float | None
    directivity_change_db: float | None

@dataclass(frozen=True)
class ValidationReport:
    rows: tuple[MeshRow, ...]
    max_relative_impedance_change: float
    max_directivity_change_db: float
    numerically_stable: bool
    warning: str

def mesh_sensitivity(frequency_mhz, lengths_m, positions_m,
                     wire_radius_mm=2.0, meshes=(5, 7, 9, 11),
                     impedance_tolerance=0.05, directivity_tolerance_db=0.25):
    """Run multiple discretizations; stability is necessary, not sufficient, for accuracy."""
    if not meshes or len(meshes) < 2 or len(set(meshes)) != len(meshes):
        raise ValueError("at least two distinct meshes required")
    if list(meshes) != sorted(meshes):
        raise ValueError("meshes must be increasing")
    if not (math.isfinite(impedance_tolerance) and impedance_tolerance > 0
            and math.isfinite(directivity_tolerance_db) and directivity_tolerance_db > 0):
        raise ValueError("tolerances must be positive and finite")
    rows = []
    previous = None
    for count in meshes:
        result = solve_yagi_mom(frequency_mhz, lengths_m, positions_m,
                                wire_radius_mm=wire_radius_mm,
                                segments_per_element=count)
        if previous is None:
            rel = None
            delta_db = None
        else:
            rel = abs(result.feed_impedance_ohm-previous.feed_impedance_ohm)/max(
                abs(result.feed_impedance_ohm),abs(previous.feed_impedance_ohm),1e-12)
            delta_db = abs(result.directivity_dbi-previous.directivity_dbi)
        rows.append(MeshRow(count,result.feed_impedance_ohm,result.swr,
                            result.directivity_dbi,result.front_to_back_db,
                            result.condition_number,rel,delta_db))
        previous = result
    changes = [r.relative_impedance_change for r in rows[1:]]
    dchanges = [r.directivity_change_db for r in rows[1:]]
    max_rel = max(changes)
    max_db = max(dchanges)
    stable = max_rel <= impedance_tolerance and max_db <= directivity_tolerance_db
    return ValidationReport(tuple(rows),float(max_rel),float(max_db),bool(stable),
        "Mesh stability is NOT physical validation. Compare with NEC reference "
        "solutions and measurements before trusting impedance, SWR or gain.")

def short_dipole_directivity_check(samples=721):
    """Independent angular-integration check: sin²(theta) has directivity 1.5."""
    if not isinstance(samples,int) or isinstance(samples,bool) or samples < 21:
        raise ValueError("samples must be integer >=21")
    theta = np.linspace(0,np.pi,samples)
    power = np.sin(theta)**2
    integrate = getattr(np,"trapezoid",None)
    if integrate is None:
        integrate = np.trapz
    integral = 2*np.pi*integrate(power*np.sin(theta),theta)
    numerical = 4*np.pi/integral
    return {"numerical_linear":float(numerical),
            "reference_linear":1.5,
            "absolute_error":float(abs(numerical-1.5)),
            "reference_dbi":float(10*np.log10(1.5))}
