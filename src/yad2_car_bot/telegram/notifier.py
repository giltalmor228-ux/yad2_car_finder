from __future__ import annotations

import json
import logging

import requests
import urllib3

from yad2_car_bot.models import TelegramPayload

# Corporate SSL-inspection proxies replace certs with a self-signed chain.
# Suppress the InsecureRequestWarning that fires when we use verify=False.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
_CAPTION_LIMIT = 1024
# Telegram sendMediaGroup allows at most 10 items.
_MAX_MEDIA_GROUP = 10


def send_notification(
    payload: TelegramPayload,
    token: str,
    chat_id: str,
    dry_run: bool = True,
) -> bool:
    """Send a Telegram notification.

    In dry_run mode: logs to stdout, makes no HTTP calls.
    Returns True on success (or dry-run), False on failure.

    When multiple images are present, the first photo carries the caption and
    the rest are sent in the same media album (up to 10 photos).
    """
    image_urls = _collect_image_urls(payload)

    if dry_run:
        logger.info("[DRY RUN] Would send Telegram message:\n%s", payload.text)
        if image_urls:
            logger.info(
                "[DRY RUN] With %d image(s): %s",
                len(image_urls),
                ", ".join(image_urls),
            )
        return True

    try:
        if image_urls:
            try:
                return _send_with_images(payload.text, image_urls, token, chat_id)
            except Exception as photo_exc:
                logger.warning(
                    "image send failed (%s), falling back to text-only", photo_exc
                )
                return _send_text(payload.text, token, chat_id)
        return _send_text(payload.text, token, chat_id)
    except Exception as exc:
        logger.error("Telegram send failed: %s", exc)
        return False


def _collect_image_urls(payload: TelegramPayload) -> list[str]:
    """Ordered unique image URLs: primary first, then extras."""
    urls: list[str] = []
    seen: set[str] = set()
    for url in [payload.image_url, *payload.extra_image_urls]:
        if not url or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def _send_with_images(
    text: str, image_urls: list[str], token: str, chat_id: str
) -> bool:
    """Send one photo or a media album for multiple photos."""
    if len(image_urls) == 1:
        return _send_photo(text, image_urls[0], token, chat_id)

    # First album: up to 10 photos, caption on the first item.
    first_batch = image_urls[:_MAX_MEDIA_GROUP]
    caption = text
    send_separate = False
    if len(caption) > _CAPTION_LIMIT:
        caption = caption[:_CAPTION_LIMIT]
        send_separate = True

    _send_media_group(first_batch, token, chat_id, caption=caption)

    # Remaining photos (11+) in follow-up albums without caption.
    remaining = image_urls[_MAX_MEDIA_GROUP:]
    while remaining:
        batch = remaining[:_MAX_MEDIA_GROUP]
        remaining = remaining[_MAX_MEDIA_GROUP:]
        _send_media_group(batch, token, chat_id, caption=None)

    if send_separate:
        _send_text(text, token, chat_id)

    return True


def _send_photo(text: str, image_url: str, token: str, chat_id: str) -> bool:
    """Send sendPhoto; if caption too long, send photo + separate message."""
    caption = text
    send_separate = False

    if len(caption) > _CAPTION_LIMIT:
        caption = caption[:_CAPTION_LIMIT]
        send_separate = True

    url = _TELEGRAM_API.format(token=token, method="sendPhoto")
    resp = requests.post(
        url,
        data={"chat_id": chat_id, "caption": caption, "photo": image_url},
        timeout=30,
        verify=False,
    )
    resp.raise_for_status()

    if send_separate:
        _send_text(text, token, chat_id)

    return True


def _send_media_group(
    image_urls: list[str],
    token: str,
    chat_id: str,
    caption: str | None,
) -> None:
    """Send a Telegram media album (2–10 photos)."""
    media = []
    for i, image_url in enumerate(image_urls):
        item: dict = {"type": "photo", "media": image_url}
        if i == 0 and caption:
            item["caption"] = caption
        media.append(item)

    url = _TELEGRAM_API.format(token=token, method="sendMediaGroup")
    resp = requests.post(
        url,
        data={"chat_id": chat_id, "media": json.dumps(media)},
        timeout=60,
        verify=False,
    )
    resp.raise_for_status()


def _send_text(text: str, token: str, chat_id: str) -> bool:
    url = _TELEGRAM_API.format(token=token, method="sendMessage")
    resp = requests.post(
        url,
        data={"chat_id": chat_id, "text": text},
        timeout=30,
        verify=False,
    )
    resp.raise_for_status()
    return True
