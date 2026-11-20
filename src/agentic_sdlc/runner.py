"""Command-line and local web entry point."""

import argparse
import json

from .graph import run_workflow
from .validation import InputError, ProviderError


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv(".env", override=False)
    parser = argparse.ArgumentParser(description="Plan software in demo or AI mode, or open the local workbench.")
    parser.add_argument("task", nargs="?", help="The software-delivery task to plan.")
    parser.add_argument("--mode", choices=("demo", "openai"), default="demo")
    parser.add_argument("--serve", action="store_true", help="Start the local browser interface.")
    parser.add_argument("--port", type=int, default=8000, help="Local web port (default: 8000).")
    args = parser.parse_args()
    if args.serve:
        if args.task is not None or args.mode != "demo":
            parser.error("With --serve, enter the task and choose the mode in your browser.")
        if not 1 <= args.port <= 65535:
            parser.error("Port must be between 1 and 65535.")
        try:
            import uvicorn
            from .web import create_app
        except ImportError:
            parser.exit(2, 'Install web support: python -m pip install -e ".[web]"\n')
        print(f"Open http://127.0.0.1:{args.port} — press Ctrl+C to stop.", flush=True)
        uvicorn.run(create_app(), host="127.0.0.1", port=args.port, log_level="warning")
        return
    if args.task is None:
        parser.error("Enter a task, or use --serve to open the browser interface.")
    try:
        result = run_workflow(args.task, args.mode)
    except (InputError, ProviderError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

