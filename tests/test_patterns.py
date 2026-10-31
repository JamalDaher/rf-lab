import numpy as np
import pytest
from rf_lab.patterns import (field_pattern, power_pattern, pattern_db,
                             radiation_mesh, elevation_cut, azimuth_cut)


@pytest.mark.parametrize("model", ["Half-wave dipole", "Short dipole",
                                   "Quarter-wave vertical (ideal ground)"])
def test_axis_null_and_broadside(model):
    assert field_pattern(0, model) == pytest.approx(0, abs=1e-9)
    assert field_pattern(np.pi/2, model) == pytest.approx(1)


def test_short_dipole_sin_squared():
    assert power_pattern(np.pi/6, "Short dipole") == pytest.approx(.25)


def test_half_wave_symmetry():
    assert field_pattern(np.pi/3) == pytest.approx(field_pattern(2*np.pi/3))


def test_monopole_below_ground():
    assert power_pattern(3*np.pi/4, "Quarter-wave vertical (ideal ground)") == 0


def test_db_floor():
    assert pattern_db(0) == pytest.approx(-40)
    assert pattern_db(np.pi/2) == pytest.approx(0)


def test_mesh_shapes_and_finite():
    x,y,z,r = radiation_mesh(theta_points=15, phi_points=19)
    assert x.shape == y.shape == z.shape == r.shape == (15,19)
    assert np.all(np.isfinite(x))


def test_cuts():
    theta, power = elevation_cut(points=181)
    assert theta[0] == 0 and theta[-1] == pytest.approx(180)
    assert power[90] == pytest.approx(1)
    phi, horizontal = azimuth_cut(elevation_deg=0)
    assert phi[-1] == 360
    assert np.allclose(horizontal, 1)


@pytest.mark.parametrize("call", [
    lambda: field_pattern(0, "Yagi"),
    lambda: field_pattern(float("nan")),
    lambda: pattern_db(0, floor_db=0),
    lambda: radiation_mesh(theta_points=2),
    lambda: azimuth_cut(elevation_deg=91),
])
def test_invalid_inputs(call):
    with pytest.raises(ValueError):
        call()
