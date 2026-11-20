import json

import pytest

from agentic_sdlc.runner import main


def test_cli_demo(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["agentic-sdlc", "Build an enquiry API"])
    main()
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "demo"
    assert result["plan"]


@pytest.mark.parametrize("args", [[], [" "], ["--mode", "bad", "test"], ["--serve", "test"], ["--serve", "--port", "0"]])
def test_cli_errors_are_readable(monkeypatch, capsys, args):
    monkeypatch.setattr("sys.argv", ["agentic-sdlc", *args])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert "Traceback" not in capsys.readouterr().err


def test_cli_missing_key(monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("sys.argv", ["agentic-sdlc", "--mode", "openai", "test"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert "OPENAI_API_KEY" in capsys.readouterr().err


def test_server_binds_only_loopback(monkeypatch):
    calls = []
    monkeypatch.setattr("sys.argv", ["agentic-sdlc", "--serve", "--port", "8123"])
    monkeypatch.setattr("uvicorn.run", lambda app, **kwargs: calls.append(kwargs))
    main()
    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["port"] == 8123
