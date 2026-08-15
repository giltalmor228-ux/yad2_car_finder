from click.testing import CliRunner

from yad2_car_bot.cli import cli


HTML = '<a data-nagish="private-item-link" data-listing-type="private-vehicle">car</a>'


def test_collect_http_writes_out_file(tmp_path, mocker):
    mocker.patch("yad2_car_bot.cli._make_page_client").return_value.get_page.return_value = HTML
    out = tmp_path / "search.html"

    result = CliRunner().invoke(cli, ["collect", "--http", "--out", str(out)])

    assert result.exit_code == 0, result.output
    assert out.read_text(encoding="utf-8") == HTML
    assert "saved" in result.output.lower()
    assert "recognized listing cards:" in result.output.lower()
    assert "[HTTP]" in result.output


def test_collect_browser_writes_out_file(tmp_path, mocker):
    factory = mocker.patch("yad2_car_bot.cli._make_page_client")
    factory.return_value.get_page.return_value = HTML
    out = tmp_path / "search.html"

    result = CliRunner().invoke(cli, ["collect", "--browser", "--out", str(out)])

    assert result.exit_code == 0, result.output
    factory.assert_called_once_with(True)
    assert out.read_text(encoding="utf-8") == HTML
    assert "[BROWSER]" in result.output


def test_collect_two_search_groups_writes_two_files(tmp_path, mocker, app_config):
    mocker.patch("yad2_car_bot.cli._make_page_client").return_value.get_page.return_value = HTML
    mocker.patch("yad2_car_bot.cli.time.sleep")

    # Force two URLs without mutating the on-disk profile permanently.
    mocker.patch(
        "yad2_car_bot.url_builder.build_search_urls",
        return_value=[
            "https://www.yad2.co.il/vehicles/cars?model=1",
            "https://www.yad2.co.il/vehicles/cars?model=2",
        ],
    )
    out = tmp_path / "search.html"

    result = CliRunner().invoke(cli, ["collect", "--http", "--out", str(out)])

    assert result.exit_code == 0, result.output
    assert out.exists()
    assert (tmp_path / "search-2.html").exists()
    assert "group 1/2" in result.output.lower()
    assert "group 2/2" in result.output.lower()


def test_collect_exits_nonzero_on_radware_page(tmp_path, mocker):
    mocker.patch("yad2_car_bot.cli._make_page_client").return_value.get_page.return_value = (
        "<title>Radware Page</title><body>Verifying your browser before proceeding...</body>"
    )
    out = tmp_path / "search.html"

    result = CliRunner().invoke(cli, ["collect", "--http", "--out", str(out)])

    assert result.exit_code == 1
    assert "Radware" in result.output
    assert not out.exists()


def test_collect_exits_nonzero_on_fetch_failure(tmp_path, mocker):
    mocker.patch("yad2_car_bot.cli._make_page_client").return_value.get_page.side_effect = RuntimeError(
        "blocked"
    )
    out = tmp_path / "search.html"

    result = CliRunner().invoke(cli, ["collect", "--out", str(out)])

    assert result.exit_code == 1
    assert "Failed to fetch search page" in result.output
    assert not out.exists()
