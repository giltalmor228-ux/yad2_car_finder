"""Tests for telegram/notifier.py"""
from yad2_car_bot.models import TelegramPayload
from yad2_car_bot.telegram import notifier


def test_dry_run_logs_all_images(mocker, caplog):
    payload = TelegramPayload(
        text="hello",
        image_url="https://img.yad2.co.il/a.jpeg",
        extra_image_urls=[
            "https://img.yad2.co.il/b.jpeg",
            "https://img.yad2.co.il/c.jpeg",
        ],
    )
    with caplog.at_level("INFO"):
        assert notifier.send_notification(payload, "t", "c", dry_run=True) is True
    assert "3 image(s)" in caplog.text
    assert "a.jpeg" in caplog.text
    assert "c.jpeg" in caplog.text


def test_single_image_uses_send_photo(mocker):
    post = mocker.patch("yad2_car_bot.telegram.notifier.requests.post")
    post.return_value.raise_for_status = mocker.Mock()

    payload = TelegramPayload(
        text="caption",
        image_url="https://img.yad2.co.il/a.jpeg",
        extra_image_urls=[],
    )
    assert notifier.send_notification(payload, "tok", "42", dry_run=False) is True

    assert post.call_count == 1
    args, kwargs = post.call_args
    assert args[0].endswith("/sendPhoto")
    assert kwargs["data"]["photo"] == "https://img.yad2.co.il/a.jpeg"
    assert kwargs["data"]["caption"] == "caption"


def test_multiple_images_uses_media_group(mocker):
    post = mocker.patch("yad2_car_bot.telegram.notifier.requests.post")
    post.return_value.raise_for_status = mocker.Mock()

    payload = TelegramPayload(
        text="album",
        image_url="https://img.yad2.co.il/a.jpeg",
        extra_image_urls=[
            "https://img.yad2.co.il/b.jpeg",
            "https://img.yad2.co.il/c.jpeg",
        ],
    )
    assert notifier.send_notification(payload, "tok", "42", dry_run=False) is True

    assert post.call_count == 1
    args, kwargs = post.call_args
    assert args[0].endswith("/sendMediaGroup")
    media = __import__("json").loads(kwargs["data"]["media"])
    assert len(media) == 3
    assert media[0]["caption"] == "album"
    assert "caption" not in media[1]
    assert media[2]["media"] == "https://img.yad2.co.il/c.jpeg"


def test_more_than_ten_images_sends_two_albums(mocker):
    post = mocker.patch("yad2_car_bot.telegram.notifier.requests.post")
    post.return_value.raise_for_status = mocker.Mock()

    urls = [f"https://img.yad2.co.il/{i}.jpeg" for i in range(12)]
    payload = TelegramPayload(
        text="many",
        image_url=urls[0],
        extra_image_urls=urls[1:],
    )
    assert notifier.send_notification(payload, "tok", "42", dry_run=False) is True

    assert post.call_count == 2
    first = __import__("json").loads(post.call_args_list[0].kwargs["data"]["media"])
    second = __import__("json").loads(post.call_args_list[1].kwargs["data"]["media"])
    assert len(first) == 10
    assert len(second) == 2
    assert first[0]["caption"] == "many"
    assert "caption" not in second[0]
