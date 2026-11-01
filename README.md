# 📡 RF Lab

**[🚀 Launch the Live Demo](https://rf-lab-jdaher.streamlit.app)** · [Source code](https://github.com/JamalDaher/rf-lab)

[![Live Demo](https://img.shields.io/badge/Streamlit-Live%20Demo-FF4B4B?logo=streamlit&logoColor=white)](https://rf-lab-jdaher.streamlit.app)


An open-source amateur radio engineering toolkit built with Python and Streamlit.

## Features (v3.9.0)

- **Local NEC-2 benchmark pipeline:** optional local CLI execution, impedance-only comparison, reproducibility hashes, JSON report import (not yet tested with a real NEC binary)
- **NEC-2 deck generator:** download a reproducible Yagi .nec model, with an opt-in local executable adapter (no NEC executable bundled; not yet an end-to-end automated benchmark)
- **NEC reference comparison workbench:** upload independently generated NEC-2/NEC-4 JSON reference data, calculate impedance and pattern errors, and inspect overlays (no bundled verified NEC fixture)
- **Numerical validation diagnostics:** multi-resolution mesh sensitivity table and short-dipole analytical integration sanity check (does not validate EFIE accuracy)
- Half-wave dipole and quarter-wave vertical starting dimensions
- **Experimental thin-wire EFIE solver:** pulse-basis current distribution, numerical impedance and SWR, polar patterns and mesh sensitivity controls (NOT validated against NEC or analytical benchmarks)
- **Yagi radiation-pattern explorer:** adjustable three-element geometry, coupled-element surrogate, 2D/3D plots, illustrative directivity and front-to-back ratio
- **Three-element Yagi designer:** 2 m and 70 cm presets, custom frequency, adjustable driven-element gap, interactive scaled boom layout and downloadable CSV cutting list
- Complete impedance Smith chart with resistance circles and reactance arcs
- Transmission-line simulator with velocity factor, length, loss and input impedance trajectory
- NanoVNA Touchstone S1P upload (RI/MA/DB), SWR and return-loss plots, Smith trace and design-frequency comparison
- VNA workbench: cable reference-plane shifting, interpolated zero-reactance resonance detection, up to five sweep overlays, and downloadable PDF measurement reports
- Radiation patterns: interactive ideal dipole and quarter-wave vertical models, elevation/azimuth polar cuts and rotatable 3D field surfaces\n- Antenna tuning assistant: measured resonance guidance, first-order element length estimates, before/after SWR overlays, and portable JSON tuning history
- Coaxial cable loss and estimated matched-line delivered power (RG-58, RG-8X, RG-213, LMR-400)
- Ideal resistive L-network matching, with two component solutions
- Complex impedance, reflection coefficient, SWR and return loss
- Watts, dBm and dBW conversions
- Ideal free-space path loss with interactive charts

**Important:** Antenna dimensions are simplified starting approximations, not electromagnetic simulation or validated tape-measure construction dimensions. Tune with an antenna analyzer. Free-space loss does not predict real-world coverage.

Read [Yagi assumptions](docs/yagi-designer.md), [advanced RF models](docs/advanced-rf.md), [transmission lines and Touchstone](docs/measurements.md), [NanoVNA workbench](docs/nanovna-workbench.md), [antenna tuning](docs/antenna-tuning.md), [radiation patterns](docs/radiation-patterns.md
docs/yagi-patterns.md), and [Yagi pattern limitations](docs/yagi-patterns.md), and [experimental thin-wire EFIE limitations](docs/thin-wire-mom.md).

## v3.9.0 validation status

This release provides numerical diagnostics, **not a validated antenna solver**. See [validation report and outstanding acceptance gates](docs/validation-v1.md). Physical impedance, SWR and gain predictions remain experimental.

See [NEC comparison schema and limitations](docs/nec-reference-comparison.md). The project does not yet include independently verified NEC reference data; physical accuracy remains unvalidated.

See [NEC-2 local runner limitations](docs/nec2-runner.md). Real NEC reference runs and verified output fixtures are still outstanding.

See [local NEC-2 pipeline and limitations](docs/nec2-pipeline.md). The solver is not bundled and the comparison is not yet physically validated.

NEC-2c support: [real solver CI smoke test and setup](docs/nec2c-integration.md). A passing smoke test is not numerical accuracy validation.

[NEC-2c radiation pattern parser verification and comparisons](docs/nec2-validation.md) (experimental; not a physical accuracy certificate).

[Scientific benchmark suite and reproducible NEC-2c mesh reports](docs/scientific-benchmarks.md) (numerical diagnostics only; no physical validation certificate).

[Automated benchmark PDF reports, historical comparisons and provenance checks](docs/benchmark-reports.md) (not physical accuracy validation).

[Automated NEC-2c regression CI and downloadable run artifacts](docs/benchmark-regression.md) (numerical drift only, not physical accuracy validation).

[Experimental three-element Yagi optimization, geometry exports and limitations](docs/yagi-optimization.md).

## RF Lab v3.9.0 — Design Workbench

The Streamlit interface now uses a **grouped sidebar** instead of 18 crowded tabs, with a restrained responsive layout. The new **Design Workbench** saves versioned Yagi designs to downloadable JSON, imports them back, compares up to five session designs, plots experimental EFIE impedance/SWR frequency sweeps, and exports a ZIP with NEC-2 deck, dimensions and optional sweep data. Session history is not server-persistent: download JSON to preserve it. These are unvalidated numerical estimates, not verified antenna specifications.

**Live demo:** https://rf-lab-jdaher.streamlit.app

## v3.9.0 Dashboard home

The new **Home** workspace is the default landing page. Six clickable cards lead directly to Design Workbench, Yagi Optimizer, NanoVNA S1P, Smith Chart, Radiation Patterns, and Validation. A session-design summary links to the existing saved-design workbench. The sidebar retains all tools, with Home as the first option. No cloud design storage is introduced: saved designs are session-only unless exported to JSON.

## v3.9.0 Visual polish

- Consistent dark engineering palette (deep navy, teal highlights), configured in `.streamlit/config.toml`.
- Shared Plotly defaults for grid lines, chart backgrounds, typography, and a six-color series palette.
- Improved spacing, metric cards, button shapes, chart framing, and sidebar visual hierarchy.
- Responsive small-screen adjustments for stacked cards and charts, plus reduced-motion support.
- All existing tools and the dashboard remain available; no Live Demo self-link is added.

**Accessibility:** Verify color contrast, keyboard focus, and mobile layouts on the deployed app; automated tests cover configuration and syntax, not visual rendering.

## v3.9.0 Antenna engineering geometry

The **3-Element Yagi** designer now includes a rotatable 3D dimensional view and an annotated, equal-scale top view. Toggle units (centimeters, inches or millimeters), inspect individual elements, see the actual driven-element feed gap and review a dimension schedule alongside the existing CSV cutting list. The geometry module is independently tested for dimensions and unit conversions. These are construction starting dimensions, **not** electromagnetic predictions or verified manufacturing drawings.

## v3.9.0 Antenna Construction Assistant

Open **Design & optimize → Construction Assistant** to create a practical three-element Yagi build packet. Choose frequency, feed gap, shop units and an extra trim allowance per physical cut piece. The assistant provides a top-down engineering layout, auditable cutting schedule, materials checklist, step-by-step assembly and measurement workflow, and a downloadable letter-size PDF with all of these details. The driven element is correctly split into two arms around the feed gap; the extra allowance applies separately to each arm.

**Important:** Dimensions are heuristic starting points, not a validated antenna design or structural engineering specification. Stock diameters, mounting clearances, feed matching, weatherproofing and safe power handling must be established by the builder and confirmed by measurements. Never install near overhead power lines.

## v3.9.0 Tape-Measure Yagi Builder

The **Design & optimize → Tape-Measure Yagi** tool creates a portable, three-element steel tape-measure antenna starting plan. Select operating frequency, driven feed gap, blade width, extra trimming length per physical piece, PVC boom end margin and mounting option (PVC cross fittings or insulated brackets). It shows the top-down geometry, four-piece blade cutting schedule, mounting marks measured from the physical boom end, minimum PVC stock length, materials list and a field assembly/tuning checklist. Download a printable PDF shop packet with the tape-specific boom references and construction steps.

**Engineering limitations:** Steel tape width and mounting change RF behavior; the model does not predict resonance, gain, matching, or mechanical stability. Verify with an antenna analyzer. Flexible steel blades have sharp edges and can spring back; use eye/hand protection, secure the blades, and stay clear of power lines.

## v3.9.0 Measurement & Tuning Workbench

The new **Measure & match → Measurement & Tuning Workbench** combines existing NanoVNA import, resonance analysis, first-order length guidance, before/after comparison, portable tuning history and printable PDF reporting in one five-step workflow. Import calibrated Touchstone v1 `.s1p` sweeps, set a target frequency and adjustable element length, compare SWR plots, then save or export session records. The workbench distinguishes the minimum-SWR frequency from a reactance-zero resonance and rejects mismatched before/after reference impedances. History is browser-session-only until exported to JSON.

**Measurement limitations:** A zero-reactance crossing is a resonance estimate, not a guarantee of 50-ohm matching. The length change assumes an inverse frequency/length relationship and is not a validated multi-element Yagi tuning model. Calibrate at the same reference plane, trim conservatively and remeasure.

## v3.9.0 Antenna Project Library

Open **Projects → Project Library** to create up to 50 named antenna projects. Attach an existing Design Workbench design, track a six-step construction checklist, archive up to ten calibrated NanoVNA `.s1p` measurements per project, view measured SWR traces and resonance summaries, and copy tuning-session history into a project. Generate a project measurement PDF. Export all projects as a versioned JSON file or a ZIP containing that JSON; reimport the JSON and merge projects by stable ID. The JSON preserves numeric S11 samples, geometry, notes and checklist state. Input is schema-validated and bounded in size. **Projects live only in the current Streamlit browser session**; download backups regularly. There is no account synchronization, server database or automatic persistence. Imported projects with matching IDs replace the current session versions.

## v3.9.0 — Professional dashboard and interface

The Home dashboard now displays live **session-only** counts for antenna projects, saved designs, S1P measurements and available engineering tools, alongside six focused quick-launch cards and recent-project shortcuts. The sidebar navigation is driven by a shared workspace catalog to keep destinations consistent, and the navy/teal theme has refined surfaces, chart framing, keyboard focus indicators, compact metrics and responsive spacing. Existing calculators, project records, designs and analysis models are unchanged. Project data still requires manual JSON/ZIP backup.

## v3.9.0 — Interactive RF Signal Analysis Workbench

Open **Signal analysis → Signal Analysis Workbench** to explore deterministic synthetic AM, FM and CW waveforms. Control carrier, modulating tone, modulation depth (or FM index), sample rate, duration and reproducible Gaussian noise at a requested SNR. Inspect time-domain waveforms, windowed one-sided FFT amplitude spectra, RMS and peak amplitude, dominant FFT bin and frequency resolution. Compare an optional 101-tap windowed-sinc low-pass FIR output and export waveform/spectrum CSV data. The FFT amplitude scale is **dB relative to amplitude 1**, not calibrated RF power (dBm), spectral density or actual receiver measurements. AM and FM examples are educational simulations and do not transmit or receive radio signals. Filter transients and FFT leakage may affect displayed estimates.

## v3.9.0 — SDR Signal Laboratory

Open **Signal analysis → SDR Signal Laboratory** for reproducible synthetic BPSK, QPSK and 16-QAM experiments. Inspect constellation plots, symbol/bit error rates in a simplified ideal synchronized AWGN channel, EVM relative to known transmitted symbols, and measured SNR. Explore complex-baseband FFT spectra and short-time waterfall plots. Import **offline** interleaved little-endian float32 IQ (complex64) or signed int8 IQ (cs8), up to 512 KiB and 65,536 samples. The imported file's sample rate must be supplied; frequency axes are offsets from its unspecified center frequency. Download constellation CSV data. No hardware connection, live SDR capture, pulse shaping, synchronization or RF transmission is included. BER is based on binary symbol-index labels, not Gray-coded modem BER; amplitude scales are not calibrated power readings.

## v3.9.0 — SDR Receiver Workbench

Use **Signal analysis → SDR Receiver Workbench** to explore an offline AM/FM receiver chain. Generate synthetic complex-baseband AM/FM carriers or import recorded IQ in interleaved little-endian float32 or signed int8 formats (up to 512 KiB). Configure the sample rate and frequency shift, optionally apply a windowed-sinc FIR low-pass or high-pass filter, and demodulate the AM envelope or FM instantaneous frequency. Inspect I/Q at input, tuned and filtered stages; compare baseband FFTs and demodulated time traces. Export processed complex64 IQ and demodulated CSV samples. Frequency tuning is an offset in the IQ recording, not an absolute RF frequency. There is no live SDR device integration, audio playback, RF transmission, AGC, deemphasis, resampling or carrier recovery. AM output is DC-removed envelope and FM output is instantaneous frequency in Hz; neither is speaker-ready calibrated audio. FIR transients and aliasing must be considered.

## v3.9.0 — SDR recovered audio

The **SDR Receiver Workbench** now includes an **Audio playback** tab for offline demodulated AM/FM IQ. Listen in-browser and export mono 16-bit PCM WAV. Adjustable audio low-pass filtering, optional automatic gain control, and 75-microsecond FM de-emphasis support receiver experiments. Playback rates are 8, 16, 24 or 48 kHz. These are educational post-processing tools, not live SDR hardware or calibrated broadcast audio. Linear resampling is not bandlimited and can alias when downsampling; high-rate imported IQ may require external preprocessing. WAV and other exports remain local to the browser session.

## v3.9.0 — AM vs FM Noise Lab

Open **Signal analysis → AM vs FM Noise Lab** to hear a clean tone and a noisy recovered tone side by side for AM and FM. Adjust complex-baseband AWGN channel SNR, tone frequency, duration and deterministic noise seed. Compare recovered audio SNR against clean demodulated references and inspect time-domain waveforms. Download noisy WAV examples. This is an educational single-tone AWGN experiment, not a claim that FM always has better reception: modulation deviation, bandwidth and threshold effects matter. Each mode uses a separate reproducible noise realization at equal nominal input SNR; playback preserves the clean/noisy relative level within each mode without AGC.

## v3.9.0 — RF Spectrum Analyzer

Navigate to **Signal analysis → RF Spectrum Analyzer** for an offline complex-IQ spectrum analyzer. Generate a deterministic two-tone test signal with noise or upload up to 512 KiB of complex64/cs8 IQ data. Select Hann or rectangular window, FFT size and 0/50/75% overlap. Welch averaging produces a PSD (relative dB/Hz), with local peak markers, a median-bin noise-floor estimate, and a 99% integrated-power occupied-bandwidth estimate. Download a frequency/PSD CSV. These are baseband offset measurements, not calibrated absolute dBm, receiver noise figure or compliance-grade occupied bandwidth.

## v3.9.0 — RF Waterfall & Signal Detection

Navigate to **Signal analysis → RF Waterfall & Signal Detection**. Explore a time-frequency waterfall of a synthetic burst/chirp signal or upload a bounded offline complex64/cs8 IQ recording. Adjust FFT size, overlap, Hann/rectangular window and detection threshold. Sustained spectral peaks are tracked across frames as approximate activity events, marked on the heatmap and exported to CSV. Frequency is a complex-baseband offset and power is relative dB/Hz; this is not live SDR monitoring, calibrated RF power measurement or a robust multi-signal tracker. Detection may split moving signals or merge nearby signals.

## v3.9.0 — RF Signal Classification Laboratory

Navigate to **Signal analysis → RF Signal Classification** to compare experimental CW/carrier, AM-like, FM-like and digital-like complex-IQ signal-shape heuristics. Generate reproducible reference signals or import a bounded offline complex64/cs8 IQ recording. The lab displays relative evidence scores, a best matching shape, an ambiguity warning, 99% spectral bandwidth, envelope variability, instantaneous frequency spread and explanations. These are transparent, heuristic scores — **not probabilities or a trained classifier**, not verified modulation identification, and not suitable for safety-critical or regulatory decisions. Complex modulations and noisy/filtered signals may be misidentified.

## v3.9.0 — Unified RF Signal Analysis Dashboard

Under **Signal analysis → RF Signal Analysis Dashboard**, inspect one offline complex-IQ recording across a synchronized spectrum plot, waterfall, and heuristic classification. Shared baseband-frequency marker, peak/event inspection, compact expandable controls, and downloadable JSON report are provided. Synthetic signals and bounded complex64/cs8 uploads supported. **Limitations:** offline-only; relative dB/Hz (not calibrated dBm), heuristic labels (not verified modulation identification); markers and event timing are estimates.

## v3.9.0 — RF Signal Recording Comparison

Under **Signal analysis → RF Signal Recording Comparison**, compare two bounded offline complex-IQ captures or synthetic references. Overlay power spectra on a shared baseband-frequency axis (Hz), inspect relative PSD differences, 99% occupied-bandwidth changes, detected events and heuristic classification changes, and download a JSON comparison report. Each capture has its own sample rate and encoding. **Limitations:** no live hardware, calibrated dBm or guaranteed modulation identification; capture conditions must be controlled before attributing differences to antennas or filters.

## v3.9.0 — RF Filter Design Laboratory

Under **Signal analysis → RF Filter Design Laboratory**, design windowed-sinc FIR low-pass, high-pass, band-pass and notch filters with adjustable cutoff/band edges and odd tap counts. Inspect magnitude and wrapped phase response, apply filters to synthetic or bounded imported complex IQ, compare relative power spectra and occupied bandwidth, and export filter coefficients/report as JSON or filtered complex64 IQ. The filters are symmetric about DC in complex baseband, not independently tunable positive/negative sidebands. **Limitations:** windowed FIR approximations, edge transients, offline-only, uncalibrated relative power.
