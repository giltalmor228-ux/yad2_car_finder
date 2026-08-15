import json
import subprocess

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


def test_get_page_raises_when_node_not_found(mocker):
    mocker.patch("yad2_car_bot.browser_client.shutil.which", return_value=None)

    client = BrowserYad2Client()

    with pytest.raises(RuntimeError, match="Node.js executable"):
        client.get_page("https://www.yad2.co.il/vehicles/cars")


def test_get_page_happy_path_returns_html(mocker):
    payload = {
        "html": '<a data-nagish="private-item-link" data-listing-type="private-vehicle">car</a>',
        "title": "רכב פרטי למכירה",
        "listingCount": 1,
    }
    mocker.patch("yad2_car_bot.browser_client.shutil.which", return_value="/usr/bin/node")
    mocker.patch(
        "yad2_car_bot.browser_client.Path.exists",
        return_value=True,
    )
    mock_run = mocker.patch(
        "yad2_car_bot.browser_client.subprocess.run",
        return_value=_completed_process(json.dumps(payload) + "\n"),
    )

    client = BrowserYad2Client()
    html = client.get_page("https://www.yad2.co.il/vehicles/cars")

    assert html == payload["html"]
    assert mock_run.call_count == 1
    launched_cmd = mock_run.call_args.args[0]
    assert "--cdp-url" not in launched_cmd


def test_get_page_passes_cdp_url_when_configured(mocker, monkeypatch):
    payload = {
        "html": '<a data-nagish="private-item-link" data-listing-type="private-vehicle">car</a>',
        "title": "רכב פרטי למכירה",
        "listingCount": 1,
    }
    monkeypatch.setenv("PLAYWRIGHT_CDP_URL", "http://127.0.0.1:9222")
    monkeypatch.setenv("PLAYWRIGHT_REUSE_TAB", "true")
    mocker.patch("yad2_car_bot.browser_client.shutil.which", return_value="/usr/bin/node")
    mocker.patch("yad2_car_bot.browser_client.Path.exists", return_value=True)
    mock_run = mocker.patch(
        "yad2_car_bot.browser_client.subprocess.run",
        return_value=_completed_process(json.dumps(payload) + "\n"),
    )

    html = BrowserYad2Client().get_page("https://www.yad2.co.il/vehicles/cars")

    assert html == payload["html"]
    launched_cmd = mock_run.call_args.args[0]
    assert launched_cmd[launched_cmd.index("--cdp-url") + 1] == "http://127.0.0.1:9222"
    assert "--reuse-tab" in launched_cmd


def test_get_page_raises_on_radware_verification(mocker):
    payload = {
        "html": "<html>Radware Page</html>",
        "title": "Radware Page",
        "listingCount": 0,
    }
    mocker.patch("yad2_car_bot.browser_client.shutil.which", return_value="/usr/bin/node")
    mocker.patch("yad2_car_bot.browser_client.Path.exists", return_value=True)
    mocker.patch(
        "yad2_car_bot.browser_client.subprocess.run",
        return_value=_completed_process(json.dumps(payload) + "\n"),
    )

    client = BrowserYad2Client()

    with pytest.raises(RuntimeError, match="Radware verification"):
        client.get_page("https://www.yad2.co.il/vehicles/cars")


def test_get_page_raises_when_no_listings_found(mocker):
    payload = {
        "html": "<html><body>empty results</body></html>",
        "title": "רכב פרטי למכירה",
        "listingCount": 0,
    }
    mocker.patch("yad2_car_bot.browser_client.shutil.which", return_value="/usr/bin/node")
    mocker.patch("yad2_car_bot.browser_client.Path.exists", return_value=True)
    mocker.patch(
        "yad2_car_bot.browser_client.subprocess.run",
        return_value=_completed_process(json.dumps(payload) + "\n"),
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
