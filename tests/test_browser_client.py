from yad2_car_bot.browser_client import is_radware_verification_page


def test_detects_radware_by_title():
    assert is_radware_verification_page("<html></html>", "Radware Page")


def test_detects_radware_by_visible_message():
    html = "<body>Verifying your browser before proceeding...</body>"
    assert is_radware_verification_page(html)


def test_normal_yad2_page_is_not_radware():
    html = '<a data-nagish="private-item-link" data-listing-type="private-vehicle">car</a>'
    assert not is_radware_verification_page(html, "רכב פרטי למכירה")
