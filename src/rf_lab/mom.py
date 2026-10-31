"""Experimental pulse-basis thin-wire EFIE solver.

Uses a finite-radius regularized Green kernel and midpoint collocation.
Mesh-dependent estimates are not validated antenna engineering predictions.
"""
from dataclasses import dataclass
import math
import numpy as np

C = 299_792_458.0
ETA0 = 376.730313668


@dataclass(frozen=True)
class MoMResult:
    frequency_mhz: float
    segment_centers_m: np.ndarray
    element_indices: np.ndarray
    currents_a: np.ndarray
    feed_impedance_ohm: complex
    swr_50: float
    azimuth_deg: np.ndarray
    azimuth_db: np.ndarray
    elevation_deg: np.ndarray
    elevation_db: np.ndarray
    directivity_dbi: float
    front_to_back_db: float
    condition_number: float


def _validate(freq, lengths, positions, radius, segments):
    if not math.isfinite(freq) or freq <= 0:
        raise ValueError("frequency must be positive and finite")
    lengths = np.asarray(lengths, dtype=float)
    positions = np.asarray(positions, dtype=float)
    if lengths.shape != (3,) or positions.shape != (3,):
        raise ValueError("three lengths and three boom positions required")
    if not np.all(np.isfinite(lengths)) or not np.all(lengths > 0):
        raise ValueError("lengths must be positive and finite")
    if not np.all(np.isfinite(positions)) or not np.all(np.diff(positions) > 0):
        raise ValueError("positions must be finite and strictly increasing")
    if not math.isfinite(radius) or radius <= 0 or radius >= min(lengths)/10:
        raise ValueError("wire radius must be positive and much smaller than length")
    if isinstance(segments, bool) or not isinstance(segments, int) or segments < 5 or segments > 31 or segments % 2 != 1:
        raise ValueError("segments per element must be odd, 5..31")
    if min(np.diff(positions)) <= 2*radius:
        raise ValueError("wires must not overlap")
    return lengths, positions


def _geometry(lengths, positions, segments):
    centers = np.concatenate([np.linspace(-l/2+l/(2*segments),l/2-l/(2*segments),segments)
                              for l in lengths])
    boom = np.repeat(positions, segments)
    dz = np.repeat(lengths/segments, segments)
    indices = np.repeat(np.arange(3), segments)
    return centers, boom, dz, indices


def _green(distance, k):
    return np.exp(-1j*k*distance)/(4*np.pi*distance)


def _impedance_matrix(centers, boom, dz, indices, radius, k):
    """Integrated pulse Green kernel, discrete scalar-potential derivative."""
    delta = centers[:,None]-centers[None,:]
    dx = boom[:,None]-boom[None,:]
    effective_radius = np.where(indices[:,None] == indices[None,:], radius, 0.0)
    nodes, weights = np.polynomial.legendre.leggauss(12)
    def integral(offset):
        result = np.zeros_like(delta, dtype=complex)
        for node, weight in zip(nodes,weights):
            r = np.sqrt(dx*dx+(delta+offset-node*dz[None,:]/2)**2+effective_radius**2)
            result += weight*_green(r,k)*dz[None,:]/2
        return result
    h = dz[:,None]
    g0 = integral(0)
    d2 = (integral(h)-2*g0+integral(-h))/(h*h)
    return 1j*ETA0/k*(k*k*g0+d2)


def _far_field(theta, phi, centers, boom, dz, currents, k):
    direction_z = np.cos(theta)
    direction_x = np.sin(theta)*np.cos(phi)
    phase = k*(centers[:,None,None]*direction_z[None,:,:] + boom[:,None,None]*direction_x[None,:,:])
    field = np.sum((currents*dz)[:,None,None]*np.exp(1j*phase),axis=0)
    return np.sin(theta)**2*np.abs(field)**2


def solve_yagi_mom(frequency_mhz, lengths_m, positions_m, wire_radius_mm=2.0,
                   segments_per_element=9, reference_ohm=50.0):
    """Experimental pulse-basis EFIE; feed and radiation estimates are mesh dependent."""
    radius = wire_radius_mm/1000
    lengths, positions = _validate(frequency_mhz,lengths_m,positions_m,radius,segments_per_element)
    if not math.isfinite(reference_ohm) or reference_ohm <= 0:
        raise ValueError("reference impedance must be positive")
    centers,boom,dz,indices = _geometry(lengths,positions,segments_per_element)
    k = 2*np.pi*frequency_mhz*1e6/C
    matrix = _impedance_matrix(centers,boom,dz,indices,radius,k)
    condition = float(np.linalg.cond(matrix))
    if not math.isfinite(condition) or condition > 1e13:
        raise ValueError("EFIE matrix ill-conditioned; adjust mesh or geometry")
    feed = segments_per_element+segments_per_element//2
    voltage = np.zeros(len(centers),complex)
    voltage[feed] = 1.0
    currents = np.linalg.solve(matrix,voltage)
    if abs(currents[feed]) < 1e-15:
        raise ValueError("feed current too small")
    zin = complex(1.0/currents[feed])
    gamma = (zin-reference_ohm)/(zin+reference_ohm)
    swr = float((1+abs(gamma))/(1-abs(gamma))) if abs(gamma)<1 else float('inf')
    theta = np.linspace(0,np.pi,91)
    phi = np.linspace(0,2*np.pi,181)
    th,ph = np.meshgrid(theta,phi,indexing='ij')
    power = _far_field(th,ph,centers,boom,dz,currents,k)
    peak = float(np.max(power))
    if peak <= 0:
        raise ValueError("invalid radiation pattern")
    integrate = getattr(np,'trapezoid',None)
    if integrate is None:
        integrate = np.trapz
    total = integrate(integrate(power*np.sin(th),phi,axis=1),theta)
    directivity = 10*np.log10(4*np.pi*peak/total)
    az = np.linspace(0,360,361)
    azpower = _far_field(np.full((1,361),np.pi/2),np.deg2rad(az)[None,:],centers,boom,dz,currents,k)[0]
    el = np.linspace(0,180,361)
    elpower = _far_field(np.deg2rad(el)[:,None],np.zeros((361,1)),centers,boom,dz,currents,k)[:,0]
    with np.errstate(divide='ignore'):
        azdb = 10*np.log10(np.maximum(azpower/peak,1e-12))
        eldb = 10*np.log10(np.maximum(elpower/peak,1e-12))
    fb = 10*np.log10(max(float(azpower[0]),1e-20)/max(float(azpower[180]),1e-20))
    return MoMResult(float(frequency_mhz),centers,indices,currents,zin,swr,
                     az,azdb,el,eldb,float(directivity),float(fb),condition)


def current_profile(result):
    return result.segment_centers_m,result.element_indices,result.currents_a
