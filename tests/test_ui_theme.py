"""Static UI smoke tests to catch accidental loss of theme and navigation."""
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_app_syntax_and_navigation():
    source=(ROOT/"app.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert 'if section == "Home":' in source
    assert 'if section == "Design Workbench":' in source
    assert 'pio.templates.default = "plotly+rf_lab"' in source
    assert "RF_CHART_COLORS" in source
    assert "@media(max-width:768px)" in source
    assert "rf-lab-jdaher.streamlit.app" not in source

def test_streamlit_theme():
    cfg=(ROOT/".streamlit"/"config.toml").read_text(encoding="utf-8")
    assert 'base = "dark"' in cfg
    assert 'primaryColor = "#39C6C0"' in cfg
    assert 'toolbarMode = "minimal"' in cfg
