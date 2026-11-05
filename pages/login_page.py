
"""Page object for the current Sportzdom OTP sign-in screen."""

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.tournament_page import TournamentsPage


class LoginPage:
    """Interactions backed by live Appium-inspected accessibility labels."""

    SIGN_IN_ENTRY = (AppiumBy.ACCESSIBILITY_ID, "Sign in")
    SCREEN_TITLE = (AppiumBy.ACCESSIBILITY_ID, "Welcome back")
    SCREEN_SUBTITLE = (
        AppiumBy.ACCESSIBILITY_ID,
        "Sign in with a one-time code. No password needed.",
    )
    MOBILE_TAB = (AppiumBy.ACCESSIBILITY_ID, "Mobile number")
    EMAIL_TAB = (AppiumBy.ACCESSIBILITY_ID, "Email")
    IDENTIFIER_FIELD = (AppiumBy.CLASS_NAME, "android.widget.EditText")
    GET_CODE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Get code")
    CREATE_ACCOUNT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Create an account")
    DEMO_ACCOUNT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Use a demo account")
    OTP_SCREEN_TITLE = (AppiumBy.ACCESSIBILITY_ID, "Verify your number")
    VERIFY_OTP_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Verify & continue")
    OTP_ERROR = (
        AppiumBy.ACCESSIBILITY_ID,
        "That code isn't right. Check it and try again.",
    )
    HOME_NAVIGATION = (AppiumBy.ACCESSIBILITY_ID, "Home\nHome")

    # Demo account form, opened from "Use a demo account".
    DEMO_TITLE = (AppiumBy.ACCESSIBILITY_ID, "Demo account")
    DEMO_EMAIL_FIELD = (AppiumBy.XPATH, "//android.widget.EditText[@hint='Email address']")
    DEMO_PASSWORD_FIELD = (AppiumBy.XPATH, "//android.widget.EditText[@hint='Password']")
    # Same label as the registration screen's SIGN_IN_ENTRY; only used on the demo form.
    DEMO_SIGN_IN_BUTTON = (AppiumBy.XPATH, "//android.widget.Button[@content-desc='Sign in']")
    BACK_TO_CODE_SIGNIN = (AppiumBy.ACCESSIBILITY_ID, "Back to code sign-in")

    # Signed-in app. The overdue-tournament popup can cover Home right after sign-in.
    TOURNAMENTS_NAV = TournamentsPage.TOURNAMENTS_NAV
    OVERDUE_POPUP = TournamentsPage.OVERDUE_POPUP
    REMIND_ME_LATER = TournamentsPage.REMIND_ME_LATER
    # Title bar of the tournament form; shown while signed in, without bottom navigation.
    TOURNAMENT_FORM = (AppiumBy.ACCESSIBILITY_ID, "Tournament Form")

    def __init__(self, driver, timeout=20):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def is_signed_in(self):
        """True when the app shows Home's bottom navigation or the overdue popup."""
        return bool(
            self.driver.find_elements(*self.TOURNAMENTS_NAV)
            or self.driver.find_elements(*self.OVERDUE_POPUP)
        )

    def _is_signed_out(self):
        return any(
            self.driver.find_elements(*locator)
            for locator in (self.SCREEN_TITLE, self.DEMO_TITLE, self.SIGN_IN_ENTRY)
        )

    def app_state(self, timeout=10):
        """'signed_out', 'signed_in' or 'unknown', from what the screen shows.

        Signed in includes screens without the bottom navigation, such as an
        open tournament form. Waits briefly because a new session can start
        while the screen is still drawing.
        """
        signed_in = (self.TOURNAMENTS_NAV, self.OVERDUE_POPUP, self.TOURNAMENT_FORM)

        def detect(_):
            if self._is_signed_out():
                return "signed_out"
            if any(self.driver.find_elements(*locator) for locator in signed_in):
                return "signed_in"
            return False

        try:
            return WebDriverWait(self.driver, timeout).until(detect)
        except TimeoutException:
            return "unknown"

    def open_signin(self):
        """Open the code sign-in screen from wherever the signed-out app currently is."""
        self.dismiss_keyboard()
        if self.driver.find_elements(*self.DEMO_TITLE):
            # A previous test left the demo form open. Its "Sign in" button shares
            # the registration entry's label, so leave the form before anything else.
            self.wait.until(EC.element_to_be_clickable(self.BACK_TO_CODE_SIGNIN)).click()
        elif not self.driver.find_elements(*self.SCREEN_TITLE):
            self.wait.until(EC.element_to_be_clickable(self.SIGN_IN_ENTRY)).click()
        self.wait.until(EC.visibility_of_element_located(self.SCREEN_TITLE))
        self.dismiss_keyboard()

    def dismiss_keyboard(self):
        """Close the keyboard and wait until it is gone.

        On the sign-in and demo screens the keyboard covers the lower buttons
        (Create an account, Use a demo account, Sign in), so they cannot be
        seen or tapped while it is open.
        """
        if not self.driver.is_keyboard_shown():
            return
        try:
            self.driver.hide_keyboard()
        except WebDriverException:
            # The keyboard closed on its own between the check and the call.
            pass
        try:
            WebDriverWait(self.driver, 5).until(lambda driver: not driver.is_keyboard_shown())
        except TimeoutException:
            raise AssertionError("The keyboard did not close; the lower buttons stay hidden") from None

    def is_signin_screen_displayed(self):
        # The identifier field can take focus and open the keyboard just after
        # the screen appears, hiding the lower buttons.
        self.dismiss_keyboard()
        return all(
            self.wait.until(EC.visibility_of_element_located(locator)).is_displayed()
            for locator in (
                self.SCREEN_TITLE,
                self.SCREEN_SUBTITLE,
                self.IDENTIFIER_FIELD,
                self.GET_CODE_BUTTON,
                self.CREATE_ACCOUNT_BUTTON,
                self.DEMO_ACCOUNT_BUTTON,
            )
        )

    def select_email(self):
        self.wait.until(EC.element_to_be_clickable(self.EMAIL_TAB)).click()
        self.wait.until(
            lambda driver: self.identifier_field().get_attribute("hint") == "Email address"
        )

    def select_mobile_number(self):
        self.wait.until(EC.element_to_be_clickable(self.MOBILE_TAB)).click()
        self.wait.until(
            lambda driver: self.identifier_field().get_attribute("hint").startswith(
                "Mobile number"
            )
        )

    def identifier_field(self):
        return self.wait.until(EC.visibility_of_element_located(self.IDENTIFIER_FIELD))

    def enter_identifier(self, identifier):
        field = self.identifier_field()
        field.click()
        field.clear()
        field.send_keys(identifier)

    def clear_identifier(self):
        field = self.identifier_field()
        field.click()
        field.clear()
        self.dismiss_keyboard()

    def identifier_hint(self):
        return self.identifier_field().get_attribute("hint")

    def is_get_code_enabled(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.GET_CODE_BUTTON)
        ).is_enabled()

    def request_otp(self):
        """Request an OTP for the selected, validated mobile-number mode."""
        if not self.is_get_code_enabled():
            raise RuntimeError("Get code is disabled; enter a valid mobile number first.")
        self.dismiss_keyboard()
        self.wait.until(EC.element_to_be_clickable(self.GET_CODE_BUTTON)).click()
        self.wait_for_otp_screen()

    def wait_for_otp_screen(self):
        self.wait.until(EC.visibility_of_element_located(self.OTP_SCREEN_TITLE))

    def enter_otp(self, otp):
        """Focus and populate the one-time-code field on the verification screen."""
        field = self.wait.until(
            EC.element_to_be_clickable(self.IDENTIFIER_FIELD)
        )
        field.click()
        field.clear()
        field.send_keys(otp)
        self.dismiss_keyboard()

    def wait_for_otp_result(self):
        """Wait for the app's automatic or button-driven OTP verification result."""
        self.wait.until(
            lambda driver: (
                driver.find_elements(*self.HOME_NAVIGATION)
                or driver.find_elements(*self.OTP_ERROR)
                or self._is_verify_button_enabled()
            )
        )

        if self.driver.find_elements(*self.OTP_ERROR):
            return "rejected"
        if self.driver.find_elements(*self.HOME_NAVIGATION):
            return "authenticated"

        self.wait.until(EC.element_to_be_clickable(self.VERIFY_OTP_BUTTON)).click()
        self.wait.until(
            lambda driver: (
                driver.find_elements(*self.HOME_NAVIGATION)
                or driver.find_elements(*self.OTP_ERROR)
            )
        )
        return "rejected" if self.driver.find_elements(*self.OTP_ERROR) else "authenticated"

    def _is_verify_button_enabled(self):
        buttons = self.driver.find_elements(*self.VERIFY_OTP_BUTTON)
        return bool(buttons and buttons[0].is_enabled())

    def click_demo_account(self):
        self.dismiss_keyboard()
        self.wait.until(EC.element_to_be_clickable(self.DEMO_ACCOUNT_BUTTON)).click()

    # -- Demo account form -------------------------------------------------

    def open_demo_account(self):
        self.click_demo_account()
        self.wait.until(EC.visibility_of_element_located(self.DEMO_TITLE))
        self.dismiss_keyboard()

    def _fill(self, locator, value):
        # The demo email field keeps text typed earlier on the code sign-in
        # screen's Email tab, so always clear before typing.
        field = self.wait.until(EC.element_to_be_clickable(locator))
        field.click()
        field = self.wait.until(EC.element_to_be_clickable(locator))
        field.clear()
        field.send_keys(value)

    def enter_demo_email(self, email):
        self._fill(self.DEMO_EMAIL_FIELD, email)

    def enter_demo_password(self, password):
        self._fill(self.DEMO_PASSWORD_FIELD, password)

    def demo_email_value(self):
        return self.wait.until(EC.presence_of_element_located(self.DEMO_EMAIL_FIELD)).get_attribute("text")

    def is_demo_password_masked(self):
        field = self.wait.until(EC.presence_of_element_located(self.DEMO_PASSWORD_FIELD))
        return field.get_attribute("password") == "true"

    def is_demo_sign_in_enabled(self):
        # Checked with the keyboard closed: while it is open the button is
        # squeezed to a few pixels behind it.
        self.dismiss_keyboard()
        button = self.wait.until(EC.presence_of_element_located(self.DEMO_SIGN_IN_BUTTON))
        return button.get_attribute("enabled") == "true"

    def submit_demo_sign_in(self):
        self.dismiss_keyboard()
        self.wait.until(EC.element_to_be_clickable(self.DEMO_SIGN_IN_BUTTON)).click()

    def wait_for_signed_in(self, timeout=45):
        """Wait for the signed-in app, then close the overdue-tournament popup if it is shown."""
        try:
            WebDriverWait(self.driver, timeout).until(lambda _: self.is_signed_in())
        except TimeoutException:
            still_on_form = bool(self.driver.find_elements(*self.DEMO_TITLE))
            raise AssertionError(
                f"Not signed in {timeout}s after tapping Sign in"
                + (" - the demo form is still shown (check the credentials)" if still_on_form else "")
            ) from None
        self.dismiss_overdue_popup()

    def dismiss_overdue_popup(self):
        if not self.driver.find_elements(*self.OVERDUE_POPUP):
            return
        self.wait.until(EC.element_to_be_clickable(self.REMIND_ME_LATER)).click()
        self.wait.until(EC.invisibility_of_element_located(self.OVERDUE_POPUP))

