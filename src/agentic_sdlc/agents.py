"""Deterministic stage implementations.

They make the workflow usable without credentials. A production model adapter
can replace these functions while retaining the validated state contract.
"""

from .state import DeliveryState


def planner(state: DeliveryState) -> DeliveryState:
    task = state["task"].strip()
    if not task:
        raise ValueError("A non-empty task is required.")
    return {"plan": [
        f"Clarify acceptance criteria for: {task}",
        "Identify affected components and data contracts.",
        "Define focused tests before implementation.",
    ]}


def architect(state: DeliveryState) -> DeliveryState:
    return {"architecture": [
        "Keep inputs, workflow state, and delivery artifacts separate.",
        "Make external integrations explicit and configurable.",
        f"Use the plan's {len(state['plan'])} steps as the implementation boundary.",
    ]}


def coder(state: DeliveryState) -> DeliveryState:
    return {"implementation_notes": [
        "Implement the smallest change that satisfies the agreed acceptance criteria.",
        "Validate normal, invalid, and boundary inputs with automated tests.",
        f"Review the {len(state['architecture'])} architecture constraints before handoff.",
    ]}
