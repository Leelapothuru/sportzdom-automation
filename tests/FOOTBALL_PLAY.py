import pytest  #login as 117

from pages.football_play_page import FootballPlayPage
from utils.football_play_texts import FootballPlayTexts as Texts


OPPONENT_TEAM_SEARCH = "367"
OPPONENT_TEAM_IDENTIFIER = "367"
MATCH_DURATION_MINUTES = "45"
VENUE_SEARCH = "stbc"
VENUE_EXPECTED_LOCATION = "Kalluru, Kurnool"


@pytest.mark.destructive
def test_football_match_can_be_created(driver):
    match_page = FootballPlayPage(driver)
    match_page.activate_app()
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

    assert match_page.submit_match(), Texts.MATCH_CONFIRMATION_NOT_DISMISSED
