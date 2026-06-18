from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path


def save_snapshot(url: str, html: str, snapshot_dir: str = "debug_snapshots") -> Path:
    """Save raw HTML to a timestamped file in *snapshot_dir*.

    Returns the path to the saved file.
    """
    dirpath = Path(snapshot_dir)
    dirpath.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")
    url_slug = re.sub(r"[^\w\-]", "_", url)[:80]
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    filename = f"{ts}_{url_slug}_{url_hash}.html"

    path = dirpath / filename
    path.write_text(html, encoding="utf-8")
    return path
