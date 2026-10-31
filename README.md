# 📡 RF Lab

An open-source amateur radio engineering toolkit built with Python and Streamlit.

## Features (v0.2.0)

- Half-wave dipole and quarter-wave vertical starting dimensions
- **Three-element Yagi designer:** 2 m and 70 cm presets, custom frequency, adjustable driven-element gap, interactive scaled boom layout and downloadable CSV cutting list
- Complex impedance, reflection coefficient, SWR and return loss
- Watts, dBm and dBW conversions
- Ideal free-space path loss with interactive charts

**Important:** Antenna dimensions are simplified starting approximations, not electromagnetic simulation or validated tape-measure construction dimensions. Tune with an antenna analyzer. Free-space loss does not predict real-world coverage.

Read [Yagi design assumptions and build cautions](docs/yagi-designer.md).

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
tests/test_core.py
tests/test_yagi.py
docs/yagi-designer.md
.github/workflows/tests.yml
pyproject.toml
```

## Roadmap

- Calibrated tape-measure Yagi construction presets and matching networks
- Transmission-line and coax loss models
- Numerical antenna solver and radiation patterns
- SDR signal analysis

## License

MIT.
