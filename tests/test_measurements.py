import cmath
import math
import pytest
from rf_lab.measurements import (
    reflection, impedance_from_gamma, line_input_gamma, line_input_impedance,
    smith_grid, parse_s1p, swr_from_gamma, return_loss_from_gamma,
    best_match, comparison_mhz,
)

def test_quarter_wave_transform():
    f, vf, z0 = 100, 0.8, 50
    length = 299792458 * vf / (f*1e6) / 4
    assert line_input_impedance(100, f, length, vf, z0=z0) == pytest.approx(25+0j, abs=1e-8)

def test_half_wave_repeat():
    f, vf = 146, 0.66
    length = 299792458*vf/(f*1e6)/2
    assert line_input_impedance(75+20j, f, length, vf) == pytest.approx(75+20j, abs=1e-8)

def test_matched_line():
    assert line_input_impedance(50, 146, 100) == pytest.approx(50+0j)
    assert line_input_gamma(50, 146, 100) == 0j

def test_loss_reduces_reflection():
    assert abs(line_input_gamma(100, 146, 20, loss_db_per_100m=20)) < abs(line_input_gamma(100, 146, 20))

@pytest.mark.parametrize("length,vf,loss", [(-1,.66,0), (1,0,0), (1,1.1,0), (1,.66,-1)])
def test_invalid_line(length,vf,loss):
    with pytest.raises(ValueError): line_input_gamma(75,146,length,vf,loss)

def test_smith_grid():
    paths = smith_grid()
    assert len(paths) == 16
    assert all(abs(p) <= 1.000001 for _, pts in paths for p in pts)

def test_gamma_roundtrip():
    z = 43+27j
    assert impedance_from_gamma(reflection(z)) == pytest.approx(z)

@pytest.mark.parametrize("fmt,row,expected", [
    ("RI", "100 0.2 0.4", 0.2+0.4j),
    ("MA", "100 0.5 90", 0+0.5j),
    ("DB", "100 -6.020599913 180", -0.5+0j),
])
def test_touchstone_formats(fmt,row,expected):
    s = parse_s1p(f"# MHZ S {fmt} R 50\n{row}\n")
    assert s.frequencies_hz == pytest.approx((100e6,))
    assert s.gamma[0] == pytest.approx(expected, abs=1e-8)

def test_touchstone_comments_and_default():
    s = parse_s1p("! comment\n# GHZ S MA R 75\n0.146 0.2 0 ! note\n0.147 0.1 0\n")
    assert s.reference_ohm == 75
    assert best_match(s) == pytest.approx((147e6, 1.1/.9))

def test_comparison():
    s = parse_s1p("# MHZ S RI R 50\n145 0.3 0\n146 0.1 0\n147 0.2 0")
    assert comparison_mhz(s, 145.5) == pytest.approx((146, .5))

@pytest.mark.parametrize("text", [
    "", "# MHZ Z RI R 50\n100 0 0", "# MHZ S RI R 50\n100 0 0\n99 0 0",
    "# MHZ S RI R 50\n100 nan 0", "# MHZ S RI R 50\n100 0",
    "[Version] 2.0\n# MHZ S RI R 50\n100 0 0",
])
def test_touchstone_invalid(text):
    with pytest.raises(ValueError): parse_s1p(text)

def test_swr_and_return_loss():
    assert swr_from_gamma(0) == 1
    assert math.isinf(return_loss_from_gamma(0))
    assert swr_from_gamma(.5) == pytest.approx(3)
    assert return_loss_from_gamma(.1) == pytest.approx(20)
