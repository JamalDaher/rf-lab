# RF Lab v1.2.0: NEC-2 deck generation and local runner

RF Lab can generate a free-space 3-element Yagi NEC-2 input deck in
the **NEC Comparison** tab. Download the `.nec` file and run it using
an independently installed compatible NEC-2 solver.

## Scope and limitations

- No NEC executable is bundled or installed on Streamlit Community Cloud.
- The Python `run_nec2(deck, executable)` adapter is **opt-in local use**,
  requires a trusted installed executable, and does not use a shell.
- NEC command-line interfaces vary. This adapter assumes the binary accepts
  the input filename as its first argument. Other variants need a tailored
  adapter. The return code and raw output must be inspected.
- The `parse_nec2_input_impedance` helper recognizes only a subset of
  conventional NEC-2 output table formats; it deliberately raises on
  unrecognized output. It does not generate a complete reference JSON.
- There is **no end-to-end verified NEC-2 run or benchmark dataset** in
  this release. No real NEC outputs have been asserted or fabricated.
- NEC geometry and excitation may not be equivalent to RF Lab's
  experimental pulse-basis EFIE discretization.

## Procedure

1. In the NEC Comparison tab, choose frequency, wire radius and segments.
2. Download the generated input deck and inspect GW, GE, GN, EX, FR, RP.
3. Execute using a trusted NEC-2 solver compatible with your system.
4. Inspect its impedance and radiation pattern results. Verify geometry,
   feed excitation, angular convention, normalization, and solver version.
5. Populate the provenance-bearing reference JSON described in
   [NEC reference comparison](nec-reference-comparison.md) from **actual**
   results, then upload it to RF Lab for error calculations.

## Scientific status

This release is a reproducible *input-generation and local execution
foundation*, not yet a fully automated benchmark runner. The next step
is to integrate and test a specific NEC-2 distribution and implement a
versioned output parser plus end-to-end tests using verified fixtures.
