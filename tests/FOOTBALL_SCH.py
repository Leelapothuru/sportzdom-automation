import os
from datetime import datetime, timedelta

import pytest

from pages.football_sch_page import FootballSchedulePage
from pages.login_page import LoginPage
from utils.football_sch_texts import FootballScheduleTexts as Texts


OPPONENT_TEAM_SEARCH = "367"
OPPONENT_TEAM_IDENTIFIER = "367"
MATCH_DURATION_MINUTES = "45"
VENUE_SEARCH = "stbc"
VENUE_EXPECTED_LOCATION = "Kalluru, Kurnool"
REFEREE_SEARCH = "380"
REFEREE_USER_IDENTIFIER = "user380"
SCORER_SEARCH = "405"
SCORER_USER_IDENTIFIER = "user405"


@pytest.mark.destructive
@pytest.mark.skipif(
    os.environ.get("SPORTZDOM_RUN_FOOTBALL_SCH_TEST") != "1",
    reason=Texts.TEST_OPT_IN_REASON,
)
def test_football_match_can_be_scheduled(driver):
    login = LoginPage(driver)
    login_state = login.wait_for_login_state()
    if login_state in ("signin", "signin_entry"):
        login.login()
    elif login_state == "logged_in":
        login.click_home()
    if not login.is_home_page():
        login.wait_for_home_page()

    assert login.is_home_page(), Texts.HOME_PAGE_NOT_DISPLAYED

    match_page = FootballSchedulePage(driver)
    match_page.open_schedule_match_flow()
    match_page.select_gender()

    own_team = match_page.select_team(Texts.YOUR_SIDE)
    assert own_team, Texts.TEAM_SELECTION_NOT_CONFIRMED

    opponent_team = match_page.select_team(
        Texts.OPPONENT,
        search_term=OPPONENT_TEAM_SEARCH,
        team_identifier=OPPONENT_TEAM_IDENTIFIER,
    )
    assert OPPONENT_TEAM_IDENTIFIER in opponent_team.casefold(), (
        Texts.TEAM_SELECTION_NOT_CONFIRMED
    )

    match_page.select_player_format()
    duration = match_page.set_duration(MATCH_DURATION_MINUTES)
    assert duration == MATCH_DURATION_MINUTES, Texts.DURATION_NOT_ACCEPTED

    now = datetime.now().astimezone()
    match_start = now + timedelta(minutes=30)
    if match_start.second or match_start.microsecond:
        match_start = (match_start + timedelta(minutes=1)).replace(
            second=0,
            microsecond=0,
        )
    actual_hour, actual_minute, expected_hour, period_selected = (
        match_page.set_match_start(match_start)
    )
    assert actual_hour == expected_hour and actual_minute == match_start.strftime("%M"), (
        Texts.MATCH_START_NOT_ACCEPTED
    )
    assert period_selected, Texts.MATCH_START_NOT_ACCEPTED

    venue = match_page.select_venue(VENUE_SEARCH, VENUE_EXPECTED_LOCATION)
    assert VENUE_EXPECTED_LOCATION.casefold() in venue.casefold(), (
        Texts.VENUE_NOT_SELECTED
    )

    referee = match_page.select_official(
        Texts.REFEREE,
        REFEREE_SEARCH,
        REFEREE_USER_IDENTIFIER,
    )
    assert REFEREE_USER_IDENTIFIER in referee, Texts.REFEREE_NOT_SELECTED

    scorer = match_page.select_official(
        Texts.SCORER,
        SCORER_SEARCH,
        SCORER_USER_IDENTIFIER,
    )
    assert SCORER_USER_IDENTIFIER in scorer, Texts.SCORER_NOT_SELECTED

    assert match_page.submit_schedule(), Texts.SCHEDULE_CONFIRMATION_NOT_DISMISSED
