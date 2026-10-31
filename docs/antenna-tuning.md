# Antenna tuning assistant (v0.6.0)

Upload an S1P measurement and enter the target frequency and the length of
the adjustable resonant element. The assistant locates measured zero-reactance
crossings, chooses the one nearest the target and estimates a length change
using the first-order approximation `f × L ≈ constant`:

`L_new ≈ L_current × f_measured / f_target`.

**Important:** A resonance *above* the target generally suggests lengthening
the resonant element; a resonance *below* the target generally suggests
shortening it. This guidance applies only when element length is the primary
tuning parameter, such as an isolated dipole or monopole. Coupled Yagis,
loaded antennas, matching networks, feed gaps, nearby objects and parasitic
elements may invalidate the simple model. The calculated millimeters are a
starting estimate, not an instruction to cut that exact amount.

Minimum SWR and zero-reactance resonance are distinct. When there are multiple
crossings, the assistant selects the crossing nearest the target. If none
exists in the sweep, no length estimate is made. Adjust gradually and
remeasure. Follow electrical and RF safety practices.

## Before/after comparison

Upload separate before and after S1P files. The tool compares the absolute
resonance error relative to the target and minimum SWR from each native sweep.
A positive resonance-error improvement means the after resonance is closer to
the target; negative means it moved away. A negative minimum-SWR change means
the after measurement has a lower minimum SWR. These are independent metrics.

## Session history

A tuning log is kept in Streamlit session state for the current browser
session, with user-entered labels and notes. Export the history as JSON to
keep it, and re-import JSON later. **History is not stored on the server or
automatically synced across devices.** S1P sweep data are not included in the
history JSON, only tuning summaries. Avoid uploading untrusted or excessively
large JSON; imports are limited to 1,000 entries.

## Testing

Run `python -m pytest -q`. Tests cover adjustment direction, approximate
magnitude, on-target/no-resonance cases, before/after metrics, JSON round trips
and invalid inputs.
