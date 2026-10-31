# Experimental thin-wire EFIE solver (v0.9.0)

The **Thin-Wire MoM** tab is an educational, low-order numerical electromagnetic
model of three parallel, perfectly conducting, z-oriented straight wires.

It uses pulse-current basis functions, midpoint testing, a finite-radius
regularized free-space Green function integrated over each pulse with
12-point Gauss-Legendre quadrature, and a three-point discrete approximation
to the second derivative in the Pocklington electric-field integral equation.
A one-volt delta-gap excitation is applied at the center of the driven wire;
reflector and director are unpowered and coupled through the matrix.

The solver displays complex current samples, experimental feed impedance,
50-ohm SWR, normalized far-field cuts, directivity from numerical sphere
integration, front-to-back ratio, and matrix condition number.

## Critical limitations

**Experimental and not validated.** This is not NEC-2/NEC-4, and it has not
passed benchmark comparisons with known thin-wire input impedances or a
convergence study. The regularized self kernel, discrete derivative, pulse
basis, delta-gap source, and segment-center current representation can create
large errors and strong mesh dependence, especially in input impedance and
SWR. A numerical result is not automatically a reliable physical result.
Do not use this solver to cut antennas, select matching components, predict
real-world gain or certify exposure safety. In particular, reported SWR
can be wildly inaccurate. No ground, dielectric boom, conductor loss,
finite feed gap, balun or coax effects are modeled.

Increase the odd segments-per-element count and compare results as a basic
mesh-sensitivity diagnostic; **agreement between two meshes is not proof of
accuracy**. A future version should add established NEC benchmarks,
charge-conserving basis functions, validated self terms, and convergence tests.

The original v0.8.0 heuristic Yagi explorer remains available separately.

Run tests with `python -m pytest -q`.
