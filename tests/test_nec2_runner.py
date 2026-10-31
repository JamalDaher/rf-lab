import pytest
from rf_lab.nec2_runner import generate_yagi_nec2, parse_nec2_input_impedance, run_nec2

def geometry():
    return (146,[1.037,.975,.924],[0,.411,.719])

def test_deck_geometry_and_excitation():
    deck=generate_yagi_nec2(*geometry(),segments_per_element=9)
    assert "GW 1 9" in deck and "GW 2 9" in deck and "GW 3 9" in deck
    assert "EX 0 2 5 0 1 0" in deck
    assert "FR 0 1 0 0 146.000000000 0" in deck
    assert deck.endswith("EN\n")

@pytest.mark.parametrize("kwargs",[
    {"frequency_mhz":0},
    {"lengths_m":[1,-1,1]},
    {"positions_m":[0,2,1]},
    {"wire_radius_mm":0},
    {"segments_per_element":8},
])
def test_invalid_geometry(kwargs):
    freq,lengths,positions=geometry()
    params=dict(frequency_mhz=freq,lengths_m=lengths,positions_m=positions)
    params.update(kwargs)
    with pytest.raises(ValueError):
        generate_yagi_nec2(**params)

def test_missing_nec_table_fails_explicitly():
    with pytest.raises(ValueError,match="not found"):
        parse_nec2_input_impedance("no input data")

def test_missing_solver_fails_explicitly():
    with pytest.raises(ValueError,match="does not exist"):
        run_nec2("EN\n","/this/path/does/not/exist")
