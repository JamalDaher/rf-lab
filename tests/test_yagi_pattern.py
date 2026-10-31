import math
import numpy as np
import pytest
from rf_lab.yagi import design_yagi
from rf_lab.yagi_pattern import coupled_currents, simulate_yagi, yagi_surface


def geometry():
    d=design_yagi(146)
    return [e.length_m for e in d.elements],[e.position_m for e in d.elements]


def test_uncoupled_only_driven():
    lengths,positions=geometry()
    currents=coupled_currents(146,lengths,positions,0)
    assert abs(currents[0]) == pytest.approx(0)
    assert abs(currents[2]) == pytest.approx(0)
    assert abs(currents[1]) > 0


def test_pattern_finite():
    lengths,positions=geometry()
    p=simulate_yagi(146,lengths,positions,samples=61)
    assert len(p.azimuth_deg)==361
    assert len(p.elevation_deg)==361
    assert np.all(np.isfinite(p.azimuth_db))
    assert np.all(np.isfinite(p.elevation_db))
    assert math.isfinite(p.directivity_dbi)
    assert math.isfinite(p.front_to_back_db)


def test_surface():
    lengths,positions=geometry()
    x,y,z,r=yagi_surface(146,lengths,positions,theta_points=13,phi_points=17)
    assert x.shape==y.shape==z.shape==r.shape==(13,17)
    assert np.max(r)==pytest.approx(1)
    assert np.min(r)>=0


@pytest.mark.parametrize("freq,lengths,positions,coupling",[
    (0,[1,1,1],[0,.2,.4],.2),
    (146,[1,-1,1],[0,.2,.4],.2),
    (146,[1,1,1],[0,.4,.2],.2),
    (146,[1,1,1],[0,.2,.4],1),
])
def test_bad_geometry(freq,lengths,positions,coupling):
    with pytest.raises(ValueError):
        simulate_yagi(freq,lengths,positions,coupling,samples=61)


def test_resolution_validation():
    lengths,positions=geometry()
    with pytest.raises(ValueError):
        simulate_yagi(146,lengths,positions,samples=10)
