"""Command-line entry point for the workflow."""

import argparse
import json

from .graph import build_workflow


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LangGraph delivery workflow.")
    parser.add_argument("task", help="The software-delivery task to plan.")
    args = parser.parse_args()
    result = build_workflow().invoke({"task": args.task})
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
