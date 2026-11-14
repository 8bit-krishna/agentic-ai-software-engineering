from agentic_sdlc.graph import build_workflow


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
