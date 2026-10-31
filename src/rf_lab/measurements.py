"""Transmission lines, Smith-chart grids and Touchstone S1P measurement data."""
from dataclasses import dataclass
import cmath
import math

C = 299_792_458.0

def _positive(x, name):
    if not math.isfinite(x) or x <= 0:
        raise ValueError(f"{name} must be positive and finite")

def reflection(z: complex, z0: float = 50.0) -> complex:
    _positive(z0, "reference impedance")
    z = complex(z)
    if not all(math.isfinite(v) for v in (z.real, z.imag)) or z.real < 0:
        raise ValueError("load must be finite and passive")
    return (z-z0)/(z+z0)

def impedance_from_gamma(gamma: complex, z0: float = 50.0) -> complex:
    _positive(z0, "reference impedance")
    if not all(math.isfinite(v) for v in (gamma.real, gamma.imag)):
        raise ValueError("reflection coefficient must be finite")
    if abs(gamma) >= 1:
        raise ValueError("finite impedance requires |gamma| < 1")
    return z0 * (1+gamma)/(1-gamma)

def line_input_gamma(load: complex, frequency_mhz: float, length_m: float,
                     velocity_factor: float = 0.66, loss_db_per_100m: float = 0.0,
                     z0: float = 50.0) -> complex:
    """Gamma at source end; loss is matched-line power dB per 100 m."""
    _positive(frequency_mhz, "frequency")
    _positive(z0, "reference impedance")
    if not math.isfinite(length_m) or length_m < 0:
        raise ValueError("length must be nonnegative and finite")
    if not math.isfinite(velocity_factor) or not 0 < velocity_factor <= 1:
        raise ValueError("velocity factor must be in (0, 1]")
    if not math.isfinite(loss_db_per_100m) or loss_db_per_100m < 0:
        raise ValueError("loss must be nonnegative and finite")
    beta = 2 * math.pi * frequency_mhz * 1e6 / (C * velocity_factor)
    # Matched-line power loss in dB; voltage-wave amplitude falls by 10^(-dB/20).
    # Reflection traverses the line twice.
    attenuation = 10 ** (-loss_db_per_100m * length_m / (100 * 10))
    return reflection(load, z0) * attenuation * cmath.exp(-2j * beta * length_m)

def line_input_impedance(load: complex, frequency_mhz: float, length_m: float,
                         velocity_factor: float = 0.66, loss_db_per_100m: float = 0.0,
                         z0: float = 50.0) -> complex:
    gamma = line_input_gamma(load, frequency_mhz, length_m, velocity_factor, loss_db_per_100m, z0)
    if abs(gamma) >= 1 - 1e-14:
        raise ValueError("input impedance is singular or infinite for this configuration")
    return impedance_from_gamma(gamma, z0)

def smith_grid():
    """Smith-chart resistance circles and reactance arcs as Gamma-plane paths."""
    traces = []
    for r in (0, 0.2, 0.5, 1, 2, 5):
        pts = [reflection(complex(r, x), 1) for x in (-1e5 + i*2e5/400 for i in range(401))]
        traces.append((f"r={r:g}", pts))
    # Arcs are generated from normalized positive resistance >= 0.
    for x in (-5, -2, -1, -0.5, -0.2, 0.2, 0.5, 1, 2, 5):
        pts = [reflection(complex(r, x), 1) for r in (i*100/400 for i in range(401))]
        traces.append((f"x={x:g}", pts))
    return traces

@dataclass(frozen=True)
class S1P:
    frequencies_hz: tuple[float, ...]
    gamma: tuple[complex, ...]
    reference_ohm: float

def parse_s1p(text: str) -> S1P:
    """Read standard Touchstone 1-port v1 data: RI, MA or DB; frequency units."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("empty Touchstone file")
    unit = "GHZ"
    fmt = "MA"
    parameter = "S"
    z0 = 50.0
    scales = {"HZ": 1, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}
    frequencies, gammas = [], []
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.split("!", 1)[0].strip()
        if not line:
            continue
        if line.startswith("["):
            raise ValueError("Touchstone v2 sections are not supported")
        if line.startswith("#"):
            parts = line[1:].upper().split()
            i = 0
            while i < len(parts):
                token = parts[i]
                if token in scales:
                    unit = token
                elif token in ("RI", "MA", "DB"):
                    fmt = token
                elif token in ("S", "Y", "Z", "H", "G"):
                    parameter = token
                elif token == "R":
                    i += 1
                    if i >= len(parts):
                        raise ValueError("missing reference impedance")
                    try:
                        z0 = float(parts[i])
                    except ValueError as exc:
                        raise ValueError("invalid reference impedance") from exc
                    _positive(z0, "reference impedance")
                else:
                    raise ValueError(f"unsupported option: {token}")
                i += 1
            if parameter != "S":
                raise ValueError("only S-parameter Touchstone is supported")
            continue
        parts = line.split()
        if len(parts) != 3:
            raise ValueError(f"line {line_no}: expected frequency and two S11 values")
        try:
            f, a, b = map(float, parts)
        except ValueError as exc:
            raise ValueError(f"line {line_no}: nonnumeric data") from exc
        _positive(f, "frequency")
        if not math.isfinite(a) or not math.isfinite(b):
            raise ValueError(f"line {line_no}: nonfinite S11")
        if fmt == "RI":
            g = complex(a, b)
        elif fmt == "MA":
            if a < 0:
                raise ValueError("negative S11 magnitude")
            g = cmath.rect(a, math.radians(b))
        else:
            g = cmath.rect(10**(a/20), math.radians(b))
        if not math.isfinite(g.real) or not math.isfinite(g.imag):
            raise ValueError("nonfinite reflection coefficient")
        frequencies.append(f * scales[unit])
        gammas.append(g)
        if len(frequencies) > 20000:
            raise ValueError("file exceeds 20,000 measurement points")
    if not frequencies:
        raise ValueError("no S11 measurement points found")
    if any(b <= a for a,b in zip(frequencies, frequencies[1:])):
        raise ValueError("frequencies must be strictly increasing")
    return S1P(tuple(frequencies), tuple(gammas), z0)

def swr_from_gamma(g: complex) -> float:
    magnitude = abs(g)
    return math.inf if magnitude >= 1 else (1+magnitude)/(1-magnitude)

def return_loss_from_gamma(g: complex) -> float:
    magnitude = abs(g)
    return math.inf if magnitude == 0 else -20*math.log10(magnitude)

def best_match(measurement: S1P) -> tuple[float, float]:
    """Frequency (Hz), minimum SWR; excludes nonpassive or fully reflective points."""
    candidates = [(swr_from_gamma(g), f) for f,g in zip(measurement.frequencies_hz, measurement.gamma) if abs(g) < 1]
    if not candidates:
        raise ValueError("no valid finite-SWR measurement points")
    value, freq = min(candidates)
    return freq, value

def comparison_mhz(measurement: S1P, design_mhz: float) -> tuple[float, float]:
    _positive(design_mhz, "design frequency")
    freq, _ = best_match(measurement)
    measured = freq / 1e6
    return measured, measured-design_mhz
