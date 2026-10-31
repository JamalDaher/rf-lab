import math
import numpy as np
import pytest
from rf_lab.yagi_optimizer import (
    optimize_yagi,cutting_list,optimized_nec_deck,score_metrics)
from rf_lab.mom import MoMResult

def fake_solver(freq,lengths,positions,**kwargs):
    # Smooth deterministic test surrogate, NOT a physical antenna model.
    z=complex(50+100*(float(lengths[0])-1),0)
    fb=10+float(positions[2])
    d=5+float(lengths[2])
    return type("FakeResult",(),{
        "feed_impedance_ohm":z,"swr_50":1.0,
        "front_to_back_db":fb,"directivity_dbi":d})()

def test_reproducible_and_original_retained(monkeypatch):
    monkeypatch.setattr("rf_lab.yagi_optimizer.solve_yagi_mom",fake_solver)
    args=(146,[1,.95,.9],[0,.3,.55])
    a=optimize_yagi(*args,seed=42,iterations=10)
    b=optimize_yagi(*args,seed=42,iterations=10)
    assert a==b
    assert a.best.score>=a.original.score
    assert a.evaluated+a.rejected==11
    assert len(a.history)==11
    assert a.best.positions_m[0]==0
    assert a.best.positions_m[0]<a.best.positions_m[1]<a.best.positions_m[2]
    assert len(cutting_list(a))==3
    deck=optimized_nec_deck(a)
    assert "GW 1 7" in deck and "EX 0 2" in deck

def test_objective_scores():
    z=complex(50,0)
    assert score_metrics(z,1,10,6,"match")==0
    assert score_metrics(z,1,20,6,"front_to_back")>score_metrics(z,1,10,6,"front_to_back")
    assert score_metrics(z,1,10,8,"directivity")>score_metrics(z,1,10,6,"directivity")

@pytest.mark.parametrize("kwargs",[
    {"iterations":0},{"iterations":41},{"seed":-1},
    {"objective":"magic"},{"length_variation":.4},
    {"spacing_variation":float("nan")},
])
def test_invalid_parameters(kwargs,monkeypatch):
    monkeypatch.setattr("rf_lab.yagi_optimizer.solve_yagi_mom",fake_solver)
    with pytest.raises(ValueError):
        optimize_yagi(146,[1,.95,.9],[0,.3,.55],**kwargs)

def test_reject_invalid_geometry(monkeypatch):
    monkeypatch.setattr("rf_lab.yagi_optimizer.solve_yagi_mom",fake_solver)
    with pytest.raises(ValueError):
        optimize_yagi(146,[1,.95,.9],[.1,.3,.55])
    with pytest.raises(ValueError):
        optimize_yagi(146,[1,.95,.9],[0,.3,.2])

def test_real_efie_smoke():
    wavelength=299792458/(146e6)
    result=optimize_yagi(146,[.505*wavelength,.475*wavelength,.45*wavelength],
        [0,.2*wavelength,.35*wavelength],iterations=1,segments_per_element=5,seed=3)
    assert result.best.score>=result.original.score
    assert math.isfinite(result.best.score)
