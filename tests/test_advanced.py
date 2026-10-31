import math
import pytest
from rf_lab.advanced import (
    COAX_DB_PER_100FT_100MHZ, gamma_from_impedance, smith_coordinates,
    coax_loss_db, delivered_power_w, l_match_solutions, matched_input_impedance,
)

def test_smith_matched():
    assert smith_coordinates(50) == pytest.approx((0, 0))

def test_smith_resistive():
    assert smith_coordinates(100) == pytest.approx((1/3, 0))

def test_smith_reactive():
    x, y = smith_coordinates(50 + 50j)
    assert x == pytest.approx(0.2)
    assert y == pytest.approx(0.4)

def test_smith_passivity():
    for z in (0, 25, 50+80j, 200-10j):
        assert abs(gamma_from_impedance(z)) <= 1 + 1e-12

@pytest.mark.parametrize("z", [-10, complex(float("nan"), 0)])
def test_invalid_impedance(z):
    with pytest.raises(ValueError): smith_coordinates(z)

def test_coax_reference_and_scaling():
    assert coax_loss_db("RG-58", 100, 100) == pytest.approx(4.9)
    assert coax_loss_db("RG-58", 400, 100) == pytest.approx(9.8)
    assert coax_loss_db("RG-58", 100, 0) == 0

def test_power_attenuation():
    assert delivered_power_w(100, 3.01029995664) == pytest.approx(50)

@pytest.mark.parametrize("coax, freq, length", [
    ("invalid", 100, 10), ("RG-58", 0, 10),
    ("RG-58", 100, -1), ("RG-58", float("nan"), 10),
])
def test_invalid_coax(coax, freq, length):
    with pytest.raises(ValueError): coax_loss_db(coax, freq, length)

@pytest.mark.parametrize("source,load", [(50, 200), (200, 50), (50, 100), (100, 25)])
def test_l_match_both_solutions(source, load):
    matches = l_match_solutions(source, load, 146)
    assert len(matches) == 2
    for network in matches:
        assert matched_input_impedance(network, load) == pytest.approx(complex(source, 0), abs=1e-9)
        assert network.series_value > 0
        assert network.shunt_value > 0

def test_l_match_equal():
    assert l_match_solutions(50, 50, 146) == []

@pytest.mark.parametrize("source,load,freq", [
    (0, 50, 146), (50, -1, 146), (50, 100, 0),
])
def test_invalid_match(source, load, freq):
    with pytest.raises(ValueError): l_match_solutions(source, load, freq)
