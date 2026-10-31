"""RF calculations (SI units)."""
import math
C = 299_792_458.0

def positive(x, name):
    if not math.isfinite(x) or x <= 0:
        raise ValueError(f"{name} must be positive and finite")

def dipole_length_m(frequency_mhz, factor=0.95):
    positive(frequency_mhz, "frequency")
    if not 0 < factor <= 1: raise ValueError("factor must be between 0 and 1")
    return C * factor / (2 * frequency_mhz * 1e6)

def quarter_wave_m(frequency_mhz, factor=0.95):
    return dipole_length_m(frequency_mhz, factor) / 2

def reflection_coefficient(z, z0=50):
    positive(z0, "reference impedance")
    z = complex(z)
    if z.real < 0 or not all(math.isfinite(v) for v in (z.real, z.imag)):
        raise ValueError("invalid load impedance")
    return (z - z0) / (z + z0)

def swr(z, z0=50):
    g = abs(reflection_coefficient(z, z0))
    return math.inf if g >= 1 else (1 + g) / (1 - g)

def return_loss_db(z, z0=50):
    g = abs(reflection_coefficient(z, z0))
    return math.inf if g == 0 else -20 * math.log10(g)

def watts_to_dbm(w):
    positive(w, "watts")
    return 10 * math.log10(w * 1000)

def dbm_to_watts(dbm):
    if not math.isfinite(dbm): raise ValueError("invalid dBm")
    return 10 ** ((dbm - 30) / 10)

def free_space_path_loss_db(frequency_mhz, distance_km):
    positive(frequency_mhz, "frequency")
    positive(distance_km, "distance")
    wavelength = C / (frequency_mhz * 1e6)
    return 20 * math.log10(4 * math.pi * distance_km * 1000 / wavelength)
