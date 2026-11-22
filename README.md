# Agentic AI Software Engineering

A local workbench that turns a software brief into a plan, an architecture, implementation notes and, in AI mode, a small code scaffold.

- **Demo:** runs immediately, with clearly labelled predefined notes and no API key.
- **AI:** three OpenAI Responses calls through a Planner → Architect → Coder LangGraph workflow. Produces task-specific notes, code files and a test plan.
- **Browser or terminal:** choose either interface.
- **Human review:** generated code is displayed as text and is never automatically executed.

## Get started on Windows

Install Python 3.11–3.14 and Git. Python 3.13 is a good Windows starting point.

Open PowerShell in the folder where you keep projects:

~~~powershell
git clone https://github.com/8bit-krishna/agentic-ai-software-engineering.git
cd agentic-ai-software-engineering
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[web,ai]"
.\.venv\Scripts\agentic-sdlc.exe --serve
~~~

Open **http://127.0.0.1:8000**, enter a brief and choose **Demo mode**. No key is needed for the demo.

The explicit interpreter paths work even when PowerShell blocks virtual-environment activation. If you download a ZIP, select `main` on GitHub before choosing **Code > Download ZIP**. Extract it and open the folder containing pyproject.toml before running the venv and install commands.

## Get started on macOS or Linux

~~~bash
git clone https://github.com/8bit-krishna/agentic-ai-software-engineering.git
cd agentic-ai-software-engineering
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[web,ai]"
.venv/bin/agentic-sdlc --serve
~~~

Use --port 8123 if port 8000 is already occupied. Stop the server with Ctrl+C.

## Enable real AI output

1. Copy .env.example to .env in the project root.
2. Enter your own OPENAI_API_KEY in .env locally. Do not paste it into chat, source files or the browser.
3. Set OPENAI_MODEL to a model your API project can access that supports Responses and structured outputs. The example uses gpt-5-mini.
4. Restart the server. Choose **AI mode** and confirm the usage notice before submitting your task.

AI mode sends the brief and prior-stage results to OpenAI. Each workflow makes up to three billable requests. API billing/access is separate from signing in to the workbench; do not assume a ChatGPT subscription includes access. Requests use store=False, a 45-second timeout per stage and no automatic retries. This does not override the provider's data retention policy. Only submit information you are allowed to send to the provider.

A failed or refused model response is reported as an error; the app never silently substitutes demo output.

Official references:
- https://developers.openai.com/api/docs/quickstart
- https://developers.openai.com/api/docs/guides/structured-outputs

## Using the browser workbench

1. Describe one small, focused task. Include intended users and preferred technologies.
2. Select Demo or AI mode. Demo results are predefined and include no generated code.
3. Run the workflow. One workflow runs at a time.
4. Read the plan, architecture, implementation notes and test plan.
5. In AI mode, inspect each generated file as text.
6. Download JSON, Markdown or individual files. Individual download names replace slashes with underscores; restore the displayed directory paths yourself when building the scaffold.

Results remain in the current tab's memory and disappear on refresh. There is no server-side result storage. Model text is rendered with textContent, not executed as HTML.

The app does not write code into your projects, run shell commands or verify generated code. Review every file, install its dependencies in a separate environment and run its tests yourself.

## Terminal use

With the environment activated:

~~~bash
agentic-sdlc "Build a customer enquiry API"
agentic-sdlc --mode openai "Build a small Python expense tracker with CSV storage"
~~~

Without activation, use .venv\Scripts\agentic-sdlc.exe on Windows or .venv/bin/agentic-sdlc on macOS/Linux.

Both commands print JSON with task, mode, engine, plan, architecture, implementation_notes, files and test_plan.

Python callers:

~~~python
from agentic_sdlc.graph import run_workflow

result = run_workflow("Build a customer enquiry API")  # demo
result = run_workflow("Build a small CSV expense tracker", mode="openai")
~~~

## Development and checks

~~~powershell
.\.venv\Scripts\python.exe -m pip install -e ".[web,ai,dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m build --wheel
~~~

The tests cover validation, real LangGraph and the compatibility runner, the CLI, HTTP endpoints, concurrent/rate-limited requests, packaged assets, and the OpenAI adapter using mocked HTTP responses. They do not use real API keys or make paid model calls.

If Node.js 22+ is installed, run `node --test tests/frontend.test.cjs` for the interface and download unit tests. These use a fake DOM; they do not replace visual browser checks. Node is only needed for these optional development tests, not to run the application.

GitHub Actions runs the suite on Linux/Python 3.11–3.14 and Windows/Python 3.13. These CI versions are separate from the developer's local test result.

## Project layout

~~~text
src/agentic_sdlc/
  agents.py       Predefined demo stages
  graph.py        Validated LangGraph assembly and compatibility runner
  provider.py     Optional OpenAI Responses adapter
  validation.py   Input and generated-output contracts
  runner.py       CLI and local server command
  web.py          FastAPI routes and local web protections
  static/         Browser interface, styles and behaviour
tests/            Offline tests, including mocked provider requests
~~~

The compatibility runner is used only when LangGraph cannot be imported. Results identify the backend with engine=compatibility instead of pretending LangGraph ran. Normal installations use engine=langgraph.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| AI mode unavailable | Install the ai extra, set OPENAI_API_KEY in .env, then restart. |
| Authentication or model error | Check the API project's key and model access locally. |
| Quota or rate-limit error | Check API billing/quota or wait before manually retrying. |
| Incomplete output | Ask for a smaller scaffold. |
| Another workflow is running | Wait for it to finish; only one can run at a time. |
| Too many local requests | Wait one minute; the app permits six runs per minute. |
| Port already in use | Start with --serve --port 8123. |

## Hosting and scope

This release is a local developer application. The CLI deliberately binds to 127.0.0.1. Host and Origin checks limit cross-site requests; request bodies and generated filenames are validated. Keys, prompts and results are not written to application logs.

Do not expose this server through a public tunnel or change it to 0.0.0.0 without adding authentication, per-user budgets, HTTPS and deployment controls. Public multi-user hosting and autonomous code execution are outside this release.

The project is MIT licensed. Keep the license notice when reusing it.

