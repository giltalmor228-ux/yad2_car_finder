from __future__ import annotations

import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from html import escape

from yad2_car_bot.models import TelegramPayload

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailSettings:
    host: str
    port: int
    username: str
    password: str
    from_addr: str
    to_addrs: tuple[str, ...]
    use_ssl: bool = False
    use_starttls: bool = True


def send_notification(
    payload: TelegramPayload,
    settings: EmailSettings,
    *,
    subject: str | None = None,
    dry_run: bool = True,
) -> bool:
    """Send an email notification using the same rendered listing text as Telegram.

    In dry_run mode: logs to stdout, makes no SMTP calls.
    Returns True on success (or dry-run), False on failure.
    """
    image_urls = _collect_image_urls(payload)
    mail_subject = (subject or _default_subject(payload.text)).strip() or "Yad2 car listing"
    plain = payload.text
    html = _build_html(plain, image_urls)

    if dry_run:
        logger.info(
            "[DRY RUN] Would send email to %s\nSubject: %s\n%s",
            ", ".join(settings.to_addrs),
            mail_subject,
            plain,
        )
        if image_urls:
            logger.info(
                "[DRY RUN] With %d image link(s): %s",
                len(image_urls),
                ", ".join(image_urls),
            )
        return True

    msg = EmailMessage()
    msg["Subject"] = mail_subject
    msg["From"] = settings.from_addr
    msg["To"] = ", ".join(settings.to_addrs)
    msg.set_content(plain)
    msg.add_alternative(html, subtype="html")

    try:
        _smtp_send(msg, settings)
        return True
    except Exception as exc:
        logger.error("Email send failed: %s", exc)
        return False


def _collect_image_urls(payload: TelegramPayload) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for url in [payload.image_url, *payload.extra_image_urls]:
        if not url or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def _default_subject(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:120]
    return "Yad2 car listing"


def _build_html(plain: str, image_urls: list[str]) -> str:
    body = escape(plain).replace("\n", "<br>\n")
    images = ""
    if image_urls:
        imgs = "\n".join(
            f'<p><img src="{escape(url, quote=True)}" '
            f'alt="listing photo" style="max-width:100%;height:auto;"></p>'
            for url in image_urls[:10]
        )
        images = f"<hr>\n{imgs}"
    return (
        "<!DOCTYPE html><html><body>"
        f"<div style=\"font-family:sans-serif;white-space:normal;\">{body}</div>"
        f"{images}"
        "</body></html>"
    )


def _smtp_send(msg: EmailMessage, settings: EmailSettings) -> None:
    context = ssl.create_default_context()
    if settings.use_ssl:
        with smtplib.SMTP_SSL(
            settings.host, settings.port, context=context, timeout=30
        ) as smtp:
            if settings.username:
                smtp.login(settings.username, settings.password)
            smtp.send_message(msg)
        return

    with smtplib.SMTP(settings.host, settings.port, timeout=30) as smtp:
        smtp.ehlo()
        if settings.use_starttls:
            smtp.starttls(context=context)
            smtp.ehlo()
        if settings.username:
            smtp.login(settings.username, settings.password)
        smtp.send_message(msg)
