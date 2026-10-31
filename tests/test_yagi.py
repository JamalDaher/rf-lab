import math
import pytest
from rf_lab.yagi import design_yagi, cutting_list, INCH_PER_M

def test_three_elements_and_order():
    d = design_yagi(146)
    assert [e.name for e in d.elements] == ["Reflector", "Driven", "Director"]
    assert [e.position_m for e in d.elements] == sorted(e.position_m for e in d.elements)
    assert d.elements[0].length_m > d.elements[1].length_m > d.elements[2].length_m

def test_frequency_scaling():
    a, b = design_yagi(146), design_yagi(292)
    assert b.boom_length_m == pytest.approx(a.boom_length_m / 2)
    assert b.elements[0].length_m == pytest.approx(a.elements[0].length_m / 2)

def test_cutting_list_and_gap():
    d = design_yagi(146, 12)
    rows = cutting_list(d)
    assert len(rows) == 3
    assert sum(r["quantity"] for r in rows) == 4
    assert 2 * rows[1]["length_m"] + d.feed_gap_m == pytest.approx(d.elements[1].length_m)
    assert rows[0]["length_in"] == pytest.approx(rows[0]["length_m"] * INCH_PER_M)

def test_boom_matches_last_element():
    d = design_yagi(146)
    assert d.boom_length_m == d.elements[-1].position_m

@pytest.mark.parametrize("f", [0, -1, float("nan"), float("inf")])
def test_invalid_frequency(f):
    with pytest.raises(ValueError): design_yagi(f)

@pytest.mark.parametrize("gap", [0, -1, float("nan"), float("inf"), 10000])
def test_invalid_gap(gap):
    with pytest.raises(ValueError): design_yagi(146, gap)

def test_70cm():
    assert 0.3 < design_yagi(435).elements[0].length_m < 0.4
