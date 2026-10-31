"""Idealized normalized far-field radiation patterns.

Theta is polar angle measured from antenna axis (+z); phi is azimuth.
No feed impedance, mismatch, environment, or numerical EM solver is modeled.
"""
import math
import numpy as np

ANTENNA_TYPES = ("Half-wave dipole", "Short dipole", "Quarter-wave vertical (ideal ground)")


def field_pattern(theta, antenna_type="Half-wave dipole"):
    """Return normalized field magnitude (0..1) for polar angle(s) in radians."""
    if antenna_type not in ANTENNA_TYPES:
        raise ValueError("unsupported antenna model")
    angles = np.asarray(theta, dtype=float)
    if not np.all(np.isfinite(angles)):
        raise ValueError("angles must be finite")
    if antenna_type == "Short dipole":
        result = np.abs(np.sin(angles))
    else:
        sin_theta = np.sin(angles)
        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.where(np.abs(sin_theta) < 1e-10, 0.0,
                              np.cos((np.pi / 2) * np.cos(angles)) / sin_theta)
        result = np.abs(result)
        if antenna_type == "Quarter-wave vertical (ideal ground)":
            result = np.where(angles <= np.pi / 2 + 1e-10, result, 0.0)
    return np.clip(result, 0.0, 1.0)


def power_pattern(theta, antenna_type="Half-wave dipole"):
    """Normalized relative power, not absolute antenna gain."""
    return field_pattern(theta, antenna_type) ** 2


def pattern_db(theta, antenna_type="Half-wave dipole", floor_db=-40.0):
    """Relative power in dB, clipped at a configurable visualization floor."""
    if not math.isfinite(floor_db) or floor_db >= 0:
        raise ValueError("floor_db must be finite and negative")
    power = power_pattern(theta, antenna_type)
    with np.errstate(divide="ignore"):
        db = 10 * np.log10(power)
    return np.maximum(db, floor_db)


def radiation_mesh(antenna_type="Half-wave dipole", theta_points=91, phi_points=145):
    """3D radius proportional to normalized field amplitude."""
    if antenna_type not in ANTENNA_TYPES:
        raise ValueError("unsupported antenna model")
    if not 3 <= theta_points <= 721 or not 3 <= phi_points <= 721:
        raise ValueError("mesh resolution out of range")
    maximum_theta = np.pi / 2 if antenna_type == "Quarter-wave vertical (ideal ground)" else np.pi
    theta, phi = np.meshgrid(np.linspace(0, maximum_theta, theta_points),
                             np.linspace(0, 2*np.pi, phi_points), indexing="ij")
    radius = field_pattern(theta, antenna_type)
    return (radius*np.sin(theta)*np.cos(phi),
            radius*np.sin(theta)*np.sin(phi),
            radius*np.cos(theta), radius)


def elevation_cut(antenna_type="Half-wave dipole", points=361):
    """Elevation cut through antenna axis, polar theta 0..180 degrees."""
    if points < 3 or points > 10001:
        raise ValueError("invalid points")
    theta = np.linspace(0, np.pi, points)
    return np.degrees(theta), power_pattern(theta, antenna_type)


def azimuth_cut(antenna_type="Half-wave dipole", elevation_deg=0.0, points=361):
    """Horizontal azimuth cut at chosen elevation above horizon.

    Axially symmetric ideal models are constant in azimuth. The vertical
    monopole has zero radiation below the ideal ground plane.
    """
    if not math.isfinite(elevation_deg) or not -90 <= elevation_deg <= 90:
        raise ValueError("elevation must be between -90 and 90 degrees")
    if points < 3 or points > 10001:
        raise ValueError("invalid points")
    theta = np.deg2rad(90-elevation_deg)
    return np.linspace(0, 360, points), np.full(points, float(power_pattern(theta, antenna_type)))
