# RF Lab v0.4.0 — transmission lines and NanoVNA measurements

## Transmission-line model

A uniform line with characteristic impedance `Z0`, velocity factor `VF`,
length `l`, frequency `f`, and matched-line attenuation is modeled by:

`Γ_in = Γ_load × exp(-2αl) × exp(-j 2βl)`

where `β = 2πf/(c VF)`. The UI accepts matched-line **power** attenuation in
dB per 100 meters; its round-trip reflection magnitude multiplier is
`10^(-loss_dB_per_100m × l / 100 / 10)`.

The source-facing impedance is `Z_in = Z0 (1 + Γ_in)/(1 - Γ_in)`.
At zero loss a quarter-wavelength section transforms a real resistance
`R` to `Z0²/R`. The simulator assumes frequency-independent velocity factor
and matched-line attenuation. It does not model connector discontinuities,
dispersion, or frequency-dependent line parameters. The simulator rejects
configurations with infinite input impedance rather than plotting a finite
fabricated value.

## Smith chart

The impedance chart shows normalized resistance circles and positive/negative
reactance arcs. A load point and a line-transformation trajectory can be
overlaid. The chart represents reflection coefficient `Γ`, not a predicted
antenna radiation pattern.

## NanoVNA Touchstone import

Upload a UTF-8 `.s1p` file containing Touchstone v1 single-port S11 data.
Supported frequency units: Hz, kHz, MHz, GHz; representations: RI (real/
imaginary), MA (linear magnitude/angle degrees), DB (dB magnitude/angle degrees).
Option lines such as `# MHz S RI R 50` are supported. Default options
are GHz, S, MA and 50 ohms when omitted. Comments beginning with `!` are
ignored. The parser requires exactly three numeric columns, strictly increasing
positive frequencies, and at most 20,000 data points. Touchstone v2 sections,
multiport files, and other parameter types are not supported.

The application displays SWR and return loss versus frequency and plots the
S11 trace on the Smith chart. `|S11| >= 1` yields infinite SWR and is not a
finite passive impedance; such points remain visible in the S11 trace but are
excluded from the best-match frequency calculation.

## Measurement comparison

The minimum finite SWR frequency is labeled **best match**, not necessarily
the physical antenna resonance (which may instead be defined by a zero crossing
of input reactance). The difference from a chosen design frequency is reported
in MHz. No automatic claim is made about gain, efficiency or antenna tuning.

## Safety and accuracy

Calibration plane, cable de-embedding, fixture, adapter quality, sweep range
and instrument calibration influence NanoVNA measurements. Verify readings
with a properly calibrated VNA and observe RF safety precautions.
