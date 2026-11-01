"""Dashboard navigation, accessibility and quick-launch regression checks."""
import ast
from pathlib import Path
from rf_lab.dashboard import WORKSPACES,FEATURED,dashboard_metrics,project_previews

APP=Path(__file__).resolve().parents[1]/"app.py"

def test_app_compiles():
    compile(APP.read_text(encoding="utf-8"),str(APP),"exec")

def test_dashboard_has_default_home_and_all_featured_tools():
    source=APP.read_text(encoding="utf-8")
    ast.parse(source)
    assert '["Home","Projects","Design & optimize","Measure & match","RF calculators","Simulate & validate"]' in source
    assert 'if section == "Home":' in source
    assert 'on_click=open_workspace,args=(group,name)' in source
    assert 'options={name:list(tools) for name,tools in WORKSPACES.items()}' in source
    for _,name,_,category in FEATURED:
        assert name in WORKSPACES[category]
        assert f'if section == "{name}":' in source
    assert 'st.session_state.get("design_library",[])' in source
    assert "rf-lab-jdaher.streamlit.app" not in source

def test_session_metrics_and_recent_project_order():
    projects=[{"id":"a","name":"A","frequency_mhz":146,
               "measurements":[1,2],"tuning_history":[1]},
              {"id":"b","name":"B","frequency_mhz":435,
               "measurements":[],"tuning_history":[]}]
    metrics=dashboard_metrics(projects,[1,2,3],[1])
    assert metrics["projects"]==2
    assert metrics["designs"]==3
    assert metrics["measurements"]==2
    assert metrics["tuning_records"]==2
    assert metrics["available_tools"]==sum(map(len,WORKSPACES.values()))
    assert [p["id"] for p in project_previews(projects)]==["b","a"]
    assert project_previews(projects,0)==[]

def test_workspace_catalog_is_unique_and_complete():
    all_tools=[name for group in WORKSPACES.values() for name in group]
    assert len(all_tools)==len(set(all_tools))
    assert "Project Library" in WORKSPACES["Projects"]
    assert "Measurement & Tuning Workbench" in WORKSPACES["Measure & match"]
