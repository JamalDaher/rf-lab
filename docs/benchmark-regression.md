# RF Lab v1.8.0 — Automated numerical regression gates

The new **Numerical Benchmark Regression** GitHub Actions workflow runs
on pull requests and can be launched manually. It checks out the
candidate PR and `main` independently, installs NEC-2c, generates
a **real** two-mesh baseline from the main branch and compares it
against the candidate's NEC-2c and experimental EFIE calculations.

## Outputs

The CI run saves a downloadable artifact named
`nec2c-regression-artifacts` for 30 days containing:
- `baseline-results/`: baseline JSON, CSV, PDF, raw NEC solver outputs and decks
- `candidate-results/`: candidate JSON, CSV, PDF, raw solver outputs, decks, and `regression.json`

Artifacts are uploaded even if the comparison step fails.

## Gates

Default maintenance thresholds per mesh:
- NEC impedance change magnitude: at most **0.5 ohm**
- EFIE impedance change magnitude: at most **0.5 ohm**
- Change in absolute model-to-NEC impedance error: at most **0.5 ohm**

These are *initial engineering maintenance thresholds*, not
experimentally established tolerances. They may need tuning with
documented evidence. A failure is actionable numerical drift,
not necessarily a physics defect.

To compare two saved summaries locally:

```bash
python -m rf_lab.regression_cli \
  --baseline previous/summary.json \
  --candidate current/summary.json \
  --output regression.json
```

The command exits with status 1 when a threshold is exceeded and
rejects mismatched frequency, antenna geometry, wire radius, or mesh
sizes. It never silently replaces a reviewed baseline.

## Baseline limitations

The workflow uses the **current main branch**, not a fixed certified
reference or immutable golden dataset. If main changes, the baseline
changes. This compares a PR against the existing main implementation;
it is not a long-term archival performance trend. Runs on main
itself are not used for cross-release regression by this workflow.

Solver versions are declared by CI; the installed solver is not
cryptographically pinned. Physical antenna accuracy remains
**UNVALIDATED**. Passing thresholds proves only bounded numerical
changes under the chosen comparison.
