import math
import pytest
from rf_lab.core import (dipole_length_m, quarter_wave_m, swr, return_loss_db,
                         watts_to_dbm, dbm_to_watts, free_space_path_loss_db)

def test_dipole():
    assert dipole_length_m(146) == pytest.approx(0.97535, rel=0.001)
def test_vertical():
    assert quarter_wave_m(146) == pytest.approx(dipole_length_m(146)/2)
def test_matched():
    assert swr(50) == 1
def test_mismatch():
    assert swr(75) == pytest.approx(1.5)
def test_reactive():
    assert swr(50+25j) > 1
def test_short():
    assert math.isinf(swr(0))
def test_return_loss():
    assert math.isinf(return_loss_db(50))
def test_power():
    assert watts_to_dbm(1) == pytest.approx(30)
    assert dbm_to_watts(30) == pytest.approx(1)
def test_path_loss():
    assert free_space_path_loss_db(1000,1) == pytest.approx(92.4478,abs=0.01)
def test_invalid():
    with pytest.raises(ValueError): dipole_length_m(0)
