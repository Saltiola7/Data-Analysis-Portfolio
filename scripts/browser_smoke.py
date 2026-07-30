"""Exercise built Marimo WASM applications."""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import json
import threading
import time
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import ConsoleMessage, Frame, Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

TIMEOUT_MS = 180_000
ConsoleRecord = tuple[str, str]
type ContentTarget = Page | Frame

_RUNTIME_ERROR_MARKERS = (
    "modulenotfounderror",
    "no module named",
    "traceback (most recent call last)",
    "marimoexceptionraisederror",
    "cellnotinitializederror",
    "ancestor raised",
)


def _is_runtime_error(message: str) -> bool:
    """Return whether browser output exposes a failed Python/Marimo runtime."""

    normalized = message.casefold()
    compact = "".join(normalized.split())
    return '"type":"exception"' in compact or any(
        marker in normalized for marker in _RUNTIME_ERROR_MARKERS
    )


def _is_allowed_remote_noise(message: str) -> bool:
    """Recognize only known, non-application Molab telemetry diagnostics."""

    if _is_runtime_error(message):
        return False
    normalized = message.casefold()
    required_fragments = (
        ("debug:", "loading pyodide packages"),
        ("relay.vector.co", "403"),
        ("api.cr-relay.com", "403"),
        ("visitor id", "unavailable"),
        ("no visitor id available",),
        ("load failed, error in settings", "[https://molab.marimo.io/"),
        ("export_demos/wasm-intro.py", "404"),
    )
    return any(
        all(fragment in normalized for fragment in fragments) for fragments in required_fragments
    )


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


def _has_live_learning_lab_evidence(
    console_messages: list[ConsoleRecord],
) -> bool:
    live_outputs = [message for _, message in console_messages if "cell-op" in message.casefold()]
    return (
        any("Success: analysis ready." in message for message in live_outputs)
        and any("fixture-identity" in message for message in live_outputs)
        and any("primary-table" in message for message in live_outputs)
    )


def _wait_for_live_learning_lab(
    page: Page,
    console_messages: list[ConsoleRecord],
) -> None:
    deadline = time.monotonic() + (TIMEOUT_MS / 1000)
    while time.monotonic() < deadline:
        runtime_errors = [
            f"{severity}: {message}"
            for severity, message in console_messages
            if _is_runtime_error(message)
        ]
        if runtime_errors:
            raise BrowserSmokeError(
                f"learning-lab runtime failed before interaction: {runtime_errors!r}"
            )
        if _has_live_learning_lab_evidence(console_messages):
            return
        page.wait_for_timeout(500)
    raise BrowserSmokeError("learning lab never emitted live success, fixture, and table evidence")


def _wait_for_recompute(
    page: ContentTarget,
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
    content: ContentTarget,
    console_messages: list[ConsoleRecord],
    page_errors: list[str],
    *,
    remote: bool,
) -> None:
    if content.locator("h1").count() != 1:
        raise BrowserSmokeError("page must expose exactly one level-one heading")
    unnamed_tables = content.locator(
        "table:not([aria-label]):not([aria-labelledby]):not(:has(caption))"
    ).count()
    if unnamed_tables:
        raise BrowserSmokeError(f"page contains {unnamed_tables} unnamed table(s)")
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(500)
    if content.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
    ):
        raise BrowserSmokeError("page causes horizontal document overflow at 390px")

    console_errors = [
        f"{severity}: {message}"
        for severity, message in console_messages
        if _is_runtime_error(message)
        or (severity == "error" and not (remote and _is_allowed_remote_noise(message)))
    ]
    fatal_page_errors = [
        message for message in page_errors if not (remote and _is_allowed_remote_noise(message))
    ]
    if console_errors or fatal_page_errors:
        raise BrowserSmokeError(
            f"browser errors: console={console_errors!r}; page={fatal_page_errors!r}"
        )


def _exercise_wellness(page: ContentTarget) -> None:
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


def _exercise_classifier(page: ContentTarget) -> None:
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


def _exercise_opportunity(page: ContentTarget) -> None:
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


def _exercise_learning_lab(page: ContentTarget) -> None:
    page.locator("h1").wait_for(state="visible", timeout=TIMEOUT_MS)
    page.get_by_text("Success: analysis ready.", exact=True).wait_for(
        state="visible",
        timeout=TIMEOUT_MS,
    )
    seed_label = page.locator("label").filter(has_text="Seed")
    if seed_label.count() != 1 or seed_label.inner_text().strip() != "Seed":
        raise BrowserSmokeError("learning lab must expose one visible Seed label")
    seed_target = seed_label.get_attribute("for")
    if not seed_target:
        raise BrowserSmokeError("Seed label must identify its input")
    seed = page.locator(f'input[id="{seed_target}"]')
    if seed.count() != 1 or seed.get_attribute("inputmode") not in {
        "decimal",
        "numeric",
    }:
        raise BrowserSmokeError("Seed label must target one numeric input")
    fixture_identity = page.locator('[data-testid="fixture-identity"]')
    primary_table = page.get_by_role("table").first
    seed.wait_for(state="visible", timeout=TIMEOUT_MS)
    fixture_identity.wait_for(state="visible", timeout=TIMEOUT_MS)
    primary_table.wait_for(state="visible", timeout=TIMEOUT_MS)
    caption = primary_table.locator("caption")
    if caption.count() != 1:
        raise BrowserSmokeError("learning-lab primary table must expose one caption")

    before_fixture = fixture_identity.inner_text()
    before_table = primary_table.inner_text()
    seed.fill("2027")
    seed.press("Enter")

    deadline = time.monotonic() + (TIMEOUT_MS / 1000)
    while time.monotonic() < deadline:
        normalized_seed = seed.input_value().replace(",", "")
        if (
            normalized_seed == "2027"
            and fixture_identity.inner_text() != before_fixture
            and primary_table.inner_text() != before_table
            and "pandas=3.0.2" in fixture_identity.inner_text()
        ):
            break
        page.wait_for_timeout(2_000)
    else:
        raise BrowserSmokeError(
            "learning lab did not update under pandas 3.0.2 after the seed change"
        )

    seed.fill("")
    seed.press("Enter")
    page.get_by_text(
        "Validation error: seed must be an integer from 0 to 999999",
        exact=False,
    ).first.wait_for(state="visible", timeout=TIMEOUT_MS)
    if page.locator('table[data-testid="primary-table"]').count():
        raise BrowserSmokeError("invalid seed retained partial primary-table evidence")
    if "Validation error:" not in fixture_identity.inner_text():
        raise BrowserSmokeError("invalid seed did not replace fixture identity")


SCENARIOS: dict[str, Callable[[ContentTarget], None]] = {
    "wellness": _exercise_wellness,
    "classifier": _exercise_classifier,
    "opportunity": _exercise_opportunity,
    "learning-labs": _exercise_learning_lab,
}


def _console_text(message: ConsoleMessage) -> str:
    """Preserve structured worker payloads that ``message.text`` collapses."""

    rendered_args: list[str] = []
    for argument in message.args:
        try:
            value = argument.json_value()
        except Exception:
            value = str(argument)
        if isinstance(value, (dict, list)):
            rendered_args.append(json.dumps(value, sort_keys=True, default=str))
        elif value is not None:
            rendered_args.append(str(value))
    return " ".join(rendered_args).strip() or message.text


def _remote_content_frame(page: Page) -> Frame:
    deadline = time.monotonic() + (TIMEOUT_MS / 1000)
    while time.monotonic() < deadline:
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            if "entrypoint=" in frame.url and "/e?" in frame.url:
                return frame
        page.wait_for_timeout(500)
    raise BrowserSmokeError("Molab did not expose its embedded Marimo application frame")


def _exercise(page: Page, url: str, scenario: str, *, remote: bool = False) -> None:
    console_messages: list[ConsoleRecord] = []
    page_errors: list[str] = []

    def capture_console(message: ConsoleMessage) -> None:
        location = message.location
        source_url = location.get("url", "")
        console_text = _console_text(message)
        rendered = f"{console_text} [{source_url}]" if source_url else console_text
        console_messages.append((message.type, rendered))

    page.on("console", capture_console)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
    content: ContentTarget = _remote_content_frame(page) if remote else page

    try:
        if scenario == "learning-labs":
            _wait_for_live_learning_lab(page, console_messages)
        SCENARIOS[scenario](content)
    except (BrowserSmokeError, PlaywrightTimeoutError) as error:
        raise BrowserSmokeError(
            f"{error}; console={console_messages!r}; page={page_errors!r}"
        ) from error
    _assert_common_page_contracts(
        page,
        content,
        console_messages,
        page_errors,
        remote=remote,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("site_root", type=Path, nargs="?")
    parser.add_argument("--url")
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS,
        required=True,
    )
    parser.add_argument("--path", default="")
    args = parser.parse_args()

    if (args.site_root is None) == (args.url is None):
        parser.error("provide exactly one local site_root or --url")
    if args.url is not None:
        parsed_url = urlparse(args.url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            parser.error("--url must be an absolute HTTPS URL")
        if args.path:
            parser.error("--path is only valid with a local site_root")
        server = None
        url = args.url
        remote = True
    else:
        root = args.site_root.resolve()
        server, base_url = _serve(root)
        url = f"{base_url}{args.path.lstrip('/')}"
        remote = False

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.emulate_media(reduced_motion="reduce")
                _exercise(page, url, args.scenario, remote=remote)
            finally:
                browser.close()
    finally:
        if server is not None:
            with contextlib.suppress(Exception):
                server.shutdown()
                server.server_close()
    print(f"browser interaction smoke passed: {args.scenario}")


if __name__ == "__main__":
    main()
