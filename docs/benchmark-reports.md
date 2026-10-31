# RF Lab v1.7.0 — Benchmark reports and validation dashboard

## Generate reports

Run a local NEC-2c benchmark:

```bash
python -m rf_lab.benchmark_cli --executable nec2c \
  --solver-version "installed NEC-2c version" --output-dir ./benchmarks
```

This produces `benchmark-report.pdf`, `summary.json`,
`summary.csv` and per-mesh `model.nec`, `solver-output.txt`
and `comparison.json` files.

In the **NEC Comparison** tab, upload a candidate `summary.json`.
Optionally upload an older baseline from the **same geometry,
frequency, radius and mesh sizes**. The dashboard shows historical
differences in absolute impedance error and creates a downloadable PDF.

## Reproducibility checks

`validate_summary` checks the schema, mesh order, geometry,
finite numeric metrics, impedance error arithmetic and presence of
SHA-256-shaped digests. `verify_artifacts` can check hashes against
the **actual raw deck/output bytes**. An uploaded summary alone cannot
prove its claimed digests correspond to the solver output.

`compare_summaries` rejects mismatched geometry, frequency, wire
radius and mesh sizes. It measures differences; it does not establish
which result is physically correct. Solver versions can differ, and
that is explicitly shown.

## Scientific limitations

These reports do not constitute a validated electromagnetic model,
calibrated antenna measurement, NEC certification or verified
independent reference. NEC and experimental EFIE excitation models
are not proven equivalent. Mesh convergence does not guarantee
accuracy. PDF files contain only submitted metrics and provenance
claims; they are not cryptographically signed.

For full provenance, retain the raw solver outputs and NEC input
decks alongside each report.
