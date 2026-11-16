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
    """Audit Sports, Teams, badge certificates, and the signed-in profile summary."""
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

    my_stats.select_badges()
    _screenshot(driver, "my_stats_badges.png")
    profile_name = my_stats.assert_profile_header_and_stats_visible()
    my_stats.assert_all_badges_displayed()
    my_stats.scroll_to_top()

    expected_sport, expected_date = my_stats.open_first_match_badge()
    my_stats.open_first_certificate()
    _screenshot(driver, "my_stats_certificate.png")
    my_stats.assert_certificate_details(profile_name, expected_sport, expected_date)
    my_stats.close_certificate()
