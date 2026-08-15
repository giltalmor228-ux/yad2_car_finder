import json
import subprocess
from pathlib import Path

import pytest

from yad2_car_bot.browser_client import BrowserYad2Client, is_radware_verification_page


def test_detects_radware_by_title():
    assert is_radware_verification_page("<html></html>", "Radware Page")


def test_detects_radware_by_visible_message():
    html = "<body>Verifying your browser before proceeding...</body>"
    assert is_radware_verification_page(html)


def test_normal_yad2_page_is_not_radware():
    html = '<a data-nagish="private-item-link" data-listing-type="private-vehicle">car</a>'
    assert not is_radware_verification_page(html, "רכב פרטי למכירה")


def _completed_process(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["node"], returncode=returncode, stdout=stdout)


def _mock_node_run(html: str, title: str, listing_count: int, returncode: int = 0):
    def _run(cmd, **_kwargs):
        html_out = Path(cmd[cmd.index("--html-out") + 1])
        html_out.write_text(html, encoding="utf-8")
        payload = {
            "title": title,
            "listingCount": listing_count,
            "htmlPath": str(html_out),
        }
        return _completed_process(json.dumps(payload) + "\n", returncode=returncode)

    return _run


def test_get_page_raises_when_node_not_found(mocker):
    mocker.patch("yad2_car_bot.browser_client.shutil.which", return_value=None)

    client = BrowserYad2Client()

    with pytest.raises(RuntimeError, match="Node.js executable"):
        client.get_page("https://www.yad2.co.il/vehicles/cars")


def test_get_page_happy_path_returns_html(mocker, monkeypatch):
    html = '<a data-nagish="private-item-link" data-listing-type="private-vehicle">car</a>'
    monkeypatch.delenv("PLAYWRIGHT_CDP_URL", raising=False)
    monkeypatch.delenv("PLAYWRIGHT_REUSE_TAB", raising=False)
    mocker.patch("yad2_car_bot.browser_client.shutil.which", return_value="/usr/bin/node")
    mocker.patch("yad2_car_bot.browser_client.Path.exists", return_value=True)
    mock_run = mocker.patch(
        "yad2_car_bot.browser_client.subprocess.run",
        side_effect=_mock_node_run(html, "רכב פרטי למכירה", 1),
    )

    client = BrowserYad2Client()
    result = client.get_page("https://www.yad2.co.il/vehicles/cars")

    assert result == html
    assert mock_run.call_count == 1
    launched_cmd = mock_run.call_args.args[0]
    assert "--html-out" in launched_cmd
    assert "--cdp-url" not in launched_cmd


def test_get_page_passes_cdp_url_when_configured(mocker, monkeypatch):
    html = '<a data-nagish="private-item-link" data-listing-type="private-vehicle">car</a>'
    monkeypatch.setenv("PLAYWRIGHT_CDP_URL", "http://127.0.0.1:9222")
    monkeypatch.setenv("PLAYWRIGHT_REUSE_TAB", "true")
    mocker.patch("yad2_car_bot.browser_client.shutil.which", return_value="/usr/bin/node")
    mocker.patch("yad2_car_bot.browser_client.Path.exists", return_value=True)
    mock_run = mocker.patch(
        "yad2_car_bot.browser_client.subprocess.run",
        side_effect=_mock_node_run(html, "רכב פרטי למכירה", 1),
    )

    result = BrowserYad2Client().get_page("https://www.yad2.co.il/vehicles/cars")

    assert result == html
    launched_cmd = mock_run.call_args.args[0]
    assert launched_cmd[launched_cmd.index("--cdp-url") + 1] == "http://127.0.0.1:9222"
    assert "--reuse-tab" in launched_cmd


def test_get_page_raises_on_radware_verification(mocker):
    mocker.patch("yad2_car_bot.browser_client.shutil.which", return_value="/usr/bin/node")
    mocker.patch("yad2_car_bot.browser_client.Path.exists", return_value=True)
    mocker.patch(
        "yad2_car_bot.browser_client.subprocess.run",
        side_effect=_mock_node_run("<html>Radware Page</html>", "Radware Page", 0),
    )

    client = BrowserYad2Client()

    with pytest.raises(RuntimeError, match="Radware verification"):
        client.get_page("https://www.yad2.co.il/vehicles/cars")


def test_get_page_raises_when_no_listings_found(mocker):
    mocker.patch("yad2_car_bot.browser_client.shutil.which", return_value="/usr/bin/node")
    mocker.patch("yad2_car_bot.browser_client.Path.exists", return_value=True)
    mocker.patch(
        "yad2_car_bot.browser_client.subprocess.run",
        side_effect=_mock_node_run(
            "<html><body>empty results</body></html>", "רכב פרטי למכירה", 0
        ),
    )

    client = BrowserYad2Client()

    with pytest.raises(RuntimeError, match="no recognizable listing cards"):
        client.get_page("https://www.yad2.co.il/vehicles/cars")


def test_get_page_raises_on_nonzero_exit_code(mocker):
    mocker.patch("yad2_car_bot.browser_client.shutil.which", return_value="/usr/bin/node")
    mocker.patch("yad2_car_bot.browser_client.Path.exists", return_value=True)
    mocker.patch(
        "yad2_car_bot.browser_client.subprocess.run",
        return_value=_completed_process("", returncode=1),
    )

    client = BrowserYad2Client()

    with pytest.raises(RuntimeError, match="node exited with code"):
        client.get_page("https://www.yad2.co.il/vehicles/cars")
