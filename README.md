# 📡 RF Lab

An open-source amateur radio engineering toolkit built with Python and Streamlit.

## Features (v1.9.0)

- **Local NEC-2 benchmark pipeline:** optional local CLI execution, impedance-only comparison, reproducibility hashes, JSON report import (not yet tested with a real NEC binary)
- **NEC-2 deck generator:** download a reproducible Yagi .nec model, with an opt-in local executable adapter (no NEC executable bundled; not yet an end-to-end automated benchmark)
- **NEC reference comparison workbench:** upload independently generated NEC-2/NEC-4 JSON reference data, calculate impedance and pattern errors, and inspect overlays (no bundled verified NEC fixture)
- **Numerical validation diagnostics:** multi-resolution mesh sensitivity table and short-dipole analytical integration sanity check (does not validate EFIE accuracy)
- Half-wave dipole and quarter-wave vertical starting dimensions
- **Experimental thin-wire EFIE solver:** pulse-basis current distribution, numerical impedance and SWR, polar patterns and mesh sensitivity controls (NOT validated against NEC or analytical benchmarks)
- **Yagi radiation-pattern explorer:** adjustable three-element geometry, coupled-element surrogate, 2D/3D plots, illustrative directivity and front-to-back ratio
- **Three-element Yagi designer:** 2 m and 70 cm presets, custom frequency, adjustable driven-element gap, interactive scaled boom layout and downloadable CSV cutting list
- Complete impedance Smith chart with resistance circles and reactance arcs
- Transmission-line simulator with velocity factor, length, loss and input impedance trajectory
- NanoVNA Touchstone S1P upload (RI/MA/DB), SWR and return-loss plots, Smith trace and design-frequency comparison
- VNA workbench: cable reference-plane shifting, interpolated zero-reactance resonance detection, up to five sweep overlays, and downloadable PDF measurement reports
- Radiation patterns: interactive ideal dipole and quarter-wave vertical models, elevation/azimuth polar cuts and rotatable 3D field surfaces\n- Antenna tuning assistant: measured resonance guidance, first-order element length estimates, before/after SWR overlays, and portable JSON tuning history
- Coaxial cable loss and estimated matched-line delivered power (RG-58, RG-8X, RG-213, LMR-400)
- Ideal resistive L-network matching, with two component solutions
- Complex impedance, reflection coefficient, SWR and return loss
- Watts, dBm and dBW conversions
- Ideal free-space path loss with interactive charts

**Important:** Antenna dimensions are simplified starting approximations, not electromagnetic simulation or validated tape-measure construction dimensions. Tune with an antenna analyzer. Free-space loss does not predict real-world coverage.

Read [Yagi assumptions](docs/yagi-designer.md), [advanced RF models](docs/advanced-rf.md), [transmission lines and Touchstone](docs/measurements.md), [NanoVNA workbench](docs/nanovna-workbench.md), [antenna tuning](docs/antenna-tuning.md), [radiation patterns](docs/radiation-patterns.md
docs/yagi-patterns.md), and [Yagi pattern limitations](docs/yagi-patterns.md), and [experimental thin-wire EFIE limitations](docs/thin-wire-mom.md).

## v1.9.0 validation status

This release provides numerical diagnostics, **not a validated antenna solver**. See [validation report and outstanding acceptance gates](docs/validation-v1.md). Physical impedance, SWR and gain predictions remain experimental.

See [NEC comparison schema and limitations](docs/nec-reference-comparison.md). The project does not yet include independently verified NEC reference data; physical accuracy remains unvalidated.

See [NEC-2 local runner limitations](docs/nec2-runner.md). Real NEC reference runs and verified output fixtures are still outstanding.

See [local NEC-2 pipeline and limitations](docs/nec2-pipeline.md). The solver is not bundled and the comparison is not yet physically validated.

NEC-2c support: [real solver CI smoke test and setup](docs/nec2c-integration.md). A passing smoke test is not numerical accuracy validation.

[NEC-2c radiation pattern parser verification and comparisons](docs/nec2-validation.md) (experimental; not a physical accuracy certificate).

[Scientific benchmark suite and reproducible NEC-2c mesh reports](docs/scientific-benchmarks.md) (numerical diagnostics only; no physical validation certificate).

[Automated benchmark PDF reports, historical comparisons and provenance checks](docs/benchmark-reports.md) (not physical accuracy validation).

[Automated NEC-2c regression CI and downloadable run artifacts](docs/benchmark-regression.md) (numerical drift only, not physical accuracy validation).

[Experimental three-element Yagi optimization, geometry exports and limitations](docs/yagi-optimization.md).
