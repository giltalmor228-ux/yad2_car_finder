from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


_LISTING_SELECTOR = 'a[data-nagish="private-item-link"][data-listing-type]'

_JS_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent.parent / "js_browser" / "fetch_page.js"
)


def is_radware_verification_page(html: str, title: str = "") -> bool:
    """Return True when the response is Radware's browser-verification page."""
    combined = f"{title}\n{html}".lower()
    return (
        "radware page" in combined
        or "verifying your browser before proceeding" in combined
    )


class BrowserYad2Client:
    """User-assisted collector backed by a visible Node.js/Playwright (JS) browser.

    The collector intentionally does not automate browser verification. It shells
    out to a small Node.js script (``js_browser/fetch_page.js``) that opens the
    requested page in a visible Chrome window and waits until listing cards
    appear. The Python side never touches Playwright directly; it only launches
    the Node process and reads back the confirmed page HTML from a temp file.
    """

    def __init__(
        self,
        browser_channel: str | None = None,
        timeout_ms: int = 60_000,
        node_executable: str | None = None,
    ):
        self.browser_channel = browser_channel or os.getenv(
            "PLAYWRIGHT_BROWSER_CHANNEL", "chrome"
        )
        self.timeout_ms = timeout_ms
        self.node_executable = node_executable or os.getenv("NODE_EXECUTABLE", "node")
        self.cdp_url = os.getenv("PLAYWRIGHT_CDP_URL", "").strip() or None
        self.reuse_tab = os.getenv("PLAYWRIGHT_REUSE_TAB", "false").lower() == "true"

    def get_page(
        self, url: str, referer: str | None = None, *, require_listings: bool = True
    ) -> str:
        node_bin = shutil.which(self.node_executable)
        if not node_bin:
            raise RuntimeError(
                f"Node.js executable {self.node_executable!r} was not found on PATH. "
                "Install Node.js, then run: "
                "cd js_browser && npm install && npx playwright install chromium"
            )

        if not _JS_SCRIPT_PATH.exists():
            raise RuntimeError(
                f"Browser automation script not found: {_JS_SCRIPT_PATH}"
            )

        with tempfile.NamedTemporaryFile(
            prefix="yad2_page_", suffix=".html", delete=False
        ) as tmp:
            html_out = Path(tmp.name)

        cmd = [
            node_bin,
            str(_JS_SCRIPT_PATH),
            url,
            "--channel",
            self.browser_channel,
            "--timeout-ms",
            str(self.timeout_ms),
            "--html-out",
            str(html_out),
        ]
        if referer:
            cmd += ["--referer", referer]
        if self.cdp_url:
            cmd += ["--cdp-url", self.cdp_url]
        if self.reuse_tab:
            cmd += ["--reuse-tab"]

        if self.cdp_url:
            print(f"\nAttaching to an already-open Chrome at {self.cdp_url}.")
        else:
            print("\nA visible browser window will open (Node.js/Playwright).")
        print("Collecting as soon as listing cards appear.")

        try:
            result = subprocess.run(
                cmd,
                cwd=_JS_SCRIPT_PATH.parent,
                stdout=subprocess.PIPE,
                stderr=None,
                stdin=None,
                text=True,
            )
        except OSError as exc:
            html_out.unlink(missing_ok=True)
            raise RuntimeError(f"Failed to launch Node browser collector: {exc}") from exc

        try:
            if result.returncode != 0:
                raise RuntimeError(
                    f"Browser collection failed (node exited with code {result.returncode})."
                )

            stdout = (result.stdout or "").strip()
            if not stdout:
                raise RuntimeError("Browser collection produced no output.")

            try:
                payload = json.loads(stdout.splitlines()[-1])
            except (json.JSONDecodeError, IndexError) as exc:
                raise RuntimeError(
                    f"Could not parse browser automation output as JSON: {exc}"
                ) from exc

            html_path = Path(payload.get("htmlPath") or html_out)
            if not html_path.exists():
                raise RuntimeError(f"Browser collector did not write HTML to {html_path}")

            html = html_path.read_text(encoding="utf-8")
            title = payload.get("title", "")
            listing_count = payload.get("listingCount", 0)

            if is_radware_verification_page(html, title):
                raise RuntimeError(
                    "The browser is still showing Radware verification. "
                    "No protected-page automation was attempted; complete it manually "
                    "and confirm only after Yad2 listings are visible."
                )

            if listing_count == 0 and require_listings:
                raise RuntimeError(
                    "The confirmed browser page contained no recognizable listing cards. "
                    "The Yad2 markup may have changed, or the search may be empty."
                )

            return html
        finally:
            html_out.unlink(missing_ok=True)
