# RF Lab v1.0.0 — Numerical validation status

## Scope

This release adds reproducible **mesh sensitivity diagnostics**, an independent
analytical **angular-integration check** for a short electric dipole, and
automated regression tests. The benchmark for a short dipole is directivity
D = 1.5 (1.7609 dBi), derived from a sin²(theta) far-field power pattern.

**This benchmark tests the radiation integral only. It does NOT validate the
pulse-basis EFIE antenna solver.** The EFIE discretization and feed model
remain experimental and can produce inaccurate feed impedance, SWR and gain.

## Mesh study

Run the same Yagi geometry at increasing odd segment counts. The table
reports input impedance, SWR, directivity, front-to-back ratio and matrix
condition number. Successive impedance differences use
|Z_new - Z_old| / max(|Z_new|, |Z_old|, 1e-12). Directivity changes are
absolute differences in dB. The *stable* flag means all successive changes
are within configurable thresholds, not that the model is accurate.

Results are sensitive to discretization and may fail the thresholds.
The tool deliberately does not extrapolate a converged physical impedance
or mark the solver as validated.

## Outstanding acceptance gates before engineering-grade status

1. Implement independent NEC-2/NEC-4 benchmark fixture(s) with documented
   geometry, wire radius, segmentation and excitation.
2. Compare a center-fed half-wave dipole's complex feed impedance and
   pattern against independent trusted reference data.
3. Replace or verify the regularized self-interaction and second-derivative
   discretization with a charge-consistent thin-wire formulation.
4. Demonstrate mesh convergence and quantify residual numerical error.
5. Validate Yagi gain, front-to-back ratio and impedance across several
   geometries, ideally against measured data.
6. Add uncertainty estimates and explicit pass/fail tolerances tied to
   those references.

Until these gates pass, **do not use RF Lab's EFIE estimates to cut antennas,
design matching networks, predict coverage or evaluate RF exposure**.
