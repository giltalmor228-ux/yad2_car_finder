from __future__ import annotations

import logging
import os
import warnings

import requests
import urllib3

from yad2_car_bot.models import TelegramPayload

# Corporate SSL-inspection proxies replace certs with a self-signed chain.
# Suppress the InsecureRequestWarning that fires when we use verify=False.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
_CAPTION_LIMIT = 1024


def send_notification(
    payload: TelegramPayload,
    token: str,
    chat_id: str,
    dry_run: bool = True,
) -> bool:
    """Send a Telegram notification.

    In dry_run mode: logs to stdout, makes no HTTP calls.
    Returns True on success (or dry-run), False on failure.
    """
    if dry_run:
        logger.info("[DRY RUN] Would send Telegram message:\n%s", payload.text)
        if payload.image_url:
            logger.info("[DRY RUN] With image: %s", payload.image_url)
        return True

    try:
        if payload.image_url:
            try:
                return _send_photo(payload, token, chat_id)
            except Exception as photo_exc:
                logger.warning("sendPhoto failed (%s), falling back to text-only", photo_exc)
                return _send_text(payload.text, token, chat_id)
        else:
            return _send_text(payload.text, token, chat_id)
    except Exception as exc:
        logger.error("Telegram send failed: %s", exc)
        return False


def _send_photo(payload: TelegramPayload, token: str, chat_id: str) -> bool:
    """Send sendPhoto; if caption too long, send photo + separate message."""
    caption = payload.text
    send_separate = False

    if len(caption) > _CAPTION_LIMIT:
        caption = caption[:_CAPTION_LIMIT]
        send_separate = True

    url = _TELEGRAM_API.format(token=token, method="sendPhoto")
    resp = requests.post(
        url,
        data={"chat_id": chat_id, "caption": caption},
        files=None,
        params={"photo": payload.image_url},
        timeout=30,
        verify=False,
    )
    resp.raise_for_status()

    if send_separate:
        _send_text(payload.text, token, chat_id)

    return True


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
