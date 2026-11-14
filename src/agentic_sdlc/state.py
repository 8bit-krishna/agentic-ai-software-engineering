"""State shared by the workflow stages."""

from typing import TypedDict


class DeliveryState(TypedDict, total=False):
    """Structured output for a single software-delivery request."""

    task: str
    plan: list[str]
    architecture: list[str]
    implementation_notes: list[str]
