from __future__ import annotations

import os
from dataclasses import dataclass

from yad2_car_bot.mail.notifier import EmailSettings
from yad2_car_bot.models import TelegramPayload

VALID_CHANNELS = ("telegram", "email")
_CLI_CHOICES = ("telegram", "email", "both")
_DEFAULT_CHANNELS = ("telegram",)


@dataclass(frozen=True)
class NotifyTargets:
    """Resolved notification destinations for a run."""

    channels: tuple[str, ...]
    telegram_token: str = ""
    telegram_chat_id: str = ""
    email: EmailSettings | None = None


def parse_channels(raw: str | None) -> tuple[str, ...]:
    """Parse channel selection.

    Accepts ``telegram``, ``email``, ``both``, or comma-separated
    ``telegram,email``. Empty / unset → telegram only.
    """
    if raw is None or not str(raw).strip():
        return _DEFAULT_CHANNELS

    text = str(raw).strip().lower()
    if text == "both":
        return ("telegram", "email")

    parts = [p.strip().lower() for p in text.split(",")]
    channels: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if not part:
            continue
        if part == "both":
            return ("telegram", "email")
        if part not in VALID_CHANNELS:
            raise ValueError(
                f"Unknown notify channel {part!r}. "
                f"Valid: telegram, email, both"
            )
        if part not in seen:
            seen.add(part)
            channels.append(part)
    if not channels:
        return _DEFAULT_CHANNELS
    return tuple(channels)


def channels_from_cli_or_env(cli_choice: str | None) -> tuple[str, ...]:
    """CLI ``--notify`` wins; otherwise ``NOTIFY_CHANNELS`` env (default telegram)."""
    if cli_choice:
        return parse_channels(cli_choice)
    return parse_channels(os.getenv("NOTIFY_CHANNELS"))


def load_email_settings_from_env() -> EmailSettings | None:
    """Build EmailSettings from env vars, or None if SMTP host is unset."""
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        return None

    to_raw = os.getenv("EMAIL_TO", "").strip()
    to_addrs = tuple(a.strip() for a in to_raw.split(",") if a.strip())
    username = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("SMTP_FROM", "").strip() or username
    port = int(os.getenv("SMTP_PORT", "587") or "587")

    use_ssl_env = os.getenv("SMTP_USE_SSL", "").strip().lower()
    if use_ssl_env in {"1", "true", "yes"}:
        use_ssl = True
    elif use_ssl_env in {"0", "false", "no"}:
        use_ssl = False
    else:
        use_ssl = port == 465

    starttls_env = os.getenv("SMTP_STARTTLS", "").strip().lower()
    if starttls_env in {"1", "true", "yes"}:
        use_starttls = True
    elif starttls_env in {"0", "false", "no"}:
        use_starttls = False
    else:
        use_starttls = not use_ssl

    return EmailSettings(
        host=host,
        port=port,
        username=username,
        password=password,
        from_addr=from_addr,
        to_addrs=to_addrs,
        use_ssl=use_ssl,
        use_starttls=use_starttls,
    )


def validate_notify_targets(targets: NotifyTargets, *, dry_run: bool) -> list[str]:
    """Return human-readable errors if --send targets are incomplete."""
    if dry_run:
        return []
    errors: list[str] = []
    if "telegram" in targets.channels:
        if not targets.telegram_token or not targets.telegram_chat_id:
            errors.append(
                "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set "
                "when notify channel includes telegram."
            )
    if "email" in targets.channels:
        if targets.email is None:
            errors.append("SMTP_HOST must be set when notify channel includes email.")
        else:
            if not targets.email.to_addrs:
                errors.append("EMAIL_TO must be set when notify channel includes email.")
            if not targets.email.from_addr:
                errors.append(
                    "SMTP_FROM or SMTP_USER must be set when notify channel includes email."
                )
            if targets.email.username and not targets.email.password:
                errors.append("SMTP_PASSWORD must be set when SMTP_USER is set.")
    return errors


def send_via_channels(
    payload: TelegramPayload,
    targets: NotifyTargets,
    *,
    subject: str | None = None,
    dry_run: bool = True,
) -> bool:
    """Send on every configured channel. True if at least one channel succeeds."""
    any_ok = False
    if "telegram" in targets.channels:
        from yad2_car_bot.telegram.notifier import send_notification as send_telegram

        ok = send_telegram(
            payload,
            targets.telegram_token,
            targets.telegram_chat_id,
            dry_run=dry_run,
        )
        any_ok = any_ok or ok
    if "email" in targets.channels:
        from yad2_car_bot.mail.notifier import send_notification as send_email

        if targets.email is None and not dry_run:
            ok = False
        else:
            # Dry-run may lack full SMTP settings; still log the would-be email.
            settings = targets.email or EmailSettings(
                host="(unset)",
                port=587,
                username="",
                password="",
                from_addr="(unset)",
                to_addrs=("(unset)",),
            )
            ok = send_email(
                payload,
                settings,
                subject=subject,
                dry_run=dry_run,
            )
        any_ok = any_ok or ok
    return any_ok
