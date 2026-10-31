# 📡 RF Lab

An open-source amateur radio engineering toolkit built with Python and Streamlit.

## Features (v0.5.0)

- Half-wave dipole and quarter-wave vertical starting dimensions
- **Three-element Yagi designer:** 2 m and 70 cm presets, custom frequency, adjustable driven-element gap, interactive scaled boom layout and downloadable CSV cutting list
- Complete impedance Smith chart with resistance circles and reactance arcs
- Transmission-line simulator with velocity factor, length, loss and input impedance trajectory
- NanoVNA Touchstone S1P upload (RI/MA/DB), SWR and return-loss plots, Smith trace and design-frequency comparison
- VNA workbench: cable reference-plane shifting, interpolated zero-reactance resonance detection, up to five sweep overlays, and downloadable PDF measurement reports
- Coaxial cable loss and estimated matched-line delivered power (RG-58, RG-8X, RG-213, LMR-400)
- Ideal resistive L-network matching, with two component solutions
- Complex impedance, reflection coefficient, SWR and return loss
- Watts, dBm and dBW conversions
- Ideal free-space path loss with interactive charts

**Important:** Antenna dimensions are simplified starting approximations, not electromagnetic simulation or validated tape-measure construction dimensions. Tune with an antenna analyzer. Free-space loss does not predict real-world coverage.

Read [Yagi assumptions](docs/yagi-designer.md), [advanced RF models](docs/advanced-rf.md), [transmission lines and Touchstone](docs/measurements.md), and [NanoVNA workbench](docs/nanovna-workbench.md).

## Quick start

Requires Python 3.10–3.13.

```bash
git clone https://github.com/JamalDaher/rf-lab.git
cd rf-lab
python -m venv .venv
# Activate the environment: Windows .venv\Scripts\activate; macOS/Linux source .venv/bin/activate
python -m pip install -e '.[dev]'
streamlit run app.py
```

## Run tests

```bash
python -m pytest -q
```

GitHub Actions tests Python 3.10–3.13 on pushes and pull requests.

## Project structure

```text
app.py
src/rf_lab/core.py
src/rf_lab/yagi.py
src/rf_lab/advanced.py
src/rf_lab/measurements.py
src/rf_lab/workbench.py
src/rf_lab/reporting.py
tests/test_core.py
tests/test_yagi.py
tests/test_advanced.py
tests/test_measurements.py
tests/test_workbench.py
docs/yagi-designer.md
docs/advanced-rf.md
docs/measurements.md
docs/nanovna-workbench.md
.github/workflows/tests.yml
pyproject.toml
```

## Roadmap

- Calibrated tape-measure Yagi construction presets and matching networks
- Datasheet-calibrated coax loss and line models
- Numerical antenna solver and radiation patterns
- SDR signal analysis

## License

MIT.
