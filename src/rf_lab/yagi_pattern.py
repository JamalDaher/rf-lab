"""Exploratory 3-element Yagi pattern via a coupled-element surrogate.

Not a thin-wire MoM or NEC solver. Coupling uses a scalar free-space Green
kernel with a configurable effective coupling strength; length detuning uses
a heuristic self-reactance. Directivity is numerically integrated.
"""
from dataclasses import dataclass
import math
import numpy as np

C = 299792458.0


@dataclass(frozen=True)
class YagiPattern:
    azimuth_deg: np.ndarray
    azimuth_db: np.ndarray
    elevation_deg: np.ndarray
    elevation_db: np.ndarray
    directivity_dbi: float
    front_to_back_db: float
    currents: tuple[complex, ...]


def _geometry(frequency_mhz, lengths_m, positions_m, coupling):
    if not math.isfinite(frequency_mhz) or frequency_mhz <= 0:
        raise ValueError("frequency must be positive and finite")
    lengths = np.asarray(lengths_m, dtype=float)
    positions = np.asarray(positions_m, dtype=float)
    if lengths.shape != (3,) or positions.shape != (3,):
        raise ValueError("exactly three element lengths and positions required")
    if not np.all(np.isfinite(lengths)) or not np.all(lengths > 0):
        raise ValueError("lengths must be finite and positive")
    if not np.all(np.isfinite(positions)) or not (positions[0] < positions[1] < positions[2]):
        raise ValueError("positions must be finite and strictly increasing")
    if not math.isfinite(coupling) or not 0 <= coupling <= 0.8:
        raise ValueError("coupling must be between 0 and 0.8")
    wavelength = C / (frequency_mhz*1e6)
    return lengths/wavelength, positions/wavelength


def coupled_currents(frequency_mhz, lengths_m, positions_m, coupling=0.25):
    """Driven-element source at index 1; scalar Green-kernel coupling surrogate."""
    l, p = _geometry(frequency_mhz, lengths_m, positions_m, coupling)
    # Self-detuning is heuristic: shorter elements are capacitive and longer inductive.
    matrix = np.diag(1 + 1j*8*(l-0.48)).astype(complex)
    for i in range(3):
        for j in range(3):
            if i != j:
                d = abs(p[i]-p[j])
                matrix[i,j] = coupling*np.exp(-2j*np.pi*d)/(1+2*np.pi*d)
    return tuple(np.linalg.solve(matrix, np.array([0,1,0], dtype=complex)))


def _power(theta, phi, p, currents):
    """Normalized shape from dipole element factor times array factor."""
    sin_theta = np.sin(theta)
    with np.errstate(divide="ignore", invalid="ignore"):
        element = np.where(np.abs(sin_theta) < 1e-10, 0,
                           np.cos(np.pi/2*np.cos(theta))/sin_theta)
    phase = 2*np.pi*np.asarray(p)[:,None,None] * (sin_theta*np.cos(phi))[None,:,:]
    array = np.sum(np.asarray(currents)[:,None,None]*np.exp(1j*phase), axis=0)
    return np.abs(element*array)**2


def simulate_yagi(frequency_mhz, lengths_m, positions_m, coupling=0.25,
                  samples=181):
    """Calculate relative cuts, 3D directivity and front/back along boom.

    Azimuth 0 degrees is +boom (toward director); 180 degrees is -boom.
    Polar theta is measured from vertical element axis.
    """
    l,p = _geometry(frequency_mhz, lengths_m, positions_m, coupling)
    if not isinstance(samples, int) or not 61 <= samples <= 721:
        raise ValueError("samples must be integer in [61, 721]")
    currents = coupled_currents(frequency_mhz, lengths_m, positions_m, coupling)
    theta = np.linspace(0,np.pi,samples)
    phi = np.linspace(0,2*np.pi,2*samples-1)
    th, ph = np.meshgrid(theta, phi, indexing="ij")
    power = _power(th,ph,p,currents)
    peak = float(np.max(power))
    if peak <= 0 or not math.isfinite(peak):
        raise ValueError("invalid simulated power")
    integral = np.trapezoid(np.trapezoid(power*np.sin(th),phi,axis=1),theta)
    directivity = 10*math.log10(4*math.pi*peak/integral)
    az = np.linspace(0,360,361)
    azpower = _power(np.full((1,361),np.pi/2),np.deg2rad(az)[None,:],p,currents)[0]
    el = np.linspace(0,180,361)
    elpower = _power(np.deg2rad(el)[:,None],np.zeros((361,1)),p,currents)[:,0]
    with np.errstate(divide="ignore"):
        azdb = 10*np.log10(np.maximum(azpower/peak,1e-12))
        eldb = 10*np.log10(np.maximum(elpower/peak,1e-12))
    fb = 10*math.log10(max(float(azpower[0]),1e-12)/max(float(azpower[180]),1e-12))
    return YagiPattern(az,azdb,el,eldb,float(directivity),float(fb),currents)


def yagi_surface(frequency_mhz, lengths_m, positions_m, coupling=0.25,
                 theta_points=61, phi_points=121):
    """Normalized field-amplitude 3D mesh for the same surrogate model."""
    _,p = _geometry(frequency_mhz,lengths_m,positions_m,coupling)
    currents = coupled_currents(frequency_mhz,lengths_m,positions_m,coupling)
    theta,phi = np.meshgrid(np.linspace(0,np.pi,theta_points),
                            np.linspace(0,2*np.pi,phi_points),indexing="ij")
    field = np.sqrt(_power(theta,phi,p,currents))
    maximum = np.max(field)
    if maximum <= 0:
        raise ValueError("invalid field")
    r = field/maximum
    return r*np.sin(theta)*np.cos(phi),r*np.sin(theta)*np.sin(phi),r*np.cos(theta),r
