from agentic_sdlc.graph import build_workflow
from agentic_sdlc.graph import run_workflow
import pytest


def test_workflow_runs_each_delivery_stage():
    result = build_workflow().invoke({"task": "Add a customer enquiry endpoint"})

    assert result["task"] == "Add a customer enquiry endpoint"
    assert len(result["plan"]) == 3
    assert len(result["architecture"]) == 3
    assert len(result["implementation_notes"]) == 3


def test_empty_task_is_rejected():
    try:
        build_workflow().invoke({"task": "   "})
    except ValueError as error:
        assert str(error) == "A non-empty task is required."
    else:
        raise AssertionError("Expected an empty task to be rejected.")


def test_demo_is_explicit_and_never_generates_code(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    result = run_workflow("  Plan a small application  ")
    assert result["mode"] == "demo"
    assert result["engine"] == "langgraph"
    assert result["task"] == "Plan a small application"
    assert result["files"] == []


def test_fallback_preserves_result_contract(monkeypatch):
    import agentic_sdlc.graph as graph
    expected = run_workflow("Build an enquiry endpoint")
    monkeypatch.setattr(graph, "StateGraph", None)
    actual = graph.run_workflow("Build an enquiry endpoint")
    assert actual.pop("engine") == "compatibility"
    expected.pop("engine")
    assert actual == expected


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError, match="Choose"):
        run_workflow("test", "unknown")

