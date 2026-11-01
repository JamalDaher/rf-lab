"""Tests for dimensional Yagi drawings (no EM predictions)."""
import math
import pytest
from rf_lab.yagi import design_yagi
from rf_lab.geometry_view import geometry_segments, dimension_rows, geometry_figure

def test_segments_and_feed_gap():
    d=design_yagi(146,12)
    segments=geometry_segments(d)
    assert len(segments)==5
    arms=[s for s in segments if s["kind"]=="driven"]
    assert len(arms)==2
    assert math.isclose(arms[1]["start"][1]-arms[0]["end"][1],d.feed_gap_m)
    assert math.isclose(segments[0]["end"][0],d.boom_length_m)

def test_dimension_units():
    d=design_yagi(146)
    cm=dimension_rows(d,"cm")
    inches=dimension_rows(d,"in")
    assert len(cm)==3
    assert cm[0]["Boom position (cm)"]==0
    assert math.isclose(cm[0]["Length (cm)"]/2.54,
                        inches[0]["Length (in)"],abs_tol=.02)

@pytest.mark.parametrize("view",["3D","Top view"])
def test_plotly_view(view):
    fig=geometry_figure(design_yagi(146),view,"cm")
    assert len(fig.data)==8
    assert fig.layout.title.text.startswith("3-element Yagi")
    assert fig.data[0].type==("scatter3d" if view=="3D" else "scatter")

def test_invalid_inputs():
    d=design_yagi(146)
    with pytest.raises(ValueError):
        geometry_figure(d,"Side","cm")
    with pytest.raises(ValueError):
        dimension_rows(d,"ft")
