"""NanoVNA analysis: reference-plane shifts, resonance and sweep comparison.

All processing is in-memory. A positive reference-plane shift moves the
measurement plane TOWARD the DUT through a uniform cable.
"""
from dataclasses import dataclass
import cmath
import math

from rf_lab.measurements import C, S1P, impedance_from_gamma, swr_from_gamma, best_match


def shift_reference_plane(sweep: S1P, length_m: float,
                          velocity_factor: float = 0.66,
                          loss_db_per_100m: float = 0.0) -> S1P:
    """Remove the modeled round-trip cable phase and optional attenuation.

    Negative length shifts away from the DUT. Loss correction is only
    supported toward the DUT, and can amplify measurement noise.
    """
    if not math.isfinite(length_m):
        raise ValueError("length must be finite")
    if not math.isfinite(velocity_factor) or not 0 < velocity_factor <= 1:
        raise ValueError("velocity factor must be in (0, 1]")
    if not math.isfinite(loss_db_per_100m) or loss_db_per_100m < 0:
        raise ValueError("loss must be finite and nonnegative")
    if length_m < 0 and loss_db_per_100m:
        raise ValueError("loss correction for negative shifts is unsupported")
    correction = 10 ** (loss_db_per_100m * length_m / 1000)
    if not math.isfinite(correction):
        raise ValueError("loss correction is too large")
    corrected = []
    for f, gamma in zip(sweep.frequencies_hz, sweep.gamma):
        phase = 4 * math.pi * f * length_m / (C * velocity_factor)
        g = gamma * correction * cmath.exp(1j * phase)
        if not math.isfinite(g.real) or not math.isfinite(g.imag):
            raise ValueError("nonfinite corrected reflection coefficient")
        corrected.append(g)
    return S1P(sweep.frequencies_hz, tuple(corrected), sweep.reference_ohm)


def resonance_frequencies_hz(sweep: S1P) -> list[float]:
    """Find zero-reactance crossings by linear interpolation between samples.

    Points with |S11| >= 1 are skipped because impedance is infinite or
    nonpassive. Exact-zero points are included without duplication.
    """
    samples = []
    for f, gamma in zip(sweep.frequencies_hz, sweep.gamma):
        if abs(gamma) >= 1:
            samples.append(None)
            continue
        try:
            z = impedance_from_gamma(gamma, sweep.reference_ohm)
        except ValueError:
            samples.append(None)
            continue
        samples.append(z.imag)
    roots = []
    for i, x in enumerate(samples):
        if x is None:
            continue
        if abs(x) <= 1e-12:
            roots.append(sweep.frequencies_hz[i])
        if i and samples[i-1] is not None:
            previous = samples[i-1]
            if previous * x < 0:
                f0, f1 = sweep.frequencies_hz[i-1:i+1]
                roots.append(f0 + (f1-f0) * (-previous) / (x-previous))
    return sorted(set(roots))


@dataclass(frozen=True)
class SweepSummary:
    name: str
    points: int
    best_match_mhz: float | None
    minimum_swr: float | None
    resonances_mhz: tuple[float, ...]


def summarize_sweep(name: str, sweep: S1P) -> SweepSummary:
    if not name.strip():
        raise ValueError("sweep name is required")
    try:
        freq, swr = best_match(sweep)
        best = freq / 1e6
    except ValueError:
        best, swr = None, None
    return SweepSummary(name, len(sweep.gamma), best, swr,
                        tuple(f/1e6 for f in resonance_frequencies_hz(sweep)))


def compare_sweeps(sweeps: dict[str, S1P]) -> list[SweepSummary]:
    """Compare independent sweeps without assuming identical frequency grids."""
    if not sweeps:
        raise ValueError("at least one sweep is required")
    return [summarize_sweep(name, sweep) for name, sweep in sweeps.items()]
