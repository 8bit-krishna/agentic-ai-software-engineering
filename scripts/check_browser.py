"""Check the local demo workflow and downloads in a real browser."""

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright


def wait_for_server(url, process):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("The demo server stopped before becoming ready.")
        try:
            with urlopen(url + "/health", timeout=1) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError):
            time.sleep(0.2)
    raise RuntimeError("The demo server did not become ready.")


def check_browser(url, output):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            context = browser.new_context(
                viewport={"width": 1440, "height": 1000},
                accept_downloads=True,
            )
            page = context.new_page()
            with page.expect_response("**/api/config") as configured:
                page.goto(url)
            assert configured.value.json()["openai"] is False
            expect(page.locator("#ai-mode")).to_be_disabled()

            task = page.get_by_label("Describe your software task")
            task.fill("   ")
            page.get_by_role("button", name="Run workflow").click()
            expect(page.get_by_role("alert")).to_have_text(
                "Please describe what you want to build."
            )

            brief = "Build a Python expense tracker with CSV storage and tests."
            task.fill(brief)
            page.get_by_role("button", name="Run workflow").click()
            expect(page.get_by_role("status")).to_have_text(
                "Workflow complete. Your results are ready below."
            )
            expect(page.locator("#result-task")).to_have_text(brief)
            expect(page.locator("#result-mode")).to_have_text(
                "DEMO RESULT · PREDEFINED NOTES"
            )
            expect(page.locator(".stage-state")).to_have_text(["Done"] * 3)
            expect(page.locator("#result-body .result-section")).to_have_count(4)

            with page.expect_download() as exported:
                page.get_by_role("button", name="Download JSON", exact=True).click()
            downloaded = exported.value
            assert downloaded.suggested_filename == "workflow-result.json"
            json_path = output / downloaded.suggested_filename
            downloaded.save_as(json_path)
            result = json.loads(json_path.read_text(encoding="utf-8"))
            assert result["mode"] == "demo"
            assert result["task"] == brief
            assert result["files"] == []
            assert all(result[key] for key in (
                "plan", "architecture", "implementation_notes", "test_plan"
            ))

            with page.expect_download() as exported:
                page.get_by_role("button", name="Download Markdown", exact=True).click()
            downloaded = exported.value
            assert downloaded.suggested_filename == "workflow-result.md"
            markdown_path = output / downloaded.suggested_filename
            downloaded.save_as(markdown_path)
            markdown = markdown_path.read_text(encoding="utf-8")
            assert brief in markdown
            assert "Mode: demo" in markdown
            assert "## Plan" in markdown and "## Test plan" in markdown

            page.screenshot(path=str(output / "desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            ), "The mobile layout overflows horizontally."
            page.screenshot(path=str(output / "mobile.png"), full_page=True)
        finally:
            browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    output = parser.parse_args().output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    environment = dict(os.environ, OPENAI_API_KEY="")
    with tempfile.TemporaryDirectory() as temporary:
        log_path = Path(temporary) / "server.log"
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn",
                 "agentic_sdlc.web:create_app", "--factory",
                 "--host", "127.0.0.1", "--port", str(port)],
                env=environment, stdout=log, stderr=subprocess.STDOUT,
            )
            try:
                wait_for_server(url, process)
                check_browser(url, output)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    print("Browser checks passed for demo results, JSON/Markdown downloads and mobile layout.")


if __name__ == "__main__":
    main()
