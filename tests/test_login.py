"""Appium tests for the Sportzdom sign-in screen and demo-account login.

Both need the app signed out (log out first with tests/test_logout.py); they
are skipped, with a reason, when it is already signed in.
  1. Sign-in screen tests.
  2. Demo-account login (TestDemoAccountLogin) - defined last because it leaves
     the app signed in, ready for the tournament tests.
The demo credentials come from environment variables, never from the code:
    SPORTZDOM_DEMO_EMAIL, SPORTZDOM_DEMO_PASSWORD
"""

import getpass
import os

import pytest
from selenium.common.exceptions import InvalidSessionIdException

from pages.login_page import LoginPage
from utils.driver_setup import get_driver

# Names this feature's reports and screenshot folders (see conftest.py).
FEATURE = "login"

def _skip_unless_signed_out(page):
    state = page.app_state()
    if state != "signed_out":
        pytest.skip(
            f"Needs the app signed out (it is {state.replace('_', ' ')}); log out first "
            r"(.\venv\Scripts\python.exe -m pytest tests\test_logout.py -v)."
        )


def _quit(session):
    try:
        session.quit()
    except InvalidSessionIdException:
        # Preserve the original test outcome when Appium has already closed a session.
        pass


@pytest.fixture
def driver():
    session = get_driver()
    yield session
    _quit(session)


@pytest.fixture
def signin_page(driver):
    page = LoginPage(driver)
    _skip_unless_signed_out(page)
    page.open_signin()
    assert page.is_signin_screen_displayed(), "OTP sign-in screen did not become visible"
    page.select_mobile_number()
    page.clear_identifier()
    return page


def test_otp_signin_screen_displays_required_controls(signin_page):
    """Sign-in exposes OTP entry, account creation, and demo-account actions."""
    assert signin_page.is_signin_screen_displayed()
    assert signin_page.identifier_hint().startswith("Mobile number")
    assert not signin_page.is_get_code_enabled()


def test_email_mode_rejects_empty_and_malformed_identifier(signin_page):
    """Get code stays unavailable until a valid email address is supplied."""
    signin_page.select_email()
    assert signin_page.identifier_hint() == "Email address"
    assert not signin_page.is_get_code_enabled()

    signin_page.enter_identifier("not-an-email")
    assert not signin_page.is_get_code_enabled()


def test_mobile_mode_rejects_empty_identifier(signin_page):
    """Get code is unavailable while the mobile-number input is empty."""
    signin_page.select_mobile_number()
    assert signin_page.identifier_hint().startswith("Mobile number")
    assert not signin_page.is_get_code_enabled()


@pytest.mark.skipif(
    not (
        os.getenv("SPORTZDOM_RUN_VALID_MOBILE_CHECK", "").lower() == "true"
        and os.getenv("SPORTZDOM_TEST_MOBILE_NUMBER")
    ),
    reason=(
        "Set SPORTZDOM_RUN_VALID_MOBILE_CHECK=true and "
        "SPORTZDOM_TEST_MOBILE_NUMBER to run the configured-number check."
    ),
)
def test_valid_mobile_number_enables_otp_request(signin_page):
    """A valid mobile number enables Get code before any SMS is requested."""
    signin_page.enter_identifier(os.environ["SPORTZDOM_TEST_MOBILE_NUMBER"])
    assert signin_page.is_get_code_enabled(), "Valid mobile number did not enable Get code"


@pytest.mark.skipif(
    os.getenv("SPORTZDOM_RUN_INTERACTIVE_OTP_LOGIN", "").lower() != "true",
    reason="Set SPORTZDOM_RUN_INTERACTIVE_OTP_LOGIN=true for the terminal-prompt OTP test.",
)
def test_interactive_mobile_otp_login(driver):
    """Request an OTP, prompt the operator for it, then verify successful login."""
    page = LoginPage(driver)
    if not driver.find_elements(*LoginPage.OTP_SCREEN_TITLE):
        page.open_signin()
        page.select_mobile_number()

        mobile_number = input(
            "Enter the registered test mobile number (without country code): "
        ).strip()
        assert mobile_number, "A registered test mobile number is required"

        page.enter_identifier(mobile_number)
        page.request_otp()

    otp = getpass.getpass(
        "Enter the 6-digit OTP sent to the test mobile number: "
    ).strip()
    assert len(otp) == 6 and otp.isdigit(), "OTP must contain exactly six digits"

    page.wait_for_otp_screen()
    page.enter_otp(otp)
    assert page.wait_for_otp_result() == "authenticated", "OTP verification was rejected"


DEMO_EMAIL = os.getenv("SPORTZDOM_DEMO_EMAIL", "")
DEMO_PASSWORD = os.getenv("SPORTZDOM_DEMO_PASSWORD", "")


@pytest.fixture(scope="class")
def demo_login():
    """One Appium session shared by every step of the demo-account login."""
    session = get_driver()
    page = LoginPage(session)
    try:
        _skip_unless_signed_out(page)
        page.open_signin()
        yield page
    finally:
        _quit(session)


@pytest.mark.incremental
@pytest.mark.skipif(
    not (DEMO_EMAIL and DEMO_PASSWORD),
    reason="Set SPORTZDOM_DEMO_EMAIL and SPORTZDOM_DEMO_PASSWORD to run the demo-account login.",
)
class TestDemoAccountLogin:
    """Sign in with the demo email and password, one step at a time.

    Runs after the sign-in screen tests (it is defined last) because it leaves
    the app signed in. If a step fails, the remaining steps are skipped.
    """

    def test_demo_form_opens_with_sign_in_disabled(self, demo_login):
        demo_login.open_demo_account()

        assert demo_login.driver.find_elements(*LoginPage.DEMO_EMAIL_FIELD), "No email field"
        assert demo_login.driver.find_elements(*LoginPage.DEMO_PASSWORD_FIELD), "No password field"
        assert not demo_login.is_demo_sign_in_enabled(), "Sign in enabled on an empty form"

    def test_sign_in_stays_disabled_without_a_password(self, demo_login):
        demo_login.enter_demo_email(DEMO_EMAIL)

        assert demo_login.demo_email_value() == DEMO_EMAIL, "Email field does not hold the typed email"
        assert not demo_login.is_demo_sign_in_enabled(), "Sign in enabled without a password"

    def test_password_is_masked_and_enables_sign_in(self, demo_login):
        demo_login.enter_demo_password(DEMO_PASSWORD)

        assert demo_login.is_demo_password_masked(), "Password is shown in plain text"
        assert demo_login.is_demo_sign_in_enabled(), "Sign in stays disabled with email and password"

    def test_sign_in_reaches_the_signed_in_app(self, demo_login):
        demo_login.submit_demo_sign_in()
        demo_login.wait_for_signed_in()

        assert demo_login.driver.find_elements(*LoginPage.TOURNAMENTS_NAV), (
            "Bottom navigation not shown after sign-in"
        )
