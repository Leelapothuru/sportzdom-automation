"""End-to-end coverage for the Sportzdom Grounds page UI."""

from datetime import datetime
from pathlib import Path

import pytest

from pages.grounds_registration_page import GroundPage


SCREENSHOTS = Path("screenshots")


def _screenshot(driver, name: str) -> None:
    SCREENSHOTS.mkdir(exist_ok=True)
    driver.save_screenshot(str(SCREENSHOTS / name))


@pytest.mark.integration
@pytest.mark.destructive
def test_grounds_page_ui_and_navigation(driver):
    grounds_page = GroundPage(driver)
    _screenshot(driver, "grounds_before_navigation.png")

    grounds_page.navigate_to_grounds_page()
    _screenshot(driver, "grounds_after_navigation.png")

    assert grounds_page.verify_grounds_page_displayed()
    assert grounds_page.verify_all_ui_elements_visible()
    assert grounds_page.verify_all_grounds_are_visible()
    assert grounds_page.verify_navigation_successful()

    grounds_page.open_registration_from_grounds()
    assert grounds_page.verify_registration_page_displayed()

    ground_name = f"Sportzdom Arena {datetime.now():%Y%m%d%H%M%S}"
    assert grounds_page.register_ground(
        ground_name=ground_name,
        state="Andhra Pradesh",
        district="Kurnool",
        city="Kurnool",
        landmark="near petrol bunk",
        description="best grounds",
    )
