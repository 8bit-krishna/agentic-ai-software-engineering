"""A loopback-only web workbench; not an unauthenticated public API."""

import asyncio
import json
import time
from collections import deque
from importlib.resources import files
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError, field_validator
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .graph import run_workflow
from .provider import openai_available
from .validation import Contract, InputError, ProviderError, validate_task


class WorkflowRequest(Contract):
    task: str
    mode: Literal["demo", "openai"] = "demo"

    @field_validator("task")
    @classmethod
    def valid_task(cls, value):
        return validate_task(value)


def failure(message, status=400):
    return JSONResponse({"error": message}, status_code=status)


def create_app(executor=run_workflow) -> FastAPI:
    app = FastAPI(title="Agentic Workbench", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])
    app.state.executor = executor
    app.state.running = asyncio.Lock()
    app.state.recent = deque()

    @app.middleware("http")
    async def security_headers(request, call_next):
        # A local-only listener is still vulnerable to requests from other tabs.
        origin = request.headers.get("origin")
        if request.method == "POST" and origin and origin != str(request.base_url).rstrip("/"):
            response = failure("This request must come from the local workbench.", 403)
        else:
            response = await call_next(request)
        response.headers.update({
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
                "connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; "
                "frame-ancestors 'none'; form-action 'self'",
        })
        return response

    @app.get("/")
    def index():
        return Response(files("agentic_sdlc").joinpath("static/index.html").read_bytes(), media_type="text/html")

    @app.get("/assets/{name}")
    def asset(name: str):
        types = {"app.js": "text/javascript", "styles.css": "text/css"}
        if name not in types:
            return failure("Not found.", 404)
        return Response(files("agentic_sdlc").joinpath(f"static/{name}").read_bytes(), media_type=types[name])

    @app.get("/api/config")
    def config():
        return {"demo": True, "openai": openai_available(), "max_task_length": 4000}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/workflow")
    async def workflow(request: Request):
        if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
            return failure("Send the task as JSON.", 415)
        length = request.headers.get("content-length")
        if length is not None and (not length.isdigit() or int(length) > 32768):
            return failure("The request is too large or has an invalid length.", 413)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 32768:
                return failure("The request is too large.", 413)
        try:
            data = WorkflowRequest.model_validate(json.loads(body))
        except (ValueError, ValidationError):
            return failure("Enter a text task of 1–4,000 characters and choose demo or openai mode.", 422)
        if data.mode == "openai" and not openai_available():
            return failure("AI mode is not configured. Install AI support and set OPENAI_API_KEY in your local .env, then restart.", 503)
        if app.state.running.locked():
            return failure("A workflow is already running. Wait for it to finish.", 429)
        now = time.monotonic()
        while app.state.recent and app.state.recent[0] <= now - 60:
            app.state.recent.popleft()
        if len(app.state.recent) >= 6:
            return failure("Too many requests. Wait one minute before trying again.", 429)
        async with app.state.running:
            app.state.recent.append(now)
            try:
                result = await run_in_threadpool(app.state.executor, data.task, data.mode)
            except InputError as error:
                return failure(str(error), 422)
            except ProviderError as error:
                return failure(str(error), 502)
            except Exception:
                return failure("The workflow could not finish. Please try again later.", 500)
        return JSONResponse(result)

    return app
