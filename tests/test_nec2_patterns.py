import numpy as np
import pytest
from rf_lab.nec2_patterns import parse_nec2_radiation_cut,compare_pattern_cut

# Synthetic NEC-style table; this is NOT a real solver benchmark.
SYNTHETIC="""RADIATION PATTERNS
 THETA PHI VERTICAL HORIZONTAL TOTAL AXIAL
 DEGREES DEGREES DB DB DB RATIO
 90.00 0.00 -99.00 -3.00 -3.00 0.00
 90.00 90.00 -99.00 1.00 1.00 0.00
 90.00 180.00 -99.00 -2.00 -2.00 0.00
"""

def test_parse_normalized_cut():
    cut=parse_nec2_radiation_cut(SYNTHETIC)
    assert cut.theta_deg==90
    assert cut.phi_deg.tolist()==[0,90,180]
    assert cut.gain_dbi.tolist()==[-3,1,-2]
    assert cut.relative_db.tolist()==[-4,0,-3]

def test_pattern_difference():
    cut=parse_nec2_radiation_cut(SYNTHETIC)
    result=compare_pattern_cut([0,90,180,360],[-4,0,-3,-4],cut)
    assert result["pattern_rms_error_db"]==pytest.approx(0)

def test_no_pattern_fails():
    with pytest.raises(ValueError,match="section"):
        parse_nec2_radiation_cut("No radiation here")

def test_ambiguous_sections_fail():
    with pytest.raises(ValueError,match="ambiguous"):
        parse_nec2_radiation_cut(SYNTHETIC+SYNTHETIC)

def test_invalid_angular_range():
    cut=parse_nec2_radiation_cut(SYNTHETIC)
    with pytest.raises(ValueError,match="outside"):
        compare_pattern_cut([10,90,180],[-4,0,-3],cut)
