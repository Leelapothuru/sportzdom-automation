"""Shared sign-in handling for flows that switch between numbered test accounts.

sign_in_as() looks at the app first and only signs in when it has to:
  * signed out                        -> sign in with the account;
  * signed in as the wanted account   -> keep the session;
  * signed in as anyone else          -> log out, then sign in;
  * on a screen without navigation    -> go back to Home first, then decide.

Profile names do not follow the account numbers (user1 is "Vishwa"), so the
signed-in account is recognised either by a profile name learnt earlier in
the run (PROFILE_NAMES) or by the caller's accept(name) check, e.g. "is an
organizer of the tournament". When neither applies, the current account is
logged out without opening the profile drawer first, which keeps runs that
switch account on every test (registration) as fast as before.
"""

import logging

from selenium.common.exceptions import WebDriverException

from test_data.tournament_data import account_credentials

log = logging.getLogger(__name__)

# Account number -> profile name, learnt as accounts sign in during this run.
PROFILE_NAMES = {}


def app_state(login, logout):
    """'signed_in', 'signed_out' or 'unknown'; an unrecognised screen is taken back to Home first."""
    state = login.app_state()
    if state == "unknown":
        # e.g. a tournament's details page, which has no bottom navigation
        try:
            logout.go_to_home()
        except (AssertionError, WebDriverException) as error:
            log.warning("Could not reach Home (%s)", error)
        state = login.app_state()
    return state


def sign_in_as(login, logout, number, accept=None):
    """Make sure test account number (or an account accept() approves) is signed in.

    login / logout: LoginPage and LogoutPage on the same session.
    accept: optional check on the signed-in profile name; when it returns True
        the current session is kept even if it is not account number.
    Returns the signed-in profile name.
    """
    state = app_state(login, logout)
    log.info("App state before signing in user%s: %s", number, state)

    if state == "signed_in":
        if number in PROFILE_NAMES or accept is not None:
            name = logout.profile_name()
            if name == PROFILE_NAMES.get(number) or (accept is not None and accept(name)):
                log.info("Already signed in as %s; keeping the session", name)
                return name
            log.info("Signed in as %s; switching to user%s", name, number)
        logout.log_out()
    elif state != "signed_out":
        raise AssertionError("The app is neither signed in nor on the sign-in screen; see the screenshot")

    credentials = account_credentials(number)
    assert credentials, (
        "No test account credentials; set SPORTZDOM_PLAYER_EMAIL_TEMPLATE and SPORTZDOM_PLAYER_PASSWORD_TEMPLATE"
    )
    log.info("Signing in as user%s", number)
    login.sign_in_with_demo_account(*credentials)
    name = logout.profile_name()
    PROFILE_NAMES[number] = name
    return name
