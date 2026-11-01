"""Construction assistant regression tests."""
import math
import pytest
from rf_lab.yagi import design_yagi
from rf_lab.construction import construction_plan, printable_plan_pdf

def test_cutting_schedule_and_allowance():
    design=design_yagi(146,12)
    plan=construction_plan(design,10)
    assert len(plan["cuts"])==3
    assert sum(c["quantity"] for c in plan["cuts"])==4
    assert all(math.isclose(c["initial_cut_m"]-c["nominal_m"],.01)
               for c in plan["cuts"])
    arms=next(c for c in plan["cuts"] if c["part"]=="Driven arm")
    driven=next(e for e in design.elements if e.name=="Driven")
    assert math.isclose(arms["nominal_m"]*2+design.feed_gap_m,driven.length_m)
    assert plan["positions"][0]==("Reflector",0.0)

def test_allowance_validation():
    design=design_yagi(146)
    for value in (-1,101,float("nan"),float("inf")):
        with pytest.raises(ValueError):
            construction_plan(design,value)

@pytest.mark.parametrize("unit",["cm","in","mm"])
def test_pdf_packet(unit):
    pdf=printable_plan_pdf(construction_plan(design_yagi(146),5),unit)
    assert pdf.startswith(b"%PDF")
    assert len(pdf)>1500

def test_unsupported_unit():
    with pytest.raises(ValueError):
        printable_plan_pdf(construction_plan(design_yagi(146)),"ft")
