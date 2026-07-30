"""Exercise the release landing page and built Marimo WASM applications."""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import threading
import time
from collections.abc import Callable
from pathlib import Path

from playwright.sync_api import ConsoleMessage, Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

TIMEOUT_MS = 180_000
LOCAL_DEMO_COUNT = 3


class BrowserSmokeError(RuntimeError):
    """A browser journey violated a release contract."""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Serve an export without adding request noise to CI logs."""

    def log_message(self, format: str, *args: object) -> None:
        return


def _serve(root: Path) -> tuple[http.server.ThreadingHTTPServer, str]:
    handler = functools.partial(QuietHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}/"


def _wait_for_recompute(
    page: Page,
    action: Callable[[], None],
    expected: Callable[[], None],
) -> None:
    action()
    deadline = time.monotonic() + (TIMEOUT_MS / 1000)
    while time.monotonic() < deadline:
        try:
            expected()
            return
        except PlaywrightTimeoutError:
            page.wait_for_timeout(5_000)
    raise BrowserSmokeError("WASM worker did not complete the expected recomputation")


def _assert_common_page_contracts(
    page: Page,
    console_errors: list[str],
    page_errors: list[str],
) -> None:
    if page.locator("h1").count() != 1:
        raise BrowserSmokeError("page must expose exactly one level-one heading")
    unnamed_tables = page.locator(
        "table:not([aria-label]):not([aria-labelledby]):not(:has(caption))"
    ).count()
    if unnamed_tables:
        raise BrowserSmokeError(f"page contains {unnamed_tables} unnamed table(s)")
    if console_errors or page_errors:
        raise BrowserSmokeError(
            f"browser errors: console={console_errors!r}; page={page_errors!r}"
        )


def _exercise_landing(page: Page, root: Path) -> None:
    page.get_by_role(
        "heading",
        name="Cloud, data, and AI systems built for evidence.",
        level=1,
    ).wait_for(state="visible", timeout=TIMEOUT_MS)
    page.get_by_role("main").wait_for(state="visible")
    if page.get_by_role("navigation", name="Primary").count() != 1:
        raise BrowserSmokeError("landing page must expose one named primary navigation")

    internal_hrefs = page.locator('a[href^="./apps/"]').evaluate_all(
        "(links) => [...new Set(links.map((link) => link.getAttribute('href')))]"
    )
    if len(internal_hrefs) != LOCAL_DEMO_COUNT:
        raise BrowserSmokeError("landing page must link all three local browser demos")
    for href in internal_hrefs:
        if href is None:
            raise BrowserSmokeError("local demo link is missing href")
        target = root / href.removeprefix("./")
        if not (target / "index.html").is_file():
            raise BrowserSmokeError(f"local demo link has no built target: {href}")

    page.keyboard.press("Tab")
    if page.evaluate("document.activeElement?.textContent?.trim()") != "Skip to work":
        raise BrowserSmokeError("skip link must be first keyboard focus")
    page.keyboard.press("Enter")
    if page.evaluate("document.activeElement?.id") != "work":
        raise BrowserSmokeError("skip link must move focus to the work section")

    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(100)
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    if overflow > 1:
        raise BrowserSmokeError(f"landing page overflows mobile viewport by {overflow}px")


def _exercise_wellness(page: Page) -> None:
    page.get_by_role("heading", name="Synthetic Wellness Data Pipeline", level=1).wait_for(
        state="visible", timeout=TIMEOUT_MS
    )
    page.wait_for_timeout(10_000)
    seed = page.get_by_role("textbox").first
    table = page.get_by_role("table").first
    table.wait_for(state="visible", timeout=TIMEOUT_MS)
    before = table.inner_text()
    seed.fill("2027")
    seed.press("Enter")
    deadline = time.monotonic() + (TIMEOUT_MS / 1000)
    while time.monotonic() < deadline:
        normalized_seed = seed.input_value().replace(",", "")
        if normalized_seed == "2027" and table.inner_text() != before:
            return
        page.wait_for_timeout(2_000)
    raise BrowserSmokeError("wellness fixture did not react to the seed change")


def _exercise_classifier(page: Page) -> None:
    page.get_by_role("heading", name="Content Performance Classifier", level=1).wait_for(
        state="visible", timeout=TIMEOUT_MS
    )
    page.wait_for_timeout(10_000)
    slider = page.get_by_role("slider").first

    def action() -> None:
        slider.focus()
        slider.press("ArrowRight")

    def expected() -> None:
        page.get_by_text("Exploratory threshold: 0.55", exact=False).wait_for(
            state="visible", timeout=10_000
        )

    _wait_for_recompute(page, action, expected)
    page.get_by_text(
        "Validation-selected reporting threshold: 0.45",
        exact=False,
    ).wait_for(state="visible", timeout=10_000)


def _exercise_opportunity(page: Page) -> None:
    page.get_by_role(
        "heading",
        name="Public-sector Opportunity Pipeline",
        level=1,
    ).wait_for(state="visible", timeout=TIMEOUT_MS)
    page.wait_for_timeout(10_000)
    remote = page.get_by_role("switch", name="Prefer remote or flexible work")
    table = page.get_by_role(
        "table",
        name="Canonical opportunities with additive contributions",
    )
    table.wait_for(state="visible", timeout=TIMEOUT_MS)
    before = table.inner_text()

    def action() -> None:
        if remote.is_checked():
            remote.click()

    action()
    deadline = time.monotonic() + (TIMEOUT_MS / 1000)
    while time.monotonic() < deadline:
        if table.inner_text() != before:
            return
        page.wait_for_timeout(2_000)
    raise BrowserSmokeError("opportunity scoring did not react to remote preference")


SCENARIOS: dict[str, Callable[[Page], None]] = {
    "wellness": _exercise_wellness,
    "classifier": _exercise_classifier,
    "opportunity": _exercise_opportunity,
}


def _exercise(page: Page, url: str, scenario: str, root: Path) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []

    def capture_console(message: ConsoleMessage) -> None:
        if message.type == "error":
            console_errors.append(message.text)

    page.on("console", capture_console)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)

    if scenario == "landing":
        _exercise_landing(page, root)
    else:
        SCENARIOS[scenario](page)
    _assert_common_page_contracts(page, console_errors, page_errors)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("site_root", type=Path)
    parser.add_argument(
        "--scenario",
        choices=["landing", *SCENARIOS],
        required=True,
    )
    parser.add_argument("--path", default="")
    args = parser.parse_args()
    root = args.site_root.resolve()
    server, base_url = _serve(root)
    url = f"{base_url}{args.path.lstrip('/')}"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.emulate_media(reduced_motion="reduce")
                _exercise(page, url, args.scenario, root)
            finally:
                browser.close()
    finally:
        with contextlib.suppress(Exception):
            server.shutdown()
            server.server_close()
    print(f"browser interaction smoke passed: {args.scenario}")


if __name__ == "__main__":
    main()
