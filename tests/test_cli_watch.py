"""Tests for watch / pipeline notify modes."""
from click.testing import CliRunner

from yad2_car_bot.cli import cli
from yad2_car_bot.notify import NotifyTargets


def _notify_targets() -> NotifyTargets:
    return NotifyTargets(
        channels=("telegram",),
        telegram_token="token",
        telegram_chat_id="chat",
    )


def test_watch_seed_then_new_only(tmp_path, mocker, app_config):
    calls: list[str] = []

    def fake_pipeline(**kwargs):
        calls.append(kwargs["notify_mode"])
        return {
            "cards": 2,
            "new": 2 if kwargs["notify_mode"] == "none" else 0,
            "notified": 0,
        }

    mocker.patch(
        "yad2_car_bot.cli._prepare_run",
        return_value=(
            app_config,
            mocker.Mock(),
            ["https://www.yad2.co.il/vehicles/cars?manufacturer=17"],
            str(tmp_path / "watch.sqlite"),
            _notify_targets(),
        ),
    )
    mocker.patch("yad2_car_bot.cli._run_pipeline", side_effect=fake_pipeline)
    # First sleep after baseline OK; second sleep stops the loop.
    sleep = mocker.patch(
        "yad2_car_bot.cli.time.sleep", side_effect=[None, KeyboardInterrupt]
    )

    result = CliRunner().invoke(
        cli,
        ["watch", "--http", "--dry-run", "--interval-minutes", "15", "--seed-first"],
    )

    assert result.exit_code == 0, result.output
    assert calls == ["none", "new_only"]
    assert sleep.call_count == 2
    assert sleep.call_args_list[0].args[0] == 15 * 60
    assert "baseline" in result.output.lower() or "seed" in result.output.lower()
    assert "[WATCH] Stopped." in result.output


def test_watch_default_notifies_new_on_first_cycle(tmp_path, mocker, app_config):
    calls: list[str] = []

    def pipeline(**kwargs):
        calls.append(kwargs["notify_mode"])
        return {"cards": 1, "new": 1, "notified": 1}

    mocker.patch(
        "yad2_car_bot.cli._prepare_run",
        return_value=(
            app_config,
            mocker.Mock(),
            ["https://example.com"],
            str(tmp_path / "watch.sqlite"),
            _notify_targets(),
        ),
    )
    mocker.patch("yad2_car_bot.cli._run_pipeline", side_effect=pipeline)
    mocker.patch("yad2_car_bot.cli.time.sleep", side_effect=KeyboardInterrupt)

    result = CliRunner().invoke(
        cli,
        ["watch", "--http", "--dry-run", "--interval-minutes", "1"],
    )

    assert result.exit_code == 0, result.output
    assert calls == ["new_only"]
    assert "new-to-db" in result.output.lower() or "new listings only" in result.output.lower()


def test_run_pipeline_new_only_skips_known(tmp_path, mocker, app_config, search_card_html):
    from yad2_car_bot.cli import _run_pipeline
    from yad2_car_bot.storage.sqlite_store import SQLiteStore

    client = mocker.Mock()
    client.get_page.return_value = search_card_html
    mocker.patch("yad2_car_bot.notify.send_via_channels", return_value=True)
    mocker.patch("yad2_car_bot.cli.time.sleep")

    db = tmp_path / "pipe.sqlite"
    urls = ["https://www.yad2.co.il/vehicles/cars?x=1"]
    targets = _notify_targets()

    with SQLiteStore(db) as store:
        seed = _run_pipeline(
            cfg=app_config,
            client=client,
            store=store,
            search_urls=urls,
            notify_targets=targets,
            dry_run=True,
            notify_mode="none",
        )
        assert seed["cards"] == 1
        assert seed["new"] == 1
        assert seed["notified"] == 0

        again = _run_pipeline(
            cfg=app_config,
            client=client,
            store=store,
            search_urls=urls,
            notify_targets=targets,
            dry_run=True,
            notify_mode="new_only",
        )
        assert again["cards"] == 1
        assert again["new"] == 0
        assert again["notified"] == 0
