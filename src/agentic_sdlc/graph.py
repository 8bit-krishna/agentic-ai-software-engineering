"""LangGraph assembly for the Planner → Architect → Coder workflow."""

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - only used where native dependencies are blocked
    END = START = StateGraph = None

from .agents import architect, coder, planner
from .state import DeliveryState


def build_workflow():
    """Build a deterministic, credential-free LangGraph workflow.

    Some managed Windows environments block a transitive native dependency of
    LangGraph. The fallback preserves the same ``invoke`` contract so the
    example remains runnable there; normal installations use LangGraph.
    """
    if StateGraph is None:
        return _FallbackWorkflow()
    workflow = StateGraph(DeliveryState)
    workflow.add_node("planner", planner)
    workflow.add_node("architect", architect)
    workflow.add_node("coder", coder)
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "architect")
    workflow.add_edge("architect", "coder")
    workflow.add_edge("coder", END)
    return workflow.compile()


class _FallbackWorkflow:
    """Minimal compatibility runner for environments that cannot import LangGraph."""

    def invoke(self, state: DeliveryState) -> DeliveryState:
        result = dict(state)
        for stage in (planner, architect, coder):
            result.update(stage(result))
        return result
