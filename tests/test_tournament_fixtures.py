"""Tournament fixtures: the organizer groups the players, adds stages and
creates every fixture. (Confirm Fixtures is being removed from the app, so it
is not tested; 12 Nov 2026.)

Dynamic: everything is worked out from the tournament at run time
(utils/fixture_planner.py):
  * players registered: the "N/M" count on the details page;
  * groups: the app's own Auto-split proposal, then each group's members;
  * stages: League plus knockout stages for the number of qualifiers
    (2 -> Final; 4 -> Semi Final, Third Place, Final; 8 -> adds Quarter Final);
  * League: every pair in a group meets once; knockouts use the app's TBD
    positions ("Group A · 1st", "Winner of Semi Final · Match 13");
  * schedule: from the tournament's first day (never today or earlier), as in
    the manual run: Group A from 9 AM, Group B from 4 PM, one hour apart,
    knockout rounds two days apart; it must fit before the tournament ends.

Sign-in (utils/session.py, shared with the registration flow): the first step
checks the app. Signed out -> the organizer account signs in; signed in as an
organizer of the tournament (profile name listed under Organizers on its
Overview tab) -> that session is kept; signed in as anyone else -> logged out
first. Any later step that finds the app signed out signs the organizer in again.

Settings (first match wins): pytest options --tournament / --organizer,
environment or pipeline variables SPORTZDOM_FIXTURES_TOURNAMENT /
SPORTZDOM_FIXTURES_ORGANIZER, then test_data/tournament_data.json "fixtures".
Tests marked known_defect assert the correct behaviour for defects found in the
manual run (reports/manual/tournament_fixtures_manual_tests.md) and fail until
they are fixed; skip them with --skip-defect-tests or SPORTZDOM_SKIP_DEFECT_TESTS=true.

Data: the run creates real fixtures. Reset the tournament
(groups emptied, stages and fixtures deleted in Supabase) before every run;
the pre-check stops the run when fixtures already exist and never deletes anything.

Run: pytest -m fixtures   (or pytest tests/test_tournament_fixtures.py)
"""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

import pytest
from selenium.common.exceptions import WebDriverException

from pages.login_page import LoginPage
from pages.logout_page import LogoutPage
from pages.tournament_fixtures_page import TournamentFixturesPage
from test_data.tournament_data import account_credentials, fixtures_data
from utils import session
from utils.driver_setup import get_driver
from utils.fixture_planner import (
    LEAGUE,
    ScheduleSettings,
    first_playable_day,
    plan_fixtures,
    tournament_dates,
)

log = logging.getLogger(__name__)

FEATURE = "tournament_fixtures"

pytestmark = [
    pytest.mark.fixtures,
    pytest.mark.skipif(
        account_credentials(1) is None,
        reason="Set SPORTZDOM_PLAYER_EMAIL_TEMPLATE and SPORTZDOM_PLAYER_PASSWORD_TEMPLATE to run fixtures tests.",
    ),
]


# -- shared state --------------------------------------------------------------


class App:
    """Page objects on one Appium session, which can be replaced if it crashes."""

    def __init__(self):
        self._start()

    def _start(self):
        session = get_driver()
        self.login = LoginPage(session)
        self.logout = LogoutPage(session)
        self.fixtures = TournamentFixturesPage(session)

    @property
    def driver(self):
        # Lets conftest.py find the session for step screenshots.
        return self.fixtures.driver

    def ensure_alive(self):
        try:
            self.driver.current_package
        except WebDriverException as error:
            log.warning("Appium session lost (%s); starting a new one", error.msg)
            self.quit()
            self._start()

    def quit(self):
        try:
            self.driver.quit()
        except WebDriverException:
            pass


@dataclass
class Run:
    """What the flow has learnt so far, shared by the tests in order."""

    data: object
    organizers: list = field(default_factory=list)  # profile names, from the Overview tab
    signed_in_as: str | None = None
    registered: int | None = None
    first_day: date | None = None
    last_day: date | None = None
    groups: dict = field(default_factory=dict)       # {"Group A": [names]}
    qualifiers: dict = field(default_factory=dict)   # {"Group A": 2}
    plan: object = None
    stages_ready: bool = False
    league_created: int = 0
    knockout_created: int = 0
    league_done: bool = False      # every planned League fixture created
    knockout_done: bool = False    # every planned knockout fixture created

    def need(self, attribute, reason):
        if not getattr(self, attribute):
            pytest.skip(f"Needs an earlier step: {reason}")


@pytest.fixture(scope="module")
def app_session():
    app = App()
    yield app
    app.quit()


@pytest.fixture
def app(app_session):
    app_session.ensure_alive()
    return app_session


@pytest.fixture(scope="module")
def run(pytestconfig):
    data = fixtures_data(pytestconfig.getoption("--tournament"), pytestconfig.getoption("--organizer"))
    log.info("Fixtures for %r, organizer user%s", data.tournament, data.organizer_account)
    return Run(data=data)


def schedule_settings(data):
    return ScheduleSettings(
        league_group_start_times=data.league_group_start_times,
        minutes_between_matches=data.minutes_between_matches,
        knockout_gap_days=data.knockout_gap_days,
        knockout_start_time=data.knockout_start_time,
        third_place_time=data.third_place_time,
        final_time=data.final_time,
    )


def tournament_organizers(app, run):
    """Profile names listed under Organizers on the tournament's Overview tab."""
    app.fixtures.open_tournament(run.data.tournament)
    organizers = app.fixtures.officials().get("Organizers", [])
    log.info("Organizers of %s: %s", run.data.tournament, organizers)
    return organizers


def ensure_signed_in_as_organizer(app, run):
    """Make sure the app is signed in as an organizer of the tournament.

    Signed out: sign in with the configured organizer account. Signed in as an
    organizer: keep that session. Signed in as anyone else: log out first.
    Returns the signed-in profile name.
    """
    number = run.data.organizer_account

    def is_organizer(name):
        run.organizers = tournament_organizers(app, run)
        return name in run.organizers

    name = session.sign_in_as(app.login, app.logout, number, accept=is_organizer)
    if name not in run.organizers:  # signed in just now: check the role
        run.organizers = tournament_organizers(app, run)
    assert name in run.organizers, (
        f"user{number} ({name}) is not an organizer of {run.data.tournament!r}; organizers: {run.organizers}. "
        "Set --organizer / SPORTZDOM_FIXTURES_ORGANIZER to an organizer's account number"
    )
    run.signed_in_as = name
    return name


def open_matches(app, run):
    """The Matches tab of the tournament, opened from wherever the app is.

    If the app has been signed out (or the session was restarted onto the
    sign-in screen), the organizer is signed in again first.
    """
    page = app.fixtures
    if page.is_present(page.MATCHES_TAB) and page.is_present(page.SETUP_CARD):
        return page
    if page.is_present(page.DETAILS_TITLE) and page.is_present(page.MATCHES_TAB):
        # On the details page, another tab (e.g. Overview) selected
        page.open_matches_tab()
        return page
    if app.login.app_state(timeout=2) == "signed_out":
        log.warning("The app is signed out; signing the organizer in again")
        ensure_signed_in_as_organizer(app, run)
    elif page.is_present(page.BACK) or page.is_present(page.FORM_TITLE):
        # Groups & stages or the fixture form
        page.back_to_matches_tab()
        return page
    page.open_tournament(run.data.tournament)
    page.open_matches_tab()
    return page


def leave_form(page):
    """Back out of the manual form to the Matches tab without creating anything."""
    for locator in (page.CANCEL_SELECTION, page.DIALOG_CANCEL):
        if page.is_present(locator):
            page.click(locator)
    page.back_to_matches_tab()


# -- 1. Setup: organizer, players, groups and stages ---------------------------


@pytest.mark.incremental
class TestSetup:
    def test_organizer_is_signed_in(self, app, run):
        name = ensure_signed_in_as_organizer(app, run)

        assert app.login.is_signed_in() or app.fixtures.is_present(app.fixtures.DETAILS_TITLE), "Not signed in"
        assert name in run.organizers, f"{name} is not an organizer of {run.data.tournament!r}"

    def test_reads_registered_players_and_dates(self, app, run):
        page = app.fixtures
        if not page.is_present(page.DETAILS_TITLE):
            page.open_tournament(run.data.tournament)
        registered, capacity = page.player_count()
        start, end = tournament_dates(page.tournament_dates_text())
        log.info("%s: %s/%s players, %s - %s", run.data.tournament, registered, capacity, start, end)

        assert registered >= 2, f"Only {registered} player(s) registered; fixtures need at least 2"
        run.registered = registered
        run.first_day = first_playable_day(start, date.today())
        run.last_day = end
        assert run.first_day <= end, f"The tournament ended on {end}; no day is left for fixtures"

    def test_no_fixtures_or_stages_yet(self, app, run):
        page = open_matches(app, run)
        scheduled = page.scheduled_count()
        assert scheduled == 0, (
            f"{run.data.tournament} already has {scheduled} fixture(s); reset it in Supabase "
            "(delete stages and fixtures, empty the groups) before running this flow"
        )
        page.open_groups_and_stages()
        stages = page.stages_listed()
        page.back_to_matches_tab()
        assert not stages, f"Stages already exist ({stages}); reset the tournament in Supabase first"

    def test_auto_split_puts_every_player_in_one_group(self, app, run):
        page = open_matches(app, run)
        page.open_groups_and_stages()
        teams, group_count = page.auto_split()

        assert teams == run.registered, f"Auto-split counts {teams} teams, but {run.registered} are registered"
        assert "Every team is in a group" in page.unassigned_message(), page.unassigned_message()
        cards = page.group_cards()
        assert len(cards) == group_count, f"Auto-split promised {group_count} groups, cards show {list(cards)}"

        for group, (size, qualifiers) in cards.items():
            members = page.group_members(group)
            assert len(members) == size, f"{group} card says {size} teams, its list shows {members}"
            run.groups[group] = members
            run.qualifiers[group] = qualifiers
        everyone = [name for names in run.groups.values() for name in names]
        assert len(everyone) == len(set(everyone)) == run.registered, (
            f"Players are missing or in more than one group: {run.groups}"
        )
        log.info("Groups: %s; qualifiers: %s", run.groups, run.qualifiers)

    def test_plan_fits_the_tournament(self, run):
        run.plan = plan_fixtures(run.groups, run.qualifiers, run.first_day, run.last_day,
                                 schedule_settings(run.data))
        log.info("Planned %s fixtures, stages %s:", run.plan.total, run.plan.stages)
        for fixture in run.plan.fixtures:
            log.info("  %s", fixture)

    def test_adds_stages(self, app, run):
        page = app.fixtures
        page.add_stages(list(run.plan.stages))

        assert page.stages_listed() == list(run.plan.stages)
        page.back_to_matches_tab()
        assert page.setup_step_done("Groups & stages"), "Setup step 2 is not ticked after adding groups and stages"
        assert "Generate Fixtures" in page.setup_text(), "Setup step 3 'Generate Fixtures' did not appear"
        run.stages_ready = True


# -- 2. Form checks that save nothing ----------------------------------------


class TestFormChecks:
    def test_smart_auto_generate_is_not_available_yet(self, app, run):
        run.need("stages_ready", "stages")
        page = open_matches(app, run)
        result = page.smart_auto_generate_result()
        if result is None:
            pytest.skip("The app skipped the creation dialog, so Smart Auto-Generate was not offered")
        assert result == "coming soon", "Smart Auto-Generate now opens; automate it and update this test"

    def test_player_cannot_play_themselves(self, app, run):
        run.need("stages_ready", "stages")
        page = open_matches(app, run)
        group, members = next(iter(run.groups.items()))
        page.open_manual_form()
        try:
            page.open_first_player_picker(LEAGUE, group)
            rows = page.picker_rows()
            assert all(row.split("\n")[0] in members for row in rows), (
                f"{group} picker offers players from other groups: {rows}"
            )
            page.pick(members[0], f"first player {members[0]!r}")
            page.open_opponent_picker()
            rows = page.picker_rows()
            assert f"{members[0]}\nAlready selected for the other side" in rows, (
                f"{members[0]} can be chosen as their own opponent: {rows}"
            )
            page.cancel_picker()
        finally:
            leave_form(page)

    def test_start_time_is_required_and_past_dates_are_disabled(self, app, run):
        run.need("stages_ready", "stages")
        page = open_matches(app, run)
        group, members = next(iter(run.groups.items()))
        page.open_manual_form()
        try:
            page.choose_stage(LEAGUE)
            page.choose_group(group)
            page.choose_side(page.FIRST_PLAYER_FIELD, run.plan.league[0].first)
            page.choose_side(page.OPPONENT_FIELD, run.plan.league[0].second)
            assert not page.is_ready_to_review(), "The form is ready to review without a start time"

            page.open_start_date_picker()
            yesterday = date.today() - timedelta(days=1)
            if yesterday.month == date.today().month:
                assert not page.calendar_day_enabled(yesterday), f"{yesterday} (in the past) can be picked"
            page.cancel_date_picker()
        finally:
            leave_form(page)

    @pytest.mark.known_defect
    def test_dates_outside_the_tournament_are_disabled(self, app, run):
        """Defect D1 (11 Nov 2026): days before the start and after the end can be picked."""
        run.need("stages_ready", "stages")
        page = open_matches(app, run)
        start, end = tournament_dates(page.tournament_dates_text())
        page.open_manual_form()
        try:
            page.choose_stage(LEAGUE)
            page.choose_group(next(iter(run.groups)))
            page.open_start_date_picker()
            outside = [day for day in (start - timedelta(days=1), end + timedelta(days=1)) if day > date.today()]
            pickable = [day for day in outside if page.calendar_day_enabled(day)]
            page.cancel_date_picker()
        finally:
            leave_form(page)
        assert not pickable, f"Days outside the tournament ({start} - {end}) can be picked: {pickable}"


# -- 3. Creating fixtures ------------------------------------------------------


@pytest.mark.incremental
class TestFixtures:
    def test_creates_league_fixtures(self, app, run):
        run.need("stages_ready", "stages")
        page = open_matches(app, run)
        page.open_manual_form()
        for fixture in run.plan.league:
            page.create_fixture(fixture)
            run.league_created += 1
        page.back_to_matches_tab()

        assert page.scheduled_count() == len(run.plan.league)
        run.league_done = True

    def test_every_player_has_all_league_matches(self, app, run):
        run.need("league_done", "League fixtures")
        page = open_matches(app, run)
        page.open_manual_form()
        try:
            for group, members in run.groups.items():
                page.open_first_player_picker(LEAGUE, group)
                availability = page.picker_availability()
                rows = page.picker_rows()
                page.cancel_picker()
                matches_each = len(members) - 1
                assert availability.startswith("0 available"), f"{group}: {availability!r}"
                for name in members:
                    assert f"{name}\nHas all {matches_each} matches in League" in rows, (
                        f"{group}: {name} does not show all {matches_each} League matches: {rows}"
                    )
        finally:
            leave_form(page)

    def test_creates_knockout_fixtures(self, app, run):
        run.need("league_done", "League fixtures")
        page = open_matches(app, run)
        page.open_manual_form()
        for fixture in run.plan.knockout:
            page.create_fixture(fixture)
            run.knockout_created += 1
        page.back_to_matches_tab()
        run.knockout_done = True

    def test_scheduled_list_has_every_fixture(self, app, run):
        run.need("knockout_done", "knockout fixtures")
        page = open_matches(app, run)

        assert page.scheduled_count() == run.plan.total, (
            f"Scheduled shows {page.scheduled_count()}, planned {run.plan.total} "
            f"({len(run.plan.league)} League + {len(run.plan.knockout)} knockout)"
        )

    def test_fixtures_persist_after_reopening(self, app, run):
        run.need("knockout_done", "knockout fixtures")
        page = app.fixtures
        page.open_tournament(run.data.tournament)
        page.open_matches_tab()

        assert page.scheduled_count() == run.plan.total, (
            f"Scheduled shows {page.scheduled_count()} after reopening the tournament, planned {run.plan.total}"
        )


# -- 4. Known defects (assert the correct behaviour) ---------------------------


class TestKnownDefects:
    @pytest.mark.known_defect
    def test_generate_fixtures_step_is_ticked(self, app, run):
        """Defect D3 (11 Nov 2026): step 3 keeps its number although fixtures exist."""
        run.need("league_done", "League fixtures")
        page = open_matches(app, run)

        assert page.setup_step_done("Generate Fixtures"), (
            f"Setup step 3 is not ticked although {page.scheduled_count()} fixtures exist"
        )


def test_logs_out_at_the_end(app):
    app.logout.log_out()

    assert not app.logout.is_signed_in(), "Still signed in after logging out"
