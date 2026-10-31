# Interactive radiation patterns (v0.7.0)

The Radiation Patterns tab displays idealized, normalized far-field **power**
cuts in polar coordinates and a rotatable 3D **field-amplitude** surface.

## Models

- **Half-wave dipole** (thin, center-fed, free-space approximation):
  normalized field magnitude |cos((π/2) cos θ) / sin θ|, with axis nulls.
- **Short dipole** (electrically small, free-space approximation):
  normalized field magnitude |sin θ|.
- **Quarter-wave vertical over ideal ground**: ideal image-theory upper
  hemisphere, using the half-wave dipole pattern above the perfect ground
  plane and zero radiation below it.

θ is the polar angle from the vertical antenna axis. The elevation plot
covers θ=0..180°; θ=90° is the horizon/broadside direction. Azimuth is
measured around the antenna axis. These models are rotationally symmetric:
the horizontal pattern is circular at any fixed elevation.

The 3D surface radius is proportional to **field amplitude**; the 2D
polar plots show **relative power** in dB with a configurable display floor.
All plots are normalized to 0 dB at the peak. They are **not absolute gain
(dBi)**, do not model impedance or SWR, and cannot predict coverage or
terrain losses.

Frequency is shown for context and a free-space wavelength calculation,
but normalized ideal patterns do not vary with frequency. Changing element
length or frequency in a real antenna may invalidate the assumed model.
No numerical method-of-moments simulation, mutual coupling, ground losses,
mounting effects, or measured patterns are included.

Run tests with `python -m pytest -q`.
