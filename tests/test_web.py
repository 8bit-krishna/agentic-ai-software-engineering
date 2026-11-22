import asyncio
import threading

import httpx
import pytest
from fastapi.testclient import TestClient

from agentic_sdlc.web import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with TestClient(create_app(), base_url="http://127.0.0.1:8000") as client:
        yield client


def test_interface_and_assets_are_packaged(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Agentic Workbench" in response.text
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/assets/styles.css").status_code == 200
    assert client.get("/.env").status_code == 404
    assert client.get("/assets/secrets.txt").status_code == 404
    assert "script-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"


def test_demo_roundtrip(client):
    response = client.post("/api/workflow", json={"task": " Build an enquiry API "}, headers={"Origin": "http://127.0.0.1:8000"})
    assert response.status_code == 200
    data = response.json()
    assert data["task"] == "Build an enquiry API"
    assert data["mode"] == "demo"
    assert data["engine"] == "langgraph"
    assert data["files"] == []
    assert data["test_plan"]


@pytest.mark.parametrize("body", [{}, [], {"task": 42}, {"task": None}, {"task": " "},
    {"task": "x" * 4001}, {"task": "test", "mode": "unknown"}, {"task": "test", "api_key": "secret"}])
def test_invalid_requests(client, body):
    assert client.post("/api/workflow", json=body).status_code == 422


def test_invalid_json_and_content_type(client):
    assert client.post("/api/workflow", content="bad", headers={"content-type": "application/json"}).status_code == 422
    assert client.post("/api/workflow", content='{"task":"test"}', headers={"content-type": "text/plain"}).status_code == 415


def test_limits_request_size(client):
    assert client.post("/api/workflow", content=b"x" * 33000, headers={"content-type": "application/json"}).status_code == 413


def test_cross_origin_and_rebinding_are_rejected(client):
    assert client.post("/api/workflow", json={"task": "test"}, headers={"origin": "https://evil.example"}).status_code == 403
    assert client.get("/", headers={"host": "evil.example"}).status_code == 400


def test_missing_ai_config_does_not_fall_back_to_demo(client):
    assert client.get("/api/config").json()["openai"] is False
    response = client.post("/api/workflow", json={"task": "test", "mode": "openai"})
    assert response.status_code == 503
    assert "plan" not in response.json()


def test_internal_errors_are_redacted():
    def broken(task, mode):
        raise RuntimeError("secret-and-private-input")
    with TestClient(create_app(broken), base_url="http://127.0.0.1") as client:
        response = client.post("/api/workflow", json={"task": "test"})
        assert response.status_code == 500
        assert "secret-and-private-input" not in response.text


def test_config_does_not_return_the_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "do-not-expose-me")
    with TestClient(create_app(), base_url="http://127.0.0.1") as client:
        response = client.get("/api/config")
        assert response.json()["openai"] is True
        assert "do-not-expose-me" not in response.text


def test_rate_limit(client):
    for _ in range(6):
        assert client.post("/api/workflow", json={"task": "test"}).status_code == 200
    assert client.post("/api/workflow", json={"task": "test"}).status_code == 429


def test_only_one_workflow_runs_at_a_time():
    entered, release = threading.Event(), threading.Event()

    def slow(task, mode):
        entered.set()
        release.wait(3)
        return {"task": task, "mode": mode}

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(slow)), base_url="http://127.0.0.1") as client:
            first = asyncio.create_task(client.post("/api/workflow", json={"task": "one"}))
            try:
                await asyncio.wait_for(asyncio.to_thread(entered.wait, 2), 3)
                assert entered.is_set()
                assert (await client.post("/api/workflow", json={"task": "two"})).status_code == 429
            finally:
                release.set()
            assert (await first).status_code == 200
    asyncio.run(exercise())
