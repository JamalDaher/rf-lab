"""Tests for v4 professional navigation metadata."""
import pytest
from rf_lab.pro_workspace import (WORKFLOWS,REPORT_TOOLS,all_tools,search_tools,
                                  tool_exists,normalize_favorites,workflow_steps)
from rf_lab.dashboard import WORKSPACES

def test_search_is_case_insensitive():
    assert ("Signal analysis","RF Filter Design Laboratory") in search_tools("filter")
    assert search_tools("  FILTER  ")==search_tools("filter")
    assert search_tools("no-such-tool")==[]
    assert search_tools("")==all_tools()

def test_workflows_reference_existing_tools():
    for flow in WORKFLOWS:
        assert len(flow["steps"])>=2
        for category,tool in flow["steps"]:
            assert tool_exists(category,tool)
    for i,flow in enumerate(WORKFLOWS):
        assert workflow_steps(i)==flow["steps"]

@pytest.mark.parametrize("index",[-1,99,1.5,True])
def test_bad_workflow_index(index):
    with pytest.raises(ValueError):
        workflow_steps(index)

def test_report_destinations_exist():
    for category,tool,_ in REPORT_TOOLS:
        assert tool_exists(category,tool)

def test_favorites_deduplicate_and_prune():
    items=[("Signal analysis","RF Filter Design Laboratory")]*2
    items.extend([("Unknown","Unknown"),("Projects","Project Library")])
    assert normalize_favorites(items)==[
        ("Signal analysis","RF Filter Design Laboratory"),("Projects","Project Library")]
    assert len(normalize_favorites(all_tools()))<=8

def test_v4_navigation():
    assert "Guided Workflows" in WORKSPACES["Professional workspace"]
    assert "Report Center" in WORKSPACES["Professional workspace"]
