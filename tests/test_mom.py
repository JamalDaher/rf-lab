import math
import numpy as np
import pytest
from rf_lab.mom import solve_yagi_mom, current_profile


def geometry():
    wavelength=299792458/(146e6)
    return [0.505*wavelength,0.475*wavelength,0.450*wavelength],[0,0.2*wavelength,0.35*wavelength]


def test_solution_shapes_and_finiteness():
    lengths, positions=geometry()
    result=solve_yagi_mom(146,lengths,positions,segments_per_element=5)
    assert result.currents_a.shape==(15,)
    assert result.segment_centers_m.shape==(15,)
    assert np.all(np.isfinite(result.currents_a))
    assert np.all(np.isfinite(result.azimuth_db))
    assert math.isfinite(result.directivity_dbi)
    assert result.condition_number > 0
    assert result.swr_50 >= 1
    assert result.feed_impedance_ohm != 0
    assert current_profile(result)[2].shape==(15,)


def test_pattern_axes():
    lengths,positions=geometry()
    result=solve_yagi_mom(146,lengths,positions,segments_per_element=5)
    assert len(result.azimuth_deg)==361
    assert len(result.elevation_deg)==361
    assert result.azimuth_deg[0]==0
    assert result.azimuth_deg[180]==180


@pytest.mark.parametrize('freq,lengths,positions,radius,segments',[
    (0,[1,1,1],[0,1,2],2,5),
    (146,[1,-1,1],[0,1,2],2,5),
    (146,[1,1,1],[0,2,1],2,5),
    (146,[1,1,1],[0,1,2],100,5),
    (146,[1,1,1],[0,1,2],2,6),
    (146,[1,1,1],[0,1,2],2,33),
])
def test_invalid_inputs(freq,lengths,positions,radius,segments):
    with pytest.raises(ValueError):
        solve_yagi_mom(freq,lengths,positions,wire_radius_mm=radius,segments_per_element=segments)
