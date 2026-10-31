# Yagi radiation pattern explorer (v0.8.0)

This tab links the existing three-element Yagi starting geometry to an
**exploratory coupled-element surrogate**. Reflector, driven-element and
director lengths and boom spacings are adjustable. The UI shows a horizontal
azimuth cut, a vertical elevation cut, a rotatable 3D surface, a numerically
integrated **surrogate directivity** and a front-to-back ratio.

## What the model computes

Three scalar complex current amplitudes are solved from a 3×3 linear system.
The driven element is excited, while the parasitic elements are unpowered.
Off-diagonal interactions use a decaying complex free-space phase kernel.
A heuristic self-reactance term depends on element length. The far-field is
the half-wave dipole element factor multiplied by a phased array factor.
Power is integrated over the sphere to estimate *directivity*, not gain.

Azimuth 0° is along the boom toward the director; 180° is toward the reflector.
The 3D plot uses relative field amplitude, while polar plots use relative
power dB, referenced to the global 3D maximum.

**This is NOT a validated thin-wire method-of-moments solver, NEC, or an
engineering prediction of Yagi gain, feed impedance, SWR, front-to-back ratio,
or bandwidth.** The scalar coupling kernel and detuning model are heuristic.
Results are intended for interactive intuition and software experimentation
only. Do not use them for antenna cutting, link budgets or safety decisions.
Actual Yagi modeling requires full-wire mutual impedances and boundary
conditions, or measured patterns. The coupling control is an exploratory
parameter, not a measured material or antenna property.

The design defaults come from `design_yagi`; edits in the pattern explorer
are local to that tab and do not change the cutting list.

Tests: `python -m pytest -q`.
