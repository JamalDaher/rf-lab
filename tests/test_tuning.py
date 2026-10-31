import pytest
from rf_lab.measurements import S1P, reflection
from rf_lab.tuning import (tuning_advice, tuning_comparison,
                           add_history_entry, history_json, load_history)


def sweep(resonance_mhz=146.0):
    frequencies = tuple((resonance_mhz + d)*1e6 for d in (-1, 0, 1))
    gammas = tuple(reflection(complex(50, d*10)) for d in (-1, 0, 1))
    return S1P(frequencies, gammas, 50)


def test_high_resonance_shortens():
    advice = tuning_advice(sweep(148), 146, 1000, 0)
    assert advice.direction == "lengthen"
    assert advice.estimated_change_mm == pytest.approx(1000*(148/146-1))


def test_low_resonance_lengthens():
    advice = tuning_advice(sweep(144), 146, 1000, 0)
    assert advice.direction == "shorten"
    assert advice.estimated_change_mm < 0


def test_on_target():
    advice = tuning_advice(sweep(146), 146, 1000)
    assert advice.direction == "on target"
    assert advice.estimated_change_mm == 0


def test_missing_resonance():
    s = S1P((145e6, 146e6), (reflection(50+10j), reflection(50+20j)), 50)
    assert tuning_advice(s, 146, 1000).direction == "unknown"


def test_comparison():
    result = tuning_comparison(sweep(145), sweep(146), 146)
    assert result["resonance_error_improvement_mhz"] == pytest.approx(1)
    assert result["minimum_swr_change"] == pytest.approx(0)


def test_history_roundtrip():
    advice = tuning_advice(sweep(146), 146, 1000)
    original = []
    updated = add_history_entry(original, "First", advice, 1000, "Initial", "2026-10-31T10:00:00Z")
    assert original == []
    assert load_history(history_json(updated)) == updated


@pytest.mark.parametrize("text", ["{}", '{"schema_version":2,"entries":[]}', '{"schema_version":1,"entries":[{}]}'])
def test_bad_history(text):
    with pytest.raises(ValueError):
        load_history(text)


@pytest.mark.parametrize("target,length", [(0,1000),(146,0),(-1,1000)])
def test_bad_parameters(target,length):
    with pytest.raises(ValueError):
        tuning_advice(sweep(), target, length)
