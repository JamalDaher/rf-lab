"""Guard the dashboard navigation against broken destinations and syntax errors."""
import ast
from pathlib import Path

APP=Path(__file__).resolve().parents[1]/"app.py"

def test_app_compiles():
    compile(APP.read_text(encoding="utf-8"),str(APP),"exec")

def test_dashboard_has_default_home_and_all_featured_tools():
    source=APP.read_text(encoding="utf-8")
    tree=ast.parse(source)
    assert '["Home","Projects","Design & optimize","Measure & match","RF calculators","Simulate & validate"]' in source
    assert 'if section == "Home":' in source
    assert 'on_click=open_workspace,args=(group,name)' in source
    featured={"Project Library","Design Workbench","Yagi Optimizer","NanoVNA S1P",
              "Smith Chart","Radiation Patterns","Validation"}
    for name in featured:
        assert f'if section == "{name}":' in source
        assert f'"{name}"' in source
    assert 'st.session_state.get("design_library",[])' in source
    assert "rf-lab-jdaher.streamlit.app" not in source
