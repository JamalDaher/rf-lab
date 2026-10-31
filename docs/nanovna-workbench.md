# NanoVNA workbench (RF Lab v0.5.0)

## Reference-plane shifting

A positive distance means the VNA measurement plane is moved **toward the DUT**,
undoing the phase of a uniform cable segment. A negative distance moves it
away from the DUT. For frequency `f`, distance `l` and velocity factor `VF`:

`Gamma_DUT = Gamma_measured * exp(+j * 4*pi*f*l/(c*VF))`.

Optional matched-line loss de-embedding applies a round-trip magnitude
correction `10^(loss_dB_per_100m * l / 1000)`. Loss correction is only
available for positive shifts. It can amplify noise and yield `|Gamma| >= 1`
when measurements or model assumptions are inconsistent. Such data are not
automatically clipped or misrepresented as passive impedances.

**This is not a SOL/OSL calibration routine.** Calibrate the VNA first.
Cable length, velocity factor, connector discontinuities, loss dispersion and
fixture behavior limit accuracy.

## Resonance detection

Convert passive S11 samples to `Z = Z0*(1+Gamma)/(1-Gamma)`, then find
reactance zero crossings, linearly interpolating between adjacent valid
samples. Exact zero samples are included. Invalid `|Gamma| >= 1` samples
are skipped. Multiple crossings are returned, as antennas can exhibit
multiple resonances. This is a sampled-sweep estimate, not a fitted model.

Minimum SWR and zero reactance are **different** conditions; a minimum SWR
frequency is not automatically the resonant frequency.

## Multiple S1P sweeps

Upload up to five independent Touchstone v1 `.s1p` files. SWR and return
loss traces are overlaid on their native frequency grids, without inventing
interpolated measurements. Reference impedances are shown per sweep. Sweeps
with differing reference impedances must be normalized to a common
reference before directly comparing SWR or impedance.

## PDF reports

The generated PDF contains a per-sweep table, minimum SWR, best-match
frequency, reactance-zero crossings and a vector SWR plot. It includes
user-supplied notes. PDF creation is in-memory with ReportLab; the application
does not persist uploaded measurements.

## Limitations

Touchstone parser supports v1 one-port S-parameters in RI, MA, DB formats.
Calibration quality, measurement noise, instrument sweep resolution and
fixtures affect results. Report charts cap displayed SWR at 20 to preserve
legibility. Do not use these estimates as a substitute for instrument
calibration or RF safety evaluation.
