# NEC comparison workbench (v1.1.0)

RF Lab now supports **user-supplied, provenance-identified NEC-2/NEC-4
reference results**. It does not run NEC and **does not ship a fabricated
or unverified NEC benchmark**.

## How to generate a real reference

Use an independently installed and properly licensed NEC solver. Model a
three-element Yagi with all wires parallel to the z-axis and placed at the
listed x-axis boom positions. Record the exact geometry, radius, frequency,
segment count, feed position, excitation type, and NEC version. Ensure
the NEC source uses the same center-fed driven element, free-space
environment, polarization, reference plane, and pattern conventions.
Note that NEC's wire junction, end effects and feed gap may differ from
RF Lab's experimental delta-gap model.

Export the NEC output to JSON following this schema:

```json
{
  "solver": "NEC-2",
  "solver_version": "REPLACE_WITH_ACTUAL_VERSION",
  "source": "REPLACE_WITH_TRACEABLE_OUTPUT_FILE_OR_CITATION",
  "frequency_mhz": 146.0,
  "lengths_m": [1.037, 0.975, 0.924],
  "positions_m": [0.0, 0.411, 0.719],
  "wire_radius_mm": 2.0,
  "segments_per_element": 9,
  "feed_impedance_real_ohm": 0.0,
  "feed_impedance_imag_ohm": 0.0,
  "directivity_dbi": 0.0
}
```

**The zero values above are placeholders, NOT NEC results.** Replace
them with actual output before comparing. Optional `front_to_back_db`
and paired `azimuth_deg` / `azimuth_db` arrays may be included.
Azimuth is 0–360 degrees; use normalized dB relative to the same
radiation peak and consistent axes as RF Lab. A difference in gain
normalization or azimuth conventions invalidates the pattern comparison.

## What the dashboard computes

- Complex impedance error (Ω), relative magnitude error, signed R/X errors
- Signed directivity difference in dB
- Optional front-to-back difference in dB
- Optional azimuth-pattern RMS error in dB, using linear interpolation

There are **no automatic accuracy passes**: reference quality and
equivalent electromagnetic geometry must be established separately.
The unit tests use explicitly **synthetic** reference data to check
software correctness, never to assert physical accuracy.

## Next validation milestone

Produce and independently verify at least one real NEC fixture; check
geometry and pattern normalization; quantify errors over multiple mesh
densities and frequencies; investigate the EFIE self-term and feed
model; and only then define defensible physical acceptance thresholds.
