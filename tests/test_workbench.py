import math
import pytest
from rf_lab.measurements import S1P, parse_s1p, reflection, line_input_gamma
from rf_lab.workbench import (
    shift_reference_plane, resonance_frequencies_hz,
    summarize_sweep, compare_sweeps,
)

def sample(zs=(40-10j, 50+0j, 60+10j)):
    return S1P((145e6, 146e6, 147e6),
               tuple(reflection(z) for z in zs), 50)

def test_shift_undoes_cable_phase():
    original = sample()
    measured = S1P(original.frequencies_hz,
        tuple(line_input_gamma(z, f/1e6, 2, .66, z0=50)
              for z, f in zip((40-10j, 50, 60+10j), original.frequencies_hz)), 50)
    restored = shift_reference_plane(measured, 2, .66)
    assert restored.gamma == pytest.approx(original.gamma, abs=1e-12)

def test_zero_shift_identity():
    s = sample()
    assert shift_reference_plane(s, 0) == s

def test_loss_correction():
    s = S1P((146e6,), (0.2+0j,), 50)
    shifted = shift_reference_plane(s, 100, loss_db_per_100m=3)
    assert abs(shifted.gamma[0]) == pytest.approx(0.2 * 10**0.3)

@pytest.mark.parametrize("length,vf,loss", [
    (float("nan"), .66, 0), (1, 0, 0), (1, 1.1, 0),
    (1, .66, -1), (-1, .66, 1),
])
def test_invalid_shift(length,vf,loss):
    with pytest.raises(ValueError):
        shift_reference_plane(sample(), length, vf, loss)

def test_resonance_exact_and_crossing():
    s = sample()
    assert resonance_frequencies_hz(s) == pytest.approx([146e6])

def test_resonance_interpolation():
    s = S1P((145e6,147e6), (reflection(50-10j), reflection(50+30j)), 50)
    assert resonance_frequencies_hz(s) == pytest.approx([145.5e6])

def test_no_crossing():
    assert resonance_frequencies_hz(sample((50+1j, 50+2j, 50+3j))) == []

def test_invalid_reflection_skipped():
    s = S1P((145e6, 146e6), (1+0j, reflection(50)), 50)
    assert resonance_frequencies_hz(s) == [146e6]

def test_comparisons_different_grids():
    s1 = sample()
    s2 = parse_s1p("# MHZ S RI R 50\n144 0.2 0\n148 0.1 0")
    results = compare_sweeps({"before":s1, "after":s2})
    assert len(results) == 2
    assert results[0].best_match_mhz == pytest.approx(146)
    assert results[1].best_match_mhz == pytest.approx(148)

def test_summary_nonpassive():
    s = S1P((145e6,), (1+0j,), 50)
    assert summarize_sweep("test",s).minimum_swr is None

def test_empty_comparison():
    with pytest.raises(ValueError):
        compare_sweeps({})

def test_pdf_bytes():
    from rf_lab.reporting import create_measurement_pdf
    result = create_measurement_pdf({"before":sample()}, 146, "Test antenna")
    assert result.startswith(b"%PDF")
    assert len(result) > 1500

def test_pdf_invalid():
    from rf_lab.reporting import create_measurement_pdf
    with pytest.raises(ValueError):
        create_measurement_pdf({}, 146)
    with pytest.raises(ValueError):
        create_measurement_pdf({"a":sample()}, 0)
