"""Parametric three-element Yagi starting geometry, not an EM solver."""
from dataclasses import dataclass
import math

C = 299_792_458.0
INCH_PER_M = 39.37007874015748

@dataclass(frozen=True)
class Element:
    name: str
    position_m: float
    length_m: float

@dataclass(frozen=True)
class YagiDesign:
    frequency_mhz: float
    elements: tuple[Element, ...]
    boom_length_m: float
    feed_gap_m: float

def design_yagi(frequency_mhz: float, feed_gap_mm: float = 12.0) -> YagiDesign:
    """Three-element approximate geometry, reflector at x=0.

    Coefficients are heuristic ratios of free-space wavelength; no predicted
    impedance, gain, bandwidth or resonance. Cut long and tune experimentally.
    """
    if not math.isfinite(frequency_mhz) or frequency_mhz <= 0:
        raise ValueError("frequency_mhz must be positive and finite")
    if not math.isfinite(feed_gap_mm) or feed_gap_mm <= 0:
        raise ValueError("feed_gap_mm must be positive and finite")
    wavelength = C / (frequency_mhz * 1e6)
    reflector = 0.505 * wavelength
    driven = 0.475 * wavelength
    director = 0.450 * wavelength
    gap = feed_gap_mm / 1000
    if gap >= driven:
        raise ValueError("feed gap must be shorter than driven element")
    elements = (
        Element("Reflector", 0.0, reflector),
        Element("Driven", 0.20 * wavelength, driven),
        Element("Director", 0.35 * wavelength, director),
    )
    return YagiDesign(frequency_mhz, elements, elements[-1].position_m, gap)

def cutting_list(design: YagiDesign):
    """Rows with total length; split driven element into two equal arms."""
    rows = []
    for element in design.elements:
        if element.name == "Driven":
            arm = (element.length_m - design.feed_gap_m) / 2
            rows.append({"part": "Driven arm", "quantity": 2, "length_m": arm,
                         "length_in": arm * INCH_PER_M})
        else:
            rows.append({"part": element.name, "quantity": 1,
                         "length_m": element.length_m,
                         "length_in": element.length_m * INCH_PER_M})
    return rows
