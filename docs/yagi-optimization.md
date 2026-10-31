# RF Lab v1.9.0 — Experimental Yagi optimization

The **Yagi Optimizer** tab uses bounded, reproducible random search
over a free-space three-element Yagi geometry. It uses the experimental
pulse-basis EFIE solver and is **not validated for physical accuracy**.

## Controls

- Frequency and wire radius
- Objective: feed-impedance match to 50 ohms, front-to-back ratio,
  directivity or a weighted balanced score
- Number of candidate evaluations (1–40), random seed
- Relative element-length and adjacent-spacing variation bounds
- EFIE mesh size (odd segments per element)

The reflector boom position remains at zero. All three element
lengths and both adjacent boom gaps vary independently within the
selected bounds. Invalid or ill-conditioned candidate models are
rejected. The original design is always evaluated and retained as a
fallback: a search cannot return a worse *objective score* than the
baseline. A higher score does not establish better real-world performance.

## Outputs

The tab displays original/optimized element lengths and boom positions,
a score-progress chart, a geometry comparison, a candidate dimensions
CSV, and a NEC-2 input deck for independent verification.

The CSV is a **candidate geometry**, not final manufacturing
instructions. Tape-measure Yagi builds require feed-gap, element
mounting, matching network, boom effects and measured tuning
considerations that this thin-wire model does not resolve.

## Objective scores

Match: negative normalized complex impedance deviation from 50 ohms.

Front-to-back: capped estimated F/B in dB divided by 20.

Directivity: capped estimated directivity in dBi divided by 10.

Balanced: match + 0.5 × front-to-back + 0.5 × directivity.

The cap avoids extreme numerical nulls dominating the search.
These scores are *relative numerical heuristics*, not physical
optimization guarantees. They should not be compared across
different frequencies, meshes or solver configurations.

## Scientific validation

The experimental EFIE feed and NEC excitation conventions are
not proven equivalent. Export to NEC-2c, compare meshes and
measure the physical antenna before treating an optimized
design as a practical recommendation. This release does not
execute NEC-2c in the hosted Streamlit app.
