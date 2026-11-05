"""End-to-end coverage for Profile drawer > My Stats."""

from pathlib import Path

import pytest

from pages.my_stats_page import MyStatsPage


SCREENSHOTS = Path("screenshots")


def _screenshot(driver, name: str) -> None:
    SCREENSHOTS.mkdir(exist_ok=True)
    driver.save_screenshot(str(SCREENSHOTS / name))


@pytest.mark.integration
def test_my_stats_sports_and_teams_match_counts(driver):
    """Audit current Sports and Teams sections and verify their match counts."""
    my_stats = MyStatsPage(driver)

    my_stats.open()
    _screenshot(driver, "my_stats_matches.png")
    my_stats.select_matches()
    assert my_stats.audit_visible_ui_to_end()
    counts = my_stats.visible_match_counts()
    assert set(counts) == {"Played", "Won", "Lost", "Drawn"}

    my_stats.scroll_to_top()
    my_stats.select_teams()
    _screenshot(driver, "my_stats_teams.png")
    assert my_stats.audit_visible_ui_to_end()
    my_stats.scroll_to_top()
    team_counts = my_stats.visible_match_counts()
    assert set(team_counts) == {"Played", "Won", "Lost", "Drawn"}
