from __future__ import annotations

import os


_LISTING_SELECTOR = 'a[data-nagish="private-item-link"][data-listing-type]'


def is_radware_verification_page(html: str, title: str = "") -> bool:
    """Return True when the response is Radware's browser-verification page."""
    combined = f"{title}\n{html}".lower()
    return (
        "radware page" in combined
        or "verifying your browser before proceeding" in combined
    )


class BrowserYad2Client:
    """User-assisted collector backed by a visible Playwright browser.

    The collector intentionally does not automate browser verification. It opens
    the requested page and waits for the user to complete any required browser
    interaction and confirm that normal search results are visible.
    """

    def __init__(self, browser_channel: str | None = None, timeout_ms: int = 60_000):
        self.browser_channel = browser_channel or os.getenv(
            "PLAYWRIGHT_BROWSER_CHANNEL", "chrome"
        )
        self.timeout_ms = timeout_ms

    def get_page(self, url: str, referer: str | None = None) -> str:
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Run: pip install -r requirements.txt"
            ) from exc

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    channel=self.browser_channel,
                    headless=False,
                )
                context = browser.new_context(locale="he-IL")
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

                print("\nA visible browser window has opened.")
                print("Complete any verification manually and wait for listings to load.")
                input("When the Yad2 results are visible, press Enter here to continue...")

                page.wait_for_timeout(1_000)
                html = page.content()
                title = page.title()
                listing_count = page.locator(_LISTING_SELECTOR).count()
                browser.close()

        except PlaywrightError as exc:
            raise RuntimeError(f"Browser collection failed: {exc}") from exc

        if is_radware_verification_page(html, title):
            raise RuntimeError(
                "The browser is still showing Radware verification. "
                "No protected-page automation was attempted; complete it manually "
                "and confirm only after Yad2 listings are visible."
            )

        if listing_count == 0:
            raise RuntimeError(
                "The confirmed browser page contained no recognizable listing cards. "
                "The Yad2 markup may have changed, or the search may be empty."
            )

        return html
