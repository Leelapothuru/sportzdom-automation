"""Page object for logging out from the profile drawer on Home."""

import logging
import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import APP_PACKAGE
from pages.login_page import LoginPage

log = logging.getLogger(__name__)

class LogoutPage:
    """Profile drawer and logout dialog, backed by live Appium-inspected labels."""

    # The profile picture has no accessibility label, and its element type
    # changes (an image for a photo, something else for the letter placeholder),
    # so it is found by position: the clickable element left of the Home search box.
    CLICKABLE = (AppiumBy.XPATH, "//*[@clickable='true']")
    DRAWER_GENERAL = (AppiumBy.ACCESSIBILITY_ID, "GENERAL")
    # Drawer header: an image labelled with the profile name, holding the "ID ..." line.
    PROFILE_NAME = (AppiumBy.XPATH, "//*[starts-with(@content-desc, 'ID ')]/parent::android.widget.ImageView")
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
            if self.is_drawer_open():
                # The drawer covers Home's search box, and tapping the Home tab
                # does not close it; Back does.
                self.close_drawer()
                continue
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

    def is_drawer_open(self):
        return self.is_present(self.DRAWER_GENERAL) or self.is_present(self.DRAWER_ACCOUNT)

    def close_drawer(self):
        self.driver.back()
        try:
            WebDriverWait(self.driver, 5).until(lambda _: not self.is_drawer_open())
        except TimeoutException:
            raise AssertionError("Back did not close the profile drawer; see the screenshot") from None

    def open_profile_drawer(self):
        self.login.dismiss_overdue_popup()
        # The picture is found by position, so only tap it on Home.
        if not self.is_on_home():
            raise AssertionError("Not on Home; call go_to_home() before opening the profile drawer")
        try:
            self.profile_picture().click()
        except StaleElementReferenceException:
            # Home redrew between finding the picture and tapping it.
            self.profile_picture().click()
        try:
            self.wait.until(EC.visibility_of_element_located(self.DRAWER_GENERAL))
        except TimeoutException:
            raise AssertionError(
                "Tapping the profile picture did not open the profile drawer; see the screenshot"
            ) from None

    def profile_picture(self, attempts=3):
        """The clickable element directly left of the Home search box, on the same row.

        Home redraws while its feed loads, so elements can disappear while they
        are being measured; those are ignored and the search is repeated.
        """
        for _ in range(attempts):
            search = self.wait.until(EC.presence_of_element_located(self.HOME_SEARCH)).rect
            row_top, row_bottom = search["y"], search["y"] + search["height"]
            candidates = []
            for element in self.driver.find_elements(*self.CLICKABLE):
                try:
                    rect = element.rect
                except StaleElementReferenceException:
                    continue
                centre_y = rect["y"] + rect["height"] / 2
                if rect["x"] + rect["width"] <= search["x"] + 1 and row_top <= centre_y <= row_bottom:
                    candidates.append((search["x"] - (rect["x"] + rect["width"]), element))
            if candidates:
                # The nearest one to the search box, in case a wider container also matches.
                return min(candidates, key=lambda candidate: candidate[0])[1]
            time.sleep(1)
        raise AssertionError("No profile picture found left of the Home search box")

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

    def _drag_drawer(self, x, size):
        """One slow upward drag in the drawer; retried once if the device rejects the gesture.

        The device has rejected a drag ("Unable to perform W3C actions") on
        10 Nov 2026; a second attempt a moment later goes through.
        """
        start, end = int(size["height"] * 0.62), int(size["height"] * 0.29)
        try:
            self.driver.swipe(x, start, x, end, 900)
        except WebDriverException as error:
            log.warning("Drawer drag rejected (%s); retrying once", error.msg)
            time.sleep(1)
            self.driver.swipe(x, start, x, end, 900)

    def scroll_drawer_to_log_out(self, max_swipes=8):
        """Scroll the drawer until Log out is clear of the bottom navigation.

        The drawer ignores UiAutomator scroll commands; only a slow drag moves it.
        Its end also sits under the bottom navigation, where a tap would land on
        the navigation instead. Since "My Child" and "My Membership" were added
        (10 Nov 2026) the drawer needs more scrolling.

        Drags start in the drawer's right margin, beside the menu rows, so a
        drag that does not move the list cannot open a row such as My Profile.
        If the margin does not scroll the list, drags move to the middle of
        the drawer.
        """
        size = self.driver.get_window_size()
        drawer = self.driver.find_element(*self.DRAWER_GENERAL).rect
        margin_x = drawer["x"] + drawer["width"] - 18
        middle_x = int(size["width"] * 0.37)  # inside the drawer, left of the dimmed Home screen
        x = margin_x
        for _ in range(max_swipes):
            if self._log_out_clear_of_navigation():
                return
            before = self.driver.page_source
            self._drag_drawer(x, size)
            if not self.is_drawer_open():
                raise AssertionError("The profile drawer closed while scrolling to Log out; see the screenshot")
            if x == margin_x and self.driver.page_source == before:
                log.info("Drawer margin does not scroll the list; dragging in the middle")
                x = middle_x
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

    def profile_name(self):
        """Profile name of the signed-in account, read from the drawer header (e.g. 'user13')."""
        self.go_to_home()
        self.open_profile_drawer()
        name = self.wait.until(EC.presence_of_element_located(self.PROFILE_NAME)).get_attribute("content-desc")
        self.close_drawer()
        return name

    def log_out(self, attempts=2):
        """Log out from any signed-in screen and wait for the sign-in screen.

        If an attempt fails part-way (e.g. a rejected drawer drag), it starts
        again from Home once more before failing, so one flaky gesture does
        not leave the next account stuck behind an open drawer.
        """
        for attempt in range(1, attempts + 1):
            try:
                self.go_to_home()
                self.open_profile_drawer()
                self.open_logout_dialog()
                self.confirm_logout()
                return
            except (AssertionError, TimeoutException, WebDriverException) as error:
                if attempt == attempts or self.is_present(self.SIGNIN_TITLE):
                    raise
                log.warning("Log out attempt %s failed (%s); trying again from Home", attempt, error)
                if self.is_present(self.LOGOUT_DIALOG):
                    self.cancel_logout()

    def signin_identifier_text(self):
        return self.login.identifier_field().get_attribute("text")

    def is_get_code_enabled(self):
        return self.login.is_get_code_enabled()
