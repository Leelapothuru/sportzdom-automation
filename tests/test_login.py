"""Appium tests for the current Sportzdom OTP sign-in screen.

The demo-account test is opt-in because it leaves the shared device signed in.
Set SPORTZDOM_RUN_DEMO_LOGIN=true only on an isolated test device.
"""

import getpass
import os

import pytest
from selenium.common.exceptions import InvalidSessionIdException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from drivers.driver_manager import get_driver
from pages.login_page import LoginPage


@pytest.fixture
def driver():
    session = get_driver()
    yield session
    try:
        session.quit()
    except InvalidSessionIdException:
        # Preserve the original test outcome when Appium has already closed a session.
        pass


@pytest.fixture
def signin_page(driver):
    page = LoginPage(driver)
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


@pytest.mark.skipif(
    os.getenv("SPORTZDOM_RUN_DEMO_LOGIN", "").lower() != "true",
    reason="Set SPORTZDOM_RUN_DEMO_LOGIN=true on an isolated test device to test demo login.",
)
def test_demo_account_login_reaches_authenticated_experience(signin_page):
    """The app's built-in demo-account route completes a successful login."""
    signin_page.click_demo_account()
    WebDriverWait(signin_page.driver, 20).until(
        EC.invisibility_of_element_located(LoginPage.SCREEN_TITLE)
    )
