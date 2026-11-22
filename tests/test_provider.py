import json

import httpx
import pytest
from openai import OpenAI

from agentic_sdlc.graph import run_workflow
from agentic_sdlc.provider import OpenAIProvider
from agentic_sdlc.validation import PlanOutput, ProviderError


def envelope(data=None, status="completed", refusal=False):
    content = [{"type": "refusal", "refusal": "Cannot complete"}] if refusal else [
        {"type": "output_text", "text": json.dumps(data), "annotations": []},
    ]
    return {"id": "resp_test", "object": "response", "created_at": 0,
            "model": "gpt-5-mini", "status": status, "output": [
                {"id": "msg_test", "type": "message", "role": "assistant", "status": "completed", "content": content},
            ]}


def client_for(handler):
    return OpenAI(api_key="test-secret", base_url="https://api.openai.com/v1",
                  max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_all_stages_use_structured_responses_and_prior_context():
    calls = []
    outputs = [
        {"plan": ["Validate customer enquiries."]},
        {"architecture": ["Use a small API and SQLite."]},
        {"implementation_notes": ["Review the scaffold."], "files": [
            {"path": "app.py", "content": "print('enquiries')"},
            {"path": "README.md", "content": "Run python app.py"},
        ], "test_plan": ["Check missing customer details."]},
    ]

    def handler(request):
        assert request.url.path == "/v1/responses"
        assert request.headers["authorization"] == "Bearer test-secret"
        body = json.loads(request.content)
        assert "test-secret" not in request.content.decode()
        assert body["store"] is False
        assert body["text"]["format"]["type"] == "json_schema"
        assert body["text"]["format"]["strict"] is True
        calls.append(body)
        return httpx.Response(200, json=envelope(outputs[len(calls) - 1]))

    with client_for(handler) as client:
        result = run_workflow("Build an enquiry API", "openai", OpenAIProvider(client, "gpt-5-mini"))
    assert len(calls) == 3
    assert json.loads(calls[1]["input"])["plan"] == outputs[0]["plan"]
    assert json.loads(calls[2]["input"])["architecture"] == outputs[1]["architecture"]
    assert result["mode"] == "openai"
    assert result["files"][0]["path"] == "app.py"


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500])
def test_provider_errors_do_not_leak_messages_or_retry(status):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"error": {"message": "test-secret raw private task", "type": "api_error"}})

    with client_for(handler) as client:
        with pytest.raises(ProviderError) as error:
            OpenAIProvider(client, "gpt-5-mini").plan({"task": "A test task"})
    assert len(calls) == 1
    assert "test-secret" not in str(error.value)
    assert "raw private task" not in str(error.value)


@pytest.mark.parametrize("data", [{"plan": []}, {"plan": [""]}, {"wrong": ["x"]}])
def test_schema_failures_are_safe(data):
    with client_for(lambda req: httpx.Response(200, json=envelope(data))) as client:
        with pytest.raises(ProviderError):
            OpenAIProvider(client, "gpt-5-mini").plan({"task": "test"})


def test_refusal_is_not_presented_as_success():
    with client_for(lambda req: httpx.Response(200, json=envelope(refusal=True))) as client:
        with pytest.raises(ProviderError, match="rephrase"):
            OpenAIProvider(client, "gpt-5-mini").plan({"task": "test"})


def test_incomplete_response_is_not_presented_as_success():
    with client_for(lambda req: httpx.Response(200, json=envelope({"plan": ["x"]}, status="incomplete"))) as client:
        with pytest.raises(ProviderError):
            OpenAIProvider(client, "gpt-5-mini").plan({"task": "test"})


def test_missing_key_is_actionable(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="OPENAI_API_KEY"):
        OpenAIProvider.from_environment()


def test_timeout_is_safe():
    def handler(request):
        raise httpx.ReadTimeout("test-secret", request=request)
    with client_for(handler) as client:
        with pytest.raises(ProviderError) as error:
            OpenAIProvider(client, "gpt-5-mini").plan({"task": "test"})
    assert "test-secret" not in str(error.value)
