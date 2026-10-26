
"""Page object for the current Sportzdom OTP sign-in screen."""

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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

    def __init__(self, driver, timeout=20):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def open_signin(self):
        """Open sign-in from registration, or reuse an already-open sign-in screen."""
        if self.driver.find_elements(*self.SCREEN_TITLE):
            self.dismiss_keyboard()
            return
        self.wait.until(EC.element_to_be_clickable(self.SIGN_IN_ENTRY)).click()
        self.wait.until(EC.visibility_of_element_located(self.SCREEN_TITLE))
        self.dismiss_keyboard()

    def dismiss_keyboard(self):
        """Return to a stable full-screen state when a prior test left the IME open."""
        if self.driver.is_keyboard_shown():
            self.driver.hide_keyboard()

    def is_signin_screen_displayed(self):
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
        self.wait.until(EC.element_to_be_clickable(self.DEMO_ACCOUNT_BUTTON)).click()

