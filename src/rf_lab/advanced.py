"""RF matching and transmission-line engineering calculations.

Ideal lumped elements; coax attenuation figures are illustrative, not
manufacturer specifications. All impedance inputs are in ohms.
"""
from dataclasses import dataclass
import cmath
import math

COAX_DB_PER_100FT_100MHZ = {
    "RG-58": 4.9,
    "RG-8X": 3.9,
    "RG-213": 2.2,
    "LMR-400": 1.5,
}

def _positive(value, label):
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be positive and finite")

def gamma_from_impedance(z: complex, z0: float = 50.0) -> complex:
    """Voltage reflection coefficient for a passive load."""
    _positive(z0, "z0")
    z = complex(z)
    if not math.isfinite(z.real) or not math.isfinite(z.imag) or z.real < 0:
        raise ValueError("load must have finite, nonnegative resistance")
    return (z - z0) / (z + z0)

def smith_coordinates(z: complex, z0: float = 50.0) -> tuple[float, float]:
    """Cartesian coordinates on an impedance Smith chart."""
    gamma = gamma_from_impedance(z, z0)
    return gamma.real, gamma.imag

def coax_loss_db(coax: str, frequency_mhz: float, length_ft: float) -> float:
    """Approximate matched-line insertion loss using sqrt(f) scaling."""
    if coax not in COAX_DB_PER_100FT_100MHZ:
        raise ValueError("unsupported coax type")
    _positive(frequency_mhz, "frequency_mhz")
    if not math.isfinite(length_ft) or length_ft < 0:
        raise ValueError("length_ft must be finite and nonnegative")
    return COAX_DB_PER_100FT_100MHZ[coax] * math.sqrt(frequency_mhz / 100.0) * length_ft / 100.0

def delivered_power_w(power_w: float, loss_db: float) -> float:
    _positive(power_w, "power_w")
    if not math.isfinite(loss_db) or loss_db < 0:
        raise ValueError("loss_db must be finite and nonnegative")
    return power_w * 10 ** (-loss_db / 10)

@dataclass(frozen=True)
class LMatch:
    topology: str
    series_reactance_ohm: float
    shunt_susceptance_siemens: float
    series_component: str
    series_value: float
    shunt_component: str
    shunt_value: float

def _reactive_part(reactance: float, frequency_hz: float, *, series: bool):
    omega = 2 * math.pi * frequency_hz
    if series:
        if reactance > 0:
            return "Inductor (H)", reactance / omega
        return "Capacitor (F)", -1 / (omega * reactance)
    if reactance > 0:  # positive susceptance = capacitive
        return "Capacitor (F)", reactance / omega
    return "Inductor (H)", -1 / (omega * reactance)

def l_match_solutions(source_ohm: float, load_ohm: float, frequency_mhz: float) -> list[LMatch]:
    """Two ideal lossless L-match solutions for unequal positive real terminations.

    Series/shunt locations are relative to the source-to-load direction.
    Returns [] for already matched resistances. Does not support complex loads.
    """
    _positive(source_ohm, "source_ohm")
    _positive(load_ohm, "load_ohm")
    _positive(frequency_mhz, "frequency_mhz")
    if math.isclose(source_ohm, load_ohm, rel_tol=1e-12):
        return []
    f_hz = frequency_mhz * 1e6
    solutions = []
    if load_ohm > source_ohm:
        # Source -> series reactance -> shunt susceptance across load.
        q = math.sqrt(load_ohm / source_ohm - 1)
        for sign in (1, -1):
            x = sign * source_ohm * q
            b = sign * q / load_ohm
            sc, sv = _reactive_part(x, f_hz, series=True)
            pc, pv = _reactive_part(b, f_hz, series=False)
            solutions.append(LMatch("Series then shunt (load side)", x, b, sc, sv, pc, pv))
    else:
        # Source -> shunt susceptance -> series reactance -> load.
        q = math.sqrt(source_ohm / load_ohm - 1)
        for sign in (1, -1):
            x = sign * load_ohm * q
            b = sign * q / source_ohm
            sc, sv = _reactive_part(x, f_hz, series=True)
            pc, pv = _reactive_part(b, f_hz, series=False)
            solutions.append(LMatch("Shunt (source side) then series", x, b, sc, sv, pc, pv))
    return solutions

def matched_input_impedance(solution: LMatch, load_ohm: float) -> complex:
    """Reconstruct source-facing impedance to validate ideal network topology."""
    zseries = complex(0, solution.series_reactance_ohm)
    b = solution.shunt_susceptance_siemens
    if solution.topology.startswith("Series then"):
        return zseries + 1 / (1 / load_ohm + 1j * b)
    return 1 / (1j * b + 1 / (load_ohm + zseries))
