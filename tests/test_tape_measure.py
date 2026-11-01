"""Tests for portable tape-measure Yagi builder."""
import math
import pytest
from rf_lab.tape_measure import tape_measure_plan
from rf_lab.construction import printable_plan_pdf

def test_tape_blade_quantity_and_gap():
    design,plan=tape_measure_plan()
    assert sum(c["quantity"] for c in plan["cuts"])==4
    assert math.isclose(plan["total_tape_m"],sum(
        c["quantity"]*c["initial_cut_m"] for c in plan["cuts"]))
    driven=next(e for e in design.elements if e.name=="Driven")
    arm=next(c for c in plan["cuts"] if c["part"]=="Driven arm")
    assert math.isclose(arm["nominal_m"]*2+design.feed_gap_m,driven.length_m)

def test_boom_reference_and_margin():
    design,plan=tape_measure_plan(146,12,10,75)
    assert math.isclose(plan["boom_stock_m"],design.boom_length_m+.15)
    assert math.isclose(plan["positions_from_boom_end"][0][1],.075)
    assert math.isclose(plan["positions_from_boom_end"][-1][1],
                        design.boom_length_m+.075)

@pytest.mark.parametrize("bad",[-1,501,float("nan"),float("inf")])
def test_invalid_boom_margin(bad):
    with pytest.raises(ValueError):
        tape_measure_plan(boom_end_margin_mm=bad)

def test_invalid_width_and_mount():
    with pytest.raises(ValueError):
        tape_measure_plan(tape_width_mm=0)
    with pytest.raises(ValueError):
        tape_measure_plan(mount="unknown")

def test_mount_choices_and_pdf():
    for mount in ("PVC cross fittings","Insulated brackets"):
        _,plan=tape_measure_plan(mount=mount)
        assert len(plan["materials"])==8
        assert len(plan["steps"])==9
        assert printable_plan_pdf(plan,"in").startswith(b"%PDF")
