from __future__ import annotations

import logging
import random
import time
from typing import Optional

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from yad2_car_bot.debug.snapshots import save_snapshot

logger = logging.getLogger(__name__)

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
}


class Yad2Client:
    """Polite HTTP client for fetching Yad2 public pages.

    - Respects Retry-After on 429 / 503
    - Exponential backoff with jitter between retries
    - Saves raw HTML snapshots in debug mode
    - Sends browser-like headers to reduce bot detection
    """

    def __init__(
        self,
        timeout: int = 15,
        user_agent: Optional[str] = None,
        max_retries: int = 3,
        debug_mode: bool = False,
        snapshot_dir: str = "debug_snapshots",
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.debug_mode = debug_mode
        self.snapshot_dir = snapshot_dir

        self.session = requests.Session()
        self.session.headers.update(_BROWSER_HEADERS)
        self.session.headers.update(
            {"User-Agent": user_agent or _DEFAULT_USER_AGENT}
        )

    def get_page(self, url: str, referer: Optional[str] = None) -> str:
        """Fetch a public URL and return HTML text.

        Retries up to *max_retries* times with exponential backoff + jitter.
        Honors Retry-After on 429/503.
        Pass *referer* to set the Referer header (e.g. the search page URL when
        fetching a detail page).
        """
        last_exc: Optional[Exception] = None
        extra_headers = {"Referer": referer} if referer else {}

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, headers=extra_headers)

                if response.status_code in (429, 503):
                    retry_after = float(
                        response.headers.get("Retry-After", 60 * (attempt + 1))
                    )
                    jitter = random.uniform(0, 5)
                    wait = retry_after + jitter
                    logger.warning(
                        "Rate limited (%s). Waiting %.1fs before retry %d/%d.",
                        response.status_code,
                        wait,
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                html = response.text

                if self.debug_mode:
                    save_snapshot(url, html, snapshot_dir=self.snapshot_dir)

                return html

            except requests.RequestException as exc:
                last_exc = exc
                if attempt < self.max_retries - 1:
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        "Request failed (%s). Retry %d/%d in %.1fs.",
                        exc,
                        attempt + 1,
                        self.max_retries,
                        backoff,
                    )
                    time.sleep(backoff)

        raise RuntimeError(
            f"Failed to fetch {url!r} after {self.max_retries} attempts: {last_exc}"
        )
