"""Single Tournament creation: one Knockout and one League tournament per run.

Both tournament types go through exactly the same steps (TournamentCreationFlow);
only the tournament type differs. Each flow walks the wizard forward once,
from Step 1 to Create, without going back to an earlier step, leaving the wizard
or restarting the app. Both flows share one Appium session, so League starts
right after Knockout finishes, and a run saves exactly two tournaments
("Ready to publish"; nothing is published).
Every check is its own test step; negative and boundary checks of each wizard
step are made on the same form before its valid values are entered. If a step
fails, the remaining steps of that flow are skipped.

Only test-account officials are invited (see test_data.tournament_data).
Known open low-severity defects (closing time before opening time, officials
over-count, ground selection accessibility, city/district check) are not
asserted; see reports/manual/ for their status.
"""

from dataclasses import replace
from datetime import date, timedelta

import pytest
from selenium.common.exceptions import InvalidSessionIdException

from pages.tournament_page import TournamentsPage
from test_data.tournament_data import new_tournament, playing_days_between
from utils.driver_setup import get_driver
from utils.helpers import by_label, review_date, rupees

pytestmark = [pytest.mark.tournament, pytest.mark.creation, pytest.mark.incremental]

# Names this feature's reports and screenshot folders (see conftest.py).
FEATURE = "tournament_creation"


@pytest.fixture(scope="module")
def tournaments():
    """One Appium session and page object shared by every step of both flows."""
    session = get_driver()
    page = TournamentsPage(session)
    yield page
    try:
        session.quit()
    except InvalidSessionIdException:
        pass


class TournamentCreationFlow:
    """Every step of creating one tournament; subclasses only choose the type.

    Not collected by itself (the class name does not start with "Test").
    """

    data = None

    # -- entry and Step 1 --------------------------------------------------

    def test_type_dialog_requires_a_tournament_type(self, tournaments):
        # The previous flow ends on the Tournaments screen after "Done".
        tournaments.ensure_main_screen()
        tournaments.open_type_dialog()
        assert not tournaments.is_type_dialog_next_enabled(), "NEXT enabled before choosing a type"

        tournaments.choose_single_tournament()

    def test_empty_basic_details_cannot_be_saved(self, tournaments):
        assert tournaments.attention_count() == 10
        tournaments.save_step()

        assert tournaments.current_step() == 1, "Empty Basic details were saved"
        assert tournaments.attention_count() == 10

    def test_tournament_name_is_limited_to_60_characters(self, tournaments):
        tournaments.enter_name("QA Long Name @#&*()! " + "X" * 130)

        assert len(tournaments.name_value()) == 60
        assert tournaments.is_present(tournaments.NAME_LIMIT_HINT)

    @pytest.mark.parametrize(
        "typed, expected",
        [("-50abc", "50"), ("5099999999999999999999", "509999999")],
        ids=["digits-only", "nine-digit-cap"],
    )
    def test_prize_accepts_only_digits_up_to_nine(self, tournaments, typed, expected):
        tournaments.enter_prize(1, typed)

        assert tournaments.field_text(tournaments.prize_field(1)) == expected

    def test_second_prize_cannot_exceed_first(self, tournaments):
        too_high = replace(self.data, first_prize="500", second_prize=self.data.second_prize)
        tournaments.complete_basic_details(too_high, save=False)
        tournaments.save_step()

        assert tournaments.has_message("Cannot be more than the 1st prize")
        assert tournaments.current_step() == 1

    def test_basic_details_are_saved(self, tournaments):
        # Everything else was filled in by the previous step; correct the 1st prize.
        tournaments.enter_prize(1, self.data.first_prize)
        tournaments.continue_to(2)

    # -- Step 2: Schedule --------------------------------------------------

    def test_empty_schedule_cannot_continue(self, tournaments):
        assert tournaments.attention_count() == 11
        tournaments.save_step()
        assert tournaments.current_step() == 2, "Empty Schedule was accepted"

    def test_start_date_cannot_be_in_the_past(self, tournaments):
        yesterday = date.today() - timedelta(days=1)
        tournaments.open_date_field(tournaments.START_DATE)

        assert tournaments.calendar_day_enabled(date.today())
        if yesterday.month == date.today().month:
            assert not tournaments.calendar_day_enabled(yesterday), "A past start date is selectable"
        tournaments.cancel_date_picker()

    def test_end_date_cannot_be_before_start_date(self, tournaments):
        tournaments.pick_date(tournaments.START_DATE, self.data.start)
        tournaments.open_date_field(tournaments.END_DATE)

        assert tournaments.calendar_day_enabled(self.data.start), "A one-day tournament should be allowed"
        day_before = self.data.start - timedelta(days=1)
        if day_before.month == self.data.start.month:
            assert not tournaments.calendar_day_enabled(day_before), "End date before start is selectable"
        tournaments.cancel_date_picker()

    def test_schedule_accepts_valid_details(self, tournaments):
        tournaments.complete_schedule(self.data, save=False)
        assert tournaments.attention_count() == 0

    @pytest.mark.parametrize(
        "minutes, message",
        [("301", "Match duration can be at most 300 minutes"),
         ("0", "Match duration must be at least 1 minute")],
        ids=["above-maximum", "below-minimum"],
    )
    def test_match_duration_must_be_between_1_and_300(self, tournaments, minutes, message):
        tournaments.fill(tournaments.MATCH_MINUTES, minutes)
        tournaments.save_step()

        assert tournaments.has_message(message)
        assert tournaments.current_step() == 2
        tournaments.fill(tournaments.MATCH_MINUTES, self.data.match_minutes)

    @pytest.mark.parametrize(
        "kind, value, message",
        [("grounds", 51, "At most 50 grounds"), ("referees", 101, "At most 100 referees")],
        ids=["grounds", "referees"],
    )
    def test_official_counts_have_upper_limits(self, tournaments, kind, value, message):
        tournaments.set_count(kind, value)
        tournaments.save_step()

        assert tournaments.has_message(message)
        assert tournaments.current_step() == 2
        tournaments.set_count(kind, getattr(self.data, kind))

    @pytest.mark.parametrize("option", ["Weekends", "Weekdays", "Every day"])
    def test_schedule_summarises_tournament_and_playing_days(self, tournaments, option):
        tournaments.choose("Playing days", option)

        expected = (
            playing_days_between(self.data.start, self.data.end, "Every day"),
            playing_days_between(self.data.start, self.data.end, option),
        )
        assert tournaments.schedule_day_counts() == expected

    def test_schedule_is_saved(self, tournaments):
        tournaments.choose("Playing days", self.data.playing_days)
        tournaments.continue_to(3)

    # -- Step 3: Registration ----------------------------------------------

    def test_registration_window_is_limited_to_before_the_start(self, tournaments):
        tournaments.open_date_field(tournaments.REGISTRATION_OPENS)

        assert tournaments.calendar_day_enabled(self.data.start), "Registration should be able to open on the start date"
        assert not tournaments.calendar_day_enabled(self.data.end), "Registration must not open after the start date"
        tournaments.cancel_date_picker()

    def test_registration_is_saved(self, tournaments):
        tournaments.complete_registration(self.data)

    # -- Step 4: Officials -------------------------------------------------

    def test_official_search_without_match_shows_empty_state(self, tournaments):
        tournaments.open_official_picker("referee")
        tournaments.search_officials("zzqxx")

        assert tournaments.is_present(tournaments.PICKER_NO_MATCH), "No empty state for an unknown referee"
        assert not tournaments.picker_confirm_enabled("referee")
        tournaments.close_official_picker()

    def test_officials_step_requires_grounds(self, tournaments):
        tournaments.add_officials("referee", self.data.referees)
        tournaments.add_officials("scorer", self.data.scorers)
        tournaments.save_step()

        assert tournaments.is_present(tournaments.GROUNDS_REQUIRED), "'Add grounds' prompt not shown"
        assert tournaments.current_step() == 4

    def test_officials_are_saved(self, tournaments):
        tournaments.add_grounds(self.data.state, self.data.grounds)
        tournaments.continue_to(5)

    # -- Steps 5-7 ---------------------------------------------------------

    def test_rules_are_added(self, tournaments):
        tournaments.add_rules(self.data.rules)
        tournaments.continue_to(6)

    def test_empty_expense_shows_validation(self, tournaments):
        tournaments.open_expense_sheet()
        tournaments.submit_expense()

        assert tournaments.is_present(tournaments.EXPENSE_ITEM_REQUIRED)
        assert tournaments.is_present(tournaments.EXPENSE_COST_REQUIRED)

    def test_expense_total_is_quantity_times_cost(self, tournaments):
        tournaments.fill_expense("Balls", "10", "250")
        tournaments.submit_expense()
        tournaments.wait_for(by_label("Balls"))

        assert tournaments.estimated_total() == rupees(2500)
        tournaments.continue_to(7)
        tournaments.continue_to(8)

    # -- Step 8: Review and creation ---------------------------------------

    def test_review_shows_entered_details(self, tournaments):
        data = self.data
        assert tournaments.review_value("Name") == data.name
        assert tournaments.review_value("Type") == data.tournament_type
        prizes = tournaments.review_value("Prizes")
        assert f"1st {rupees(data.first_prize)}" in prizes and f"2nd {rupees(data.second_prize)}" in prizes
        assert tournaments.review_value("Dates") == f"{review_date(data.start)} – {review_date(data.end)}"
        assert tournaments.review_value("Ground hours") == "8:00 AM – 6:00 PM"
        assert tournaments.review_value("Grounds · Referees · Scorers") == (
            f"{data.grounds} · {data.referees} · {data.scorers}"
        )
        assert tournaments.review_value("Entry fee") == rupees(data.entry_fee)
        for code in data.rules:
            assert tournaments.has_message(code), f"Rule {code} missing from Review"

    def test_cancel_keeps_the_user_on_review(self, tournaments):
        tournaments.open_create_dialog()
        tournaments.cancel_create()
        tournaments.wait_for_step(8, timeout=10)
        assert tournaments.is_present(tournaments.CREATE_BUTTON), "Cancel should keep the user on Review"

    def test_create_saves_the_tournament_ready_to_publish(self, tournaments):
        tournaments.open_create_dialog()
        message = tournaments.confirm_create()
        assert "ready to publish" in message, f"Unexpected confirmation: {message!r}"
        tournaments.finish()

        card = tournaments.draft_card(self.data.name)
        assert "Ready to publish" in card, f"Created tournament not listed as ready to publish: {card!r}"


@pytest.mark.smoke
class TestKnockoutTournamentCreation(TournamentCreationFlow):
    data = new_tournament("Knockout")


@pytest.mark.league
class TestLeagueTournamentCreation(TournamentCreationFlow):
    data = new_tournament("League")
