"""Planner → Architect → Coder in explicit demo or OpenAI mode."""

from collections.abc import Mapping
from typing import Protocol

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    END = START = StateGraph = None

from .agents import architect, coder, planner
from .state import DeliveryState
from .validation import InputError, validate_task


class StageProvider(Protocol):
    def plan(self, state: DeliveryState) -> DeliveryState: ...
    def design(self, state: DeliveryState) -> DeliveryState: ...
    def implement(self, state: DeliveryState) -> DeliveryState: ...


def build_workflow(mode: str = "demo", provider: StageProvider | None = None):
    if mode not in ("demo", "openai"):
        raise InputError("Choose demo or openai mode.")
    if mode == "openai" and provider is None:
        from .provider import OpenAIProvider
        provider = OpenAIProvider.from_environment()
    if mode == "demo" and provider is not None:
        raise InputError("A model provider requires openai mode.")
    stages = (planner, architect, coder) if mode == "demo" else (
        provider.plan, provider.design, provider.implement,
    )

    def prepare(state):
        if not isinstance(state, Mapping):
            raise InputError("Workflow input must contain a text task.")
        return {"task": validate_task(state.get("task")), "mode": mode,
                "engine": "langgraph" if StateGraph is not None else "compatibility",
                "plan": [], "architecture": [], "implementation_notes": [],
                "files": [], "test_plan": []}

    if StateGraph is None:
        return _FallbackWorkflow(prepare, stages)
    workflow = StateGraph(DeliveryState)
    workflow.add_node("validate", prepare)
    for name, stage in zip(("planner", "architect", "coder"), stages):
        workflow.add_node(name, stage)
    workflow.add_edge(START, "validate")
    workflow.add_edge("validate", "planner")
    workflow.add_edge("planner", "architect")
    workflow.add_edge("architect", "coder")
    workflow.add_edge("coder", END)
    return workflow.compile()


class _FallbackWorkflow:
    def __init__(self, prepare, stages):
        self.prepare, self.stages = prepare, stages

    def invoke(self, state):
        result = self.prepare(state)
        for stage in self.stages:
            result.update(stage(result))
        return result


def run_workflow(task: object, mode: str = "demo", provider: StageProvider | None = None) -> dict:
    # Validate before reading credentials or making any provider calls.
    task = validate_task(task)
    return dict(build_workflow(mode, provider).invoke({"task": task}))

