"""Appium smoke test for the live single-tournament wizard."""

from pathlib import Path
import time

from drivers.driver_manager import get_driver
from pages.tournaments_page import TournamentsPage


SCREENSHOTS = Path("screenshots/tournaments")


def capture(driver, filename):
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    driver.save_screenshot(str(SCREENSHOTS / filename))


def test_start_single_tournament_wizard():
    driver = get_driver()
    tournaments = TournamentsPage(driver)
    try:
        capture(driver, "01_home.png")
        tournaments.click_tournaments_nav()
        capture(driver, "02_tournaments.png")
        tournaments.click_here_button()
        capture(driver, "03_create_type.png")
        tournaments.select_single_tournament()
        tournaments.click_modal_next()
        capture(driver, "04_basic_empty.png")
        tournaments.complete_current_basic_details(
            name=f"Appium Mobile Test {int(time.time())}",
            state="Andhra Pradesh",
            district="Anantapur",
            city="Kurnool",
        )
        capture(driver, "05_schedule.png")
    finally:
        driver.quit()
