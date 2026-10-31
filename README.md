# 📡 RF Lab

A professional, open-source amateur radio engineering toolkit built with Python and Streamlit.

## Features (v0.1.0)

- Half-wave dipole and quarter-wave vertical starting dimensions
- Complex impedance, reflection coefficient, SWR and return loss
- Watts, dBm and dBW conversions
- Ideal free-space path loss with interactive charts

**Important:** Antenna dimensions use simplified length corrections, not electromagnetic simulation. Real antennas require measurement and tuning. Free-space loss does not predict real-world coverage.

## Quick start

Requires Python 3.10–3.13.

```bash
git clone https://github.com/JamalDaher/rf-lab.git
cd rf-lab
python -m venv .venv
# Activate the virtual environment (Windows: .venv\Scripts\activate; macOS/Linux: source .venv/bin/activate)
python -m pip install -e '.[dev]'
streamlit run app.py
```

## Run tests

```bash
python -m pytest -q
```

GitHub Actions runs the test suite on Python 3.10, 3.11, 3.12 and 3.13 for pushes and pull requests.

## Project structure

```text
app.py
src/rf_lab/core.py
tests/test_core.py
.github/workflows/tests.yml
pyproject.toml
```

## Roadmap

- Tape-measure Yagi antenna builder
- Transmission-line and coax loss models
- Antenna pattern visualization
- Numerical antenna solver integration
- SDR signal analysis

## License

MIT.