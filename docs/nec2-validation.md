# NEC-2c parser verification and radiation cuts (v1.5.0)

This release extends the **real NEC-2c GitHub Actions job** to require
both the feed-impedance parser and a radiation-pattern parser to process
output produced by an installed solver. The actual CI result is the
verification evidence; synthetic tests alone are insufficient.

## Outputs

When the local benchmark succeeds, `comparison.json` now includes
normalized radiation-pattern RMS and maximum absolute differences
and the aligned angular samples, **only if** a single theta=90-degree
cut is unambiguously parsed. The Streamlit NEC Comparison tab plots
NEC versus experimental EFIE normalized patterns from uploaded JSON.

## Geometry and scientific caveats

- NEC theta=90-degree, varying-phi is an azimuth cut for vertical wires.
- NEC tabular TOTAL gain is **not automatically directivity**. We
  normalize each cut to its own peak for shape comparisons.
- The experimental EFIE and NEC solver excitation, reference
  orientations, phase and mesh conventions are not proven equivalent.
- The parser currently targets the standard NEC-2c printed table;
  unsupported layouts fail rather than inventing numbers.
- A successful parser smoke test confirms **compatibility**, not
  physical accuracy. No external independent truth standard, calibrated
  measured data, or certified NEC benchmark is supplied.
- A nonzero or ambiguous parser result is a CI failure, not a pass.
- The hosted Streamlit app does not run the external solver.

## Local execution

```bash
python -m rf_lab.nec2_cli --adapter nec2c --executable nec2c \
  --solver-version "verified locally" --output-dir ./nec-results
```

Review the raw `solver-output.txt` alongside the generated JSON
before interpreting any pattern difference.
