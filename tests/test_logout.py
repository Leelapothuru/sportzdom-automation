"""Appium tests for logging out of Sportzdom from the profile drawer.

Needs the app signed in (e.g. after tests/test_login.py's demo-account login);
skipped, with a reason, when it is already signed out. Starts from whatever
screen the app is on: it first goes to Home (Home tab, or Back until the bottom
navigation appears). Runs as one ordered flow in a single session and ends on
the sign-in screen. If a step fails, the remaining steps are skipped. Delete
Account is checked but never tapped.
"""

import pytest
from selenium.common.exceptions import InvalidSessionIdException

from pages.logout_page import LogoutPage
from utils.driver_setup import get_driver

pytestmark = pytest.mark.incremental

# Names this feature's reports and screenshot folders (see conftest.py).
FEATURE = "logout"


@pytest.fixture(scope="module")
def logout():
    """One Appium session shared by every step of the logout flow."""
    session = get_driver()
    page = LogoutPage(session)
    try:
        if page.login.app_state() == "signed_out":
            pytest.skip("The app is already signed out; sign in first (tests/test_login.py demo login).")
        yield page
    finally:
        try:
            session.quit()
        except InvalidSessionIdException:
            # Preserve the original test outcome when Appium has already closed a session.
            pass


class TestLogout:
    def test_app_returns_to_home_from_any_screen(self, logout):
        logout.go_to_home()

        assert logout.is_on_home(), "Home is not shown"

    def test_profile_picture_opens_the_drawer(self, logout):
        logout.open_profile_drawer()

        assert logout.is_present(LogoutPage.DRAWER_GENERAL), "Drawer did not open"

    def test_drawer_lists_the_account_actions(self, logout):
        logout.scroll_drawer_to_log_out()

        for item in (LogoutPage.DRAWER_ACCOUNT, LogoutPage.MY_PROFILE,
                     LogoutPage.DELETE_ACCOUNT, LogoutPage.DRAWER_LOG_OUT):
            assert logout.is_present(item), f"'{item[1]}' missing from the drawer"

    def test_log_out_asks_for_confirmation(self, logout):
        logout.open_logout_dialog()

        assert logout.is_present(LogoutPage.LOGOUT_DIALOG_MESSAGE), "Dialog message missing"
        assert logout.is_present(LogoutPage.LOGOUT_CANCEL), "No Cancel button"
        assert logout.is_present(LogoutPage.LOGOUT_CONFIRM), "No Log out button in the dialog"

    def test_cancel_keeps_the_user_signed_in(self, logout):
        logout.cancel_logout()

        assert logout.is_present(LogoutPage.DRAWER_LOG_OUT), "Drawer closed after Cancel"
        assert not logout.is_present(LogoutPage.SIGNIN_TITLE), "Signed out although Cancel was tapped"

    def test_confirming_logs_out_to_the_signin_screen(self, logout):
        logout.open_logout_dialog()
        logout.confirm_logout()

        assert not logout.is_signed_in(), "Bottom navigation still shown after logout"
        assert logout.signin_identifier_text() == "", "Sign-in field not empty after logout"
        assert not logout.is_get_code_enabled(), "Get code enabled on an empty sign-in form"
