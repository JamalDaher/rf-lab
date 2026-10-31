# Local NEC-2 benchmark pipeline (v1.3.0)

This release adds a reproducible local **impedance-only** benchmark
pipeline. It is not a verified physical validation result.

## Run

Install a compatible NEC-2 command-line executable yourself. The
existing runner expects an executable that accepts the input file path
as its first argument and writes model.out or stdout. NEC-2 programs
have different command-line conventions; the adapter is not tested
against a specific binary distribution.

From an installed RF Lab checkout:

```bash
python -m rf_lab.nec2_cli --executable /absolute/path/to/nec2 \
  --solver-version "YOUR_VERIFIED_NEC_BUILD" --output-dir ./nec-results
```

This creates, **only after a successful run and recognized impedance
table**:

- `model.nec`: generated input deck
- `solver-output.txt`: unmodified solver output
- `comparison.json`: impedance errors and traceable SHA-256 hashes

Upload `comparison.json` in the NEC Comparison tab to inspect
impedance error metrics. Keep the raw output and input deck together
for reproducibility.

## Explicit limits

- NEC execution is local, not available on the hosted Streamlit app.
- The parser currently recognizes only a narrow NEC input impedance
  table format. Unsupported output fails with an error rather than
  guessing values.
- Radiation pattern and gain/directivity parsing is **not implemented**.
  The JSON reports mark `pattern_metrics_available=false`.
- No real NEC binary or actual reference output has been tested as part
  of this PR. Automated tests mock the solver and use synthetic numbers.
- The experimental EFIE feed and NEC feed models may not be equivalent.
  A discrepancy is not necessarily a bug in either model.
- The uploaded report is not authenticated or externally verified;
  use the saved raw output and hashes for provenance checking.

## To complete physical validation

Select and pin a specific NEC-2 distribution, test its actual output
format, independently inspect excitation and pattern conventions,
generate real versioned reference fixtures, parse radiation patterns,
and define quantitative acceptance criteria based on those references.
