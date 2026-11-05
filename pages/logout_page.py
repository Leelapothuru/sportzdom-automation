"""Page object for logging out from the profile drawer on Home."""

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import APP_PACKAGE
from pages.login_page import LoginPage


class LogoutPage:
    """Profile drawer and logout dialog, backed by live Appium-inspected labels."""

    # The profile picture has no accessibility label, and its element type
    # changes (an image for a photo, something else for the letter placeholder),
    # so it is found by position: the clickable element left of the Home search box.
    CLICKABLE = (AppiumBy.XPATH, "//*[@clickable='true']")
    DRAWER_GENERAL = (AppiumBy.ACCESSIBILITY_ID, "GENERAL")
    DRAWER_ACCOUNT = (AppiumBy.ACCESSIBILITY_ID, "ACCOUNT")
    MY_PROFILE = (AppiumBy.ACCESSIBILITY_ID, "My Profile")
    # Sits directly above Log out; never tapped by these tests.
    DELETE_ACCOUNT = (AppiumBy.ACCESSIBILITY_ID, "Delete Account")
    DRAWER_LOG_OUT = (AppiumBy.XPATH, "//android.widget.Button[@content-desc='Log out']")
    LOGOUT_DIALOG = (AppiumBy.ACCESSIBILITY_ID, "Log out?")
    LOGOUT_DIALOG_MESSAGE = (AppiumBy.ACCESSIBILITY_ID, "You can log back in any time.")
    LOGOUT_CANCEL = (AppiumBy.ACCESSIBILITY_ID, "Cancel")
    # The dialog's button has the same label as the drawer's, so anchor it to the dialog title.
    LOGOUT_CONFIRM = (
        AppiumBy.XPATH,
        "//*[@content-desc='Log out?']/following::android.widget.Button[@content-desc='Log out']",
    )

    TOURNAMENTS_NAV = LoginPage.TOURNAMENTS_NAV
    SIGNIN_TITLE = LoginPage.SCREEN_TITLE
    HOME_TAB = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.Button").descriptionStartsWith("Home")',
    )
    # Only Home has this search field at the top.
    HOME_SEARCH = (AppiumBy.XPATH, "//android.widget.EditText[starts-with(@hint, 'Search ID')]")
    APP_PACKAGE = APP_PACKAGE

    def __init__(self, driver, timeout=20):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        # Signed-in checks, the overdue popup and the sign-in screen belong to the login page.
        self.login = LoginPage(driver, timeout)

    def is_present(self, locator):
        return bool(self.driver.find_elements(*locator))

    def is_signed_in(self):
        return self.login.is_signed_in()

    def is_on_home(self):
        return self.is_present(self.HOME_SEARCH) and self.is_present(self.TOURNAMENTS_NAV)

    def go_to_home(self, max_back_presses=10):
        """Reach Home from whatever screen the signed-in app is showing.

        From a bottom-navigation tab, taps Home. From any other screen (a form,
        a details page, the drawer, a dialog) presses Back one step at a time
        until the bottom navigation appears. Inside a tournament form Back moves
        to the previous step; already-saved steps stay saved in the draft.
        """
        for _ in range(max_back_presses + 1):
            self.login.dismiss_overdue_popup()
            if self.is_on_home():
                return
            if self.driver.current_package != self.APP_PACKAGE:
                raise AssertionError(
                    f"Left the Sportzdom app (now in {self.driver.current_package}) while going to Home"
                )
            if self.is_present(self.SIGNIN_TITLE) or self.is_present(LoginPage.DEMO_TITLE):
                raise AssertionError("The app is on the sign-in screen; it is already signed out")
            if self.is_present(self.TOURNAMENTS_NAV):
                self.wait.until(EC.element_to_be_clickable(self.HOME_TAB)).click()
                try:
                    WebDriverWait(self.driver, 5).until(lambda _: self.is_on_home())
                except TimeoutException:
                    pass  # checked again at the top of the loop
                continue
            self.login.dismiss_keyboard()
            self.driver.back()
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda _: self.is_present(self.TOURNAMENTS_NAV) or self.is_present(self.SIGNIN_TITLE)
                )
            except TimeoutException:
                pass  # still on an inner screen; press Back again
        raise AssertionError(f"Could not reach Home after {max_back_presses} Back presses; see the screenshot")

    def open_profile_drawer(self):
        self.login.dismiss_overdue_popup()
        # The picture is found by position, so only tap it on Home.
        if not self.is_on_home():
            raise AssertionError("Not on Home; call go_to_home() before opening the profile drawer")
        self.profile_picture().click()
        try:
            self.wait.until(EC.visibility_of_element_located(self.DRAWER_GENERAL))
        except TimeoutException:
            raise AssertionError(
                "Tapping the profile picture did not open the profile drawer; see the screenshot"
            ) from None

    def profile_picture(self):
        """The clickable element directly left of the Home search box, on the same row."""
        search = self.wait.until(EC.presence_of_element_located(self.HOME_SEARCH)).rect
        row_top, row_bottom = search["y"], search["y"] + search["height"]
        candidates = []
        for element in self.driver.find_elements(*self.CLICKABLE):
            rect = element.rect
            centre_y = rect["y"] + rect["height"] / 2
            if rect["x"] + rect["width"] <= search["x"] + 1 and row_top <= centre_y <= row_bottom:
                candidates.append((search["x"] - (rect["x"] + rect["width"]), element))
        if not candidates:
            raise AssertionError("No profile picture found left of the Home search box")
        # The nearest one to the search box, in case a wider container also matches.
        return min(candidates, key=lambda candidate: candidate[0])[1]

    def _log_out_clear_of_navigation(self):
        """True when the drawer's Log out button is fully above the bottom navigation."""
        buttons = self.driver.find_elements(*self.DRAWER_LOG_OUT)
        navigation = self.driver.find_elements(*self.TOURNAMENTS_NAV)
        if not buttons:
            return False
        if not navigation:
            return True
        button = buttons[0].rect
        return button["y"] + button["height"] <= navigation[0].rect["y"]

    def scroll_drawer_to_log_out(self, max_swipes=5):
        """Scroll the drawer until Log out is clear of the bottom navigation.

        The drawer ignores UiAutomator scroll commands; only a slow drag moves it.
        Its end also sits under the bottom navigation, where a tap would land on
        the navigation instead.
        """
        size = self.driver.get_window_size()
        x = int(size["width"] * 0.37)  # inside the drawer, left of the dimmed Home screen
        for _ in range(max_swipes):
            if self._log_out_clear_of_navigation():
                return
            self.driver.swipe(x, int(size["height"] * 0.62), x, int(size["height"] * 0.29), 900)
        if not self._log_out_clear_of_navigation():
            raise AssertionError(f"Log out not reachable above the bottom navigation after {max_swipes} swipes")

    def open_logout_dialog(self):
        self.scroll_drawer_to_log_out()
        # Tapped by its exact label only: Delete Account sits directly above it.
        self.wait.until(EC.element_to_be_clickable(self.DRAWER_LOG_OUT)).click()
        self.wait.until(EC.visibility_of_element_located(self.LOGOUT_DIALOG))

    def cancel_logout(self):
        self.wait.until(EC.element_to_be_clickable(self.LOGOUT_CANCEL)).click()
        self.wait.until(EC.invisibility_of_element_located(self.LOGOUT_DIALOG))

    def confirm_logout(self, timeout=45):
        self.wait.until(EC.element_to_be_clickable(self.LOGOUT_CONFIRM)).click()
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SIGNIN_TITLE)
            )
        except TimeoutException:
            raise AssertionError(f"Sign-in screen not shown {timeout}s after confirming Log out") from None

    def signin_identifier_text(self):
        return self.login.identifier_field().get_attribute("text")

    def is_get_code_enabled(self):
        return self.login.is_get_code_enabled()
