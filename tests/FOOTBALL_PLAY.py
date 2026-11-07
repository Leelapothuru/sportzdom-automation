import os

import pytest

from pages.football_play_page import FootballPlayPage
from pages.login_page import LoginPage
from utils.football_play_texts import FootballPlayTexts as Texts


OPPONENT_TEAM_SEARCH = "367"
OPPONENT_TEAM_IDENTIFIER = "367"
MATCH_DURATION_MINUTES = "45"
VENUE_SEARCH = "stbc"
VENUE_EXPECTED_LOCATION = "Kalluru, Kurnool"


@pytest.mark.destructive
@pytest.mark.skipif(
    os.environ.get("SPORTZDOM_RUN_FOOTBALL_PLAY_TEST") != "1",
    reason=Texts.PLAY_TEST_OPT_IN_REASON,
)
def test_football_match_can_be_created(driver):
    match_page = FootballPlayPage(driver)
    match_page.activate_app()

    login = LoginPage(driver)
    login_state = login.wait_for_login_state()
    if login_state in ("signin", "signin_entry"):
        login.login()
    elif login_state == "logged_in":
        login.click_home()
    if not login.is_home_page():
        login.wait_for_home_page()

    assert login.is_home_page(), Texts.HOME_PAGE_NOT_DISPLAYED

    match_page.open_play_now_flow()
    match_page.select_gender()

    own_team = match_page.select_team(Texts.YOUR_SIDE)
    assert own_team, Texts.TEAM_SELECTION_FAILED

    opponent_team = match_page.select_team(
        Texts.OPPONENT,
        search_term=OPPONENT_TEAM_SEARCH,
        team_identifier=OPPONENT_TEAM_IDENTIFIER,
    )
    assert OPPONENT_TEAM_IDENTIFIER in opponent_team.casefold(), (
        Texts.TEAM_SELECTION_FAILED
    )

    match_page.select_player_format()
    duration = match_page.set_duration(MATCH_DURATION_MINUTES)
    assert duration == MATCH_DURATION_MINUTES, Texts.DURATION_NOT_ACCEPTED

    venue = match_page.select_venue(VENUE_SEARCH, VENUE_EXPECTED_LOCATION)
    assert VENUE_EXPECTED_LOCATION.casefold() in venue.casefold(), (
        Texts.VENUE_NOT_SELECTED
    )

    assert match_page.submit_match(), Texts.CREATE_MATCH_NOT_CONFIRMED
