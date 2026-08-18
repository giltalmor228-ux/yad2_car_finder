"""Tests for mail/notifier.py and notify dispatch helpers."""
from email.message import EmailMessage

import pytest

from yad2_car_bot.mail.notifier import EmailSettings, send_notification
from yad2_car_bot.models import TelegramPayload
from yad2_car_bot.notify import (
    NotifyTargets,
    parse_channels,
    send_via_channels,
    validate_notify_targets,
)


def _settings(**overrides) -> EmailSettings:
    base = dict(
        host="smtp.example.com",
        port=587,
        username="bot@example.com",
        password="secret",
        from_addr="bot@example.com",
        to_addrs=("me@example.com",),
        use_ssl=False,
        use_starttls=True,
    )
    base.update(overrides)
    return EmailSettings(**base)


def test_parse_channels_defaults_to_telegram():
    assert parse_channels(None) == ("telegram",)
    assert parse_channels("") == ("telegram",)
    assert parse_channels("  ") == ("telegram",)


def test_parse_channels_email_and_both():
    assert parse_channels("email") == ("email",)
    assert parse_channels("both") == ("telegram", "email")
    assert parse_channels("telegram,email") == ("telegram", "email")
    assert parse_channels("email, telegram, email") == ("email", "telegram")


def test_parse_channels_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown notify channel"):
        parse_channels("sms")


def test_validate_email_send_requires_to():
    targets = NotifyTargets(
        channels=("email",),
        email=_settings(to_addrs=()),
    )
    errors = validate_notify_targets(targets, dry_run=False)
    assert any("EMAIL_TO" in e for e in errors)


def test_validate_telegram_still_required_when_selected():
    targets = NotifyTargets(channels=("telegram",))
    errors = validate_notify_targets(targets, dry_run=False)
    assert any("TELEGRAM" in e for e in errors)


def test_email_dry_run_logs(mocker, caplog):
    payload = TelegramPayload(
        text="Mazda 3\nscore 80",
        image_url="https://img.yad2.co.il/a.jpeg",
    )
    smtp = mocker.patch("yad2_car_bot.mail.notifier.smtplib.SMTP")
    with caplog.at_level("INFO"):
        assert send_notification(payload, _settings(), dry_run=True) is True
    assert "Would send email" in caplog.text
    assert "Mazda 3" in caplog.text
    smtp.assert_not_called()


def test_email_send_uses_starttls(mocker):
    payload = TelegramPayload(text="hello car", image_url=None)
    smtp_cm = mocker.MagicMock()
    smtp = mocker.patch("yad2_car_bot.mail.notifier.smtplib.SMTP", return_value=smtp_cm)
    smtp_cm.__enter__.return_value = smtp_cm

    assert (
        send_notification(
            payload, _settings(), subject="My subject", dry_run=False
        )
        is True
    )

    smtp.assert_called_once()
    smtp_cm.starttls.assert_called_once()
    smtp_cm.login.assert_called_once_with("bot@example.com", "secret")
    smtp_cm.send_message.assert_called_once()
    msg = smtp_cm.send_message.call_args.args[0]
    assert isinstance(msg, EmailMessage)
    assert msg["Subject"] == "My subject"
    assert msg["To"] == "me@example.com"


def test_send_via_channels_calls_both(mocker):
    payload = TelegramPayload(text="x", image_url=None)
    tg = mocker.patch(
        "yad2_car_bot.telegram.notifier.send_notification", return_value=True
    )
    em = mocker.patch("yad2_car_bot.mail.notifier.send_notification", return_value=True)
    targets = NotifyTargets(
        channels=("telegram", "email"),
        telegram_token="t",
        telegram_chat_id="c",
        email=_settings(),
    )
    assert send_via_channels(payload, targets, dry_run=True) is True
    tg.assert_called_once()
    em.assert_called_once()
