# RF Lab v1.6.0 — Scientific Benchmark Suite

The local CLI executes a **trusted, separately installed** NEC-2c solver
for each Yagi mesh, runs the experimental EFIE solver for the same
nominal geometry, and exports inspectable inputs, outputs and comparisons.

## Run locally

```bash
python -m pip install -e '.[dev]'
python -m rf_lab.benchmark_cli --adapter nec2c --executable nec2c \
  --solver-version "your installed nec2c build" \
  --meshes 7 9 11 13 --frequency-mhz 146 \
  --output-dir ./benchmarks
```

The output directory contains `summary.json` and `summary.csv`, plus
`mesh-07/`, `mesh-09/`, etc. Each case contains `model.nec`,
`solver-output.txt`, and `comparison.json`. Individual comparison
manifests contain deck and solver-output SHA-256 digests, solver version,
frequency, geometry, and mesh. Review the raw NEC output rather than
relying on parsed metrics alone.

Upload `summary.json` in the hosted Streamlit **NEC Comparison** tab
to inspect impedance versus mesh resolution and download the report.
No executable runs in Streamlit Cloud.

## What this verifies

- Numerical **mesh sensitivity** within NEC-2c and experimental EFIE.
- Differences between the two feed-impedance estimates.
- Reproducible model decks and solver-output provenance.
- GitHub Actions executes a real two-mesh NEC-2c integration test.
- Pattern RMS differences are included per mesh when parsable.

## What this does not verify

**The experimental EFIE solver remains unvalidated for physical accuracy.**
NEC and EFIE feed/excitation conventions may differ, and a stable
sequence of mesh values does not prove the correct physical answer.
The suite includes no independently certified NEC reference values or
calibrated antenna measurements. It makes no acceptance claim for
radiation gain, efficiency, directivity, SWR or input impedance.

Solver version is supplied by the operator; the suite does not independently
authenticate a solver binary or verify the user-supplied version string.
