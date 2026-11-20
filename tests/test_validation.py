import pytest
from pydantic import ValidationError

from agentic_sdlc.graph import run_workflow
from agentic_sdlc.validation import GeneratedFile, InputError, validate_task


@pytest.mark.parametrize("task", [None, 42, [], {}, "", " \n\t ", "x" * 4001, "bad\x00task"])
def test_bad_tasks_are_actionable(task):
    with pytest.raises(InputError):
        validate_task(task)


def test_normalizes_whitespace_and_preserves_unicode():
    assert validate_task("  தமிழ்\ncustomer enquiry  ") == "தமிழ்\ncustomer enquiry"


def test_validation_happens_before_provider_setup(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(InputError, match="non-empty"):
        run_workflow(" ", "openai")


@pytest.mark.parametrize("path", ["../key", "/tmp/code", "C:/key", "src\\app.py", "a//b.py", "./app.py", "a\x00.py", "a?.py", "CON", "src/LPT1.py", "app.py.", "file "])
def test_export_paths_cannot_escape_or_use_unsafe_names(path):
    with pytest.raises(ValidationError):
        GeneratedFile(path=path, content="example")


def test_relative_path_is_preserved():
    assert GeneratedFile(path="src/app.py", content="print('hello')").path == "src/app.py"
