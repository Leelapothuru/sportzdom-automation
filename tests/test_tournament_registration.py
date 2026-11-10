"""Tournament registration: fill a published tournament with numbered test accounts.

Dynamic: the number of players to register is read from the tournament itself
(the "N/M" players count on its details page). Accounts are tried in order,
user1, user2, ... (test_data/tournament_data.json "registration": first_account
to last_account), until every place is taken. Accounts that hold an official
role in the tournament (organizer, referee, scorer, commentator, sponsor,
photographer, ... - every role listed on the Overview tab except Grounds) are
skipped: the app itself does not stop them from registering.

One device is shared by every account, so each account's test logs out the
previous account (LogoutPage.log_out), signs in with its own account
(LoginPage.sign_in_with_demo_account), reads its profile name, opens the
tournament and registers (Register now -> Agree -> "Successfully registered").
A player who is already registered is checked instead: the button reads
"Registered" and cannot be tapped, so reruns top the tournament up.

Order (one Appium session, tests run top to bottom):
  1. One test per account until the tournament is full; later accounts are
     skipped as not needed.
  2. The tournament shows every place taken (M/M).
  3. The organizer found in step 1 sees M/M players, then the app logs out.

The app accepts registrations beyond the expected count by design (confirmed
6 Nov 2026), so the tests stop at the expected count and never register more.

Accounts come from SPORTZDOM_PLAYER_EMAIL_TEMPLATE / SPORTZDOM_PLAYER_PASSWORD_TEMPLATE
({n} is the account number; secret pipeline variables in Azure DevOps).
Registrations on these test accounts are test data (confirmed 6 Nov 2026).
"""

import logging
from dataclasses import dataclass, field

import pytest
from selenium.common.exceptions import WebDriverException

from pages.login_page import LoginPage
from pages.logout_page import LogoutPage
from pages.tournament_registration_page import TournamentRegistrationPage
from test_data.tournament_data import account_credentials, registration_data
from utils.driver_setup import get_driver

log = logging.getLogger(__name__)

DATA = registration_data()
SUCCESS = TournamentRegistrationPage.SUCCESS_MESSAGE
POOL = f"user{DATA.first_account}-user{DATA.last_account}"

pytestmark = [
    pytest.mark.registration,
    pytest.mark.skipif(
        account_credentials(DATA.first_account) is None,
        reason="Set SPORTZDOM_PLAYER_EMAIL_TEMPLATE and SPORTZDOM_PLAYER_PASSWORD_TEMPLATE to run registration tests.",
    ),
]

# Names this feature's reports and screenshot folders (see conftest.py).
FEATURE = "tournament_registration"


class App:
    """Page objects on one Appium session, which can be replaced if it crashes."""

    def __init__(self):
        self._start()

    def _start(self):
        session = get_driver()
        self.login = LoginPage(session)
        self.logout = LogoutPage(session)
        self.registration = TournamentRegistrationPage(session)

    @property
    def driver(self):
        # Lets conftest.py find the session for step screenshots.
        return self.registration.driver

    def ensure_alive(self):
        """Start a new session when the current one no longer answers.

        On 10 Nov 2026 the UiAutomator2 server on the phone crashed mid-run and
        every later test failed with "instrumentation process is not running".
        """
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
class Progress:
    """What the run has learnt so far, shared by the tests in order."""

    capacity: int | None = None
    officials: dict | None = None          # {role: [profile names]}, read once
    full: bool = False
    organizers: list = field(default_factory=list)
    skipped_officials: dict = field(default_factory=dict)  # {account: roles}

    def roles_of(self, name):
        return [role for role, names in (self.officials or {}).items() if name in names]


@pytest.fixture(scope="module")
def app_session():
    """One Appium session shared by every account's steps (replaced if it crashes)."""
    app = App()
    yield app
    app.quit()


@pytest.fixture
def app(app_session):
    app_session.ensure_alive()
    return app_session


@pytest.fixture(scope="module")
def progress():
    return Progress()


def sign_in_as(app, number):
    """Log out whoever is signed in, sign in as test account number, return its profile name."""
    if app.login.app_state() != "signed_out":
        app.logout.log_out()
    email, password = account_credentials(number)
    log.info("Signing in as user%s", number)
    app.login.sign_in_with_demo_account(email, password)
    return app.logout.profile_name()


def open_tournament(app, progress):
    """Open the tournament; returns the registered count and records the capacity."""
    app.registration.open_tournament(DATA.tournament)
    registered, capacity = app.registration.player_count()
    if progress.capacity is None:
        progress.capacity = capacity
        log.info("%s expects %s players (%s registered)", DATA.tournament, capacity, registered)
    assert capacity == progress.capacity, f"Expected players changed from {progress.capacity} to {capacity}"
    if progress.officials is None:
        progress.officials = app.registration.officials()
        log.info("Officials: %s", progress.officials)
    return registered


@pytest.mark.parametrize("number", DATA.accounts, ids=[f"user{n}" for n in DATA.accounts])
def test_account_registers(app, progress, number):
    if progress.full:
        pytest.skip(f"Not needed: the tournament is full ({progress.capacity}/{progress.capacity})")

    name = sign_in_as(app, number)
    before = open_tournament(app, progress)

    roles = progress.roles_of(name)
    if roles:
        progress.skipped_officials[number] = roles
        if "Organizers" in roles:
            progress.organizers.append(number)
        pytest.skip(f"user{number} ({name}) is an official of the tournament: {', '.join(roles)}")

    label, enabled = app.registration.registration_state()
    if label == "Registered":
        # Registered earlier (e.g. a previous run): it must not be possible again.
        assert not enabled, f"user{number}: 'Registered' button can be tapped again (duplicate registration)"
        log.info("user%s (%s) was already registered (%s/%s)", number, name, before, progress.capacity)
        progress.full = before >= progress.capacity
        return

    if before >= progress.capacity:
        progress.full = True
        pytest.skip(f"The tournament was already full ({before}/{progress.capacity}) before user{number}")

    assert (label, enabled) == ("Register now", True), (
        f"user{number}: expected an enabled 'Register now', got {label!r} (enabled={enabled}) "
        f"at {before}/{progress.capacity}"
    )
    message = app.registration.register()
    assert message == SUCCESS, f"user{number} ({name}) was not registered; the app said: {message!r}"

    after, _ = app.registration.player_count()
    assert after == before + 1, f"user{number}: player count went from {before} to {after}, expected {before + 1}"
    assert app.registration.registration_state() == ("Registered", False), (
        f"user{number}: button does not show a disabled 'Registered' after registering"
    )
    listed = app.registration.players_registered_label()
    assert listed in (None, after), f"'{listed} players registered' does not match the count {after}"
    log.info("user%s (%s) registered: %s/%s", number, name, after, progress.capacity)
    progress.full = after >= progress.capacity


def test_tournament_is_full(app, progress):
    if progress.capacity is None:
        pytest.fail("No account opened the tournament; see the account tests")
    assert progress.full, f"Accounts {POOL} ran out before the tournament was full; add more accounts"
    if not app.registration.is_present(TournamentRegistrationPage.DETAILS_TITLE):
        open_tournament(app, progress)
    assert app.registration.player_count() == (progress.capacity, progress.capacity), (
        f"Expected every place taken ({progress.capacity}/{progress.capacity})"
    )


def test_organizer_sees_full_tournament(app, progress):
    if not progress.organizers:
        pytest.skip(f"No organizer account found among the accounts tried in {POOL}")
    number = progress.organizers[0]
    sign_in_as(app, number)
    registered = open_tournament(app, progress)

    assert registered == progress.capacity, f"Organizer user{number} sees {registered}/{progress.capacity} players"
    listed = app.registration.players_listed_on_teams_tab()
    assert listed == progress.capacity, f"Organizer's Teams tab lists {listed} players, expected {progress.capacity}"


def test_logs_out_at_the_end(app):
    app.logout.log_out()

    assert not app.logout.is_signed_in(), "Still signed in after logging out"
