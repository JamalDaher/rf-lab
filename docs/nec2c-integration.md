# NEC-2c integration: v1.4.0

RF Lab now supports the **nec2c** command-line syntax explicitly:
`nec2c -i<input-file> -o<output-file>`, with a dedicated GitHub Actions
job installing the real `nec2c` Ubuntu package and running a generated
Yagi model. The PR's integration job is the evidence for execution; a
green mocked unit test alone does not establish NEC compatibility.

## Local run

Install `nec2c` separately, then:

```bash
python -m rf_lab.nec2_cli --adapter nec2c --executable nec2c \
  --solver-version "$(nec2c -v 2>&1)" --output-dir ./nec-results
```

The pipeline requires a recognized NEC input impedance table to complete.
It fails explicitly if parsing fails. The solver output is preserved as
`solver-output.txt` when a full pipeline run succeeds.

## Verification status

- The GitHub Actions integration job executes a **real** NEC-2c binary.
- This smoke test checks successful execution and the expected NEC output
  section, **not** accuracy of the resulting impedance.
- The impedance parser may still need adjustment to actual NEC-2c output.
  A separate parser validation using real solver output is required before
  treating generated comparison JSON as independently verified.
- No verified NEC radiation patterns, directivity, or F/B reference values
  are included. No accuracy claims are warranted.
- Streamlit Cloud still only imports locally generated reports and does
  not execute NEC-2c on the server.

## Source for invocation syntax

Ubuntu nec2c manual:
https://manpages.ubuntu.com/manpages/bionic/man1/nec2c.1.html
