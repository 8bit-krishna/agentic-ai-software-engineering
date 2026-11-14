# Agentic AI Software Engineering

A small, runnable LangGraph foundation for a software-delivery workflow:

```text
Planner → Architect → Coder
```

Given a task, the workflow produces a structured plan, architecture constraints,
and implementation notes. It is intentionally deterministic and runs without
API keys or network calls.

## What this project is—and is not

This is a working workflow foundation, not a finished autonomous coding agent.
The current stages use deterministic functions so that the graph can be tested
and demonstrated safely. A future model-provider adapter can replace those
stage functions without changing the graph or state contract. No model calls,
file edits, command execution, or deployments occur from this project. In a
managed environment that blocks LangGraph's native transitive dependencies,
the same ordered workflow automatically uses a small compatibility runner.

## Run it

Requires Python 3.11–3.14. On Windows, Python 3.13 is recommended.

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
agentic-sdlc "Add a customer enquiry endpoint"
pytest
```

On macOS or Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

The command prints JSON containing `plan`, `architecture`, and
`implementation_notes`.

## Project layout

```text
src/agentic_sdlc/
  agents.py       # deterministic Planner, Architect, and Coder stages
  graph.py        # LangGraph workflow assembly
  state.py        # shared state contract
  runner.py       # command-line entry point
tests/
  test_workflow.py
```

## Next extension

To integrate a model provider, add an adapter that accepts a task and returns
validated structured output for each stage. Keep credentials in environment
variables and add tests using mocked provider responses. Do not commit API keys.
