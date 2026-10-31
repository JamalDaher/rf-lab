"""Bounded deterministic optimization of an experimental three-element Yagi.

Uses RF Lab's experimental EFIE model. Results are candidate geometries,
NOT validated antenna performance or manufacturing specifications.
"""
from dataclasses import dataclass
import math
import numpy as np
from .mom import solve_yagi_mom,C
from .nec2_runner import generate_yagi_nec2

OBJECTIVES=("match","front_to_back","directivity","balanced")

@dataclass(frozen=True)
class Candidate:
    lengths_m: tuple
    positions_m: tuple
    impedance_ohm: complex
    swr: float
    front_to_back_db: float
    directivity_dbi: float
    score: float

@dataclass(frozen=True)
class OptimizationResult:
    original: Candidate
    best: Candidate
    evaluated: int
    rejected: int
    history: tuple
    objective: str
    frequency_mhz: float
    wire_radius_mm: float
    segments_per_element: int

def score_metrics(z,swr,front_to_back_db,directivity_dbi,objective):
    if objective not in OBJECTIVES:
        raise ValueError("unsupported objective")
    if not all(math.isfinite(x) for x in (z.real,z.imag,front_to_back_db,directivity_dbi)):
        raise ValueError("nonfinite model output")
    # Bounded terms avoid unstable domination by an extreme F/B null.
    match=-min(abs(z-50)/50,20)
    fb=min(max(front_to_back_db,-30),40)/20
    direct=min(max(directivity_dbi,-20),20)/10
    if objective=="match":
        return match
    if objective=="front_to_back":
        return fb
    if objective=="directivity":
        return direct
    return match+0.5*fb+0.5*direct

def optimize_yagi(frequency_mhz,lengths_m,positions_m,objective="balanced",
                  wire_radius_mm=2.0,segments_per_element=7,
                  length_variation=0.08,spacing_variation=0.20,
                  iterations=12,seed=0):
    """Seeded bounded random search; includes original design as a candidate.

    The reflector is fixed at boom position 0. Relative adjacent spacings
    are optimized independently and always remain positive.
    """
    if objective not in OBJECTIVES:
        raise ValueError("unsupported objective")
    if type(iterations)!=int or not 1<=iterations<=40:
        raise ValueError("iterations must be 1..40")
    if type(seed)!=int or not 0<=seed<=2**32-1:
        raise ValueError("seed must be a 32-bit unsigned integer")
    if not all(math.isfinite(x) and 0<=x<=0.30 for x in (length_variation,spacing_variation)):
        raise ValueError("variation limits must be finite and between 0 and 0.30")
    lengths=np.asarray(lengths_m,dtype=float)
    positions=np.asarray(positions_m,dtype=float)
    if lengths.shape!=(3,) or positions.shape!=(3,) or not np.all(np.isfinite(lengths)) or not np.all(np.isfinite(positions)):
        raise ValueError("three finite lengths and positions required")
    if not np.all(lengths>0) or not np.all(np.diff(positions)>0):
        raise ValueError("invalid starting Yagi geometry")
    if not math.isclose(positions[0],0,abs_tol=1e-10):
        raise ValueError("reflector boom position must be zero")
    # Validate the original using the same NEC deck rules as exports.
    generate_yagi_nec2(frequency_mhz,lengths,positions,wire_radius_mm,segments_per_element)
    base_gaps=np.diff(positions)
    rng=np.random.default_rng(seed)
    def evaluate(ls,ps):
        model=solve_yagi_mom(frequency_mhz,ls,ps,
                             wire_radius_mm=wire_radius_mm,
                             segments_per_element=segments_per_element)
        return Candidate(tuple(float(x) for x in ls),
                         tuple(float(x) for x in ps),
                         model.feed_impedance_ohm,float(model.swr_50),
                         float(model.front_to_back_db),float(model.directivity_dbi),
                         float(score_metrics(model.feed_impedance_ohm,model.swr_50,
                             model.front_to_back_db,model.directivity_dbi,objective)))
    original=evaluate(lengths,positions)
    best=original
    history=[{"evaluation":0,"score":original.score,"best_score":original.score,
              "accepted":True}]
    rejected=0
    for index in range(1,iterations+1):
        ls=lengths*(1+rng.uniform(-length_variation,length_variation,size=3))
        gaps=base_gaps*(1+rng.uniform(-spacing_variation,spacing_variation,size=2))
        ps=np.array([0.0,gaps[0],gaps.sum()])
        try:
            generate_yagi_nec2(frequency_mhz,ls,ps,wire_radius_mm,segments_per_element)
            candidate=evaluate(ls,ps)
        except (ValueError,np.linalg.LinAlgError,OverflowError,FloatingPointError):
            rejected+=1
            history.append({"evaluation":index,"score":None,
                            "best_score":best.score,"accepted":False})
            continue
        if candidate.score>best.score:
            best=candidate
        history.append({"evaluation":index,"score":candidate.score,
                        "best_score":best.score,"accepted":True})
    return OptimizationResult(original,best,iterations+1-rejected,rejected,
                              tuple(history),objective,float(frequency_mhz),
                              float(wire_radius_mm),segments_per_element)

def cutting_list(result):
    """Lengths and boom positions in millimeters for review, not final cutting."""
    return [{"element":name,"length_mm":round(length*1000,2),
             "boom_position_mm":round(position*1000,2)}
            for name,length,position in zip(("Reflector","Driven","Director"),
                result.best.lengths_m,result.best.positions_m)]

def optimized_nec_deck(result):
    return generate_yagi_nec2(result.frequency_mhz,result.best.lengths_m,
                              result.best.positions_m,result.wire_radius_mm,
                              result.segments_per_element)
