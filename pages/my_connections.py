"""Page object for the Profile drawer's My Connections screen."""

from __future__ import annotations

from xml.etree import ElementTree

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.myprofile_page import MyProfilePage
from utils.configuration import (
    get_short_wait_timeout_seconds,
    get_wait_timeout_seconds,
)


class MyConnectionsPage:
    """Navigate My Connections and perform actions selected by the test."""

    MY_CONNECTIONS_TAB = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("My Connections")')
    REQUESTS_TAB = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("Requests")')
    ADD_CONNECTIONS_TAB = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("Add Connections")')
    DISCOVER_TAB_LOCATORS = (
        (AppiumBy.ACCESSIBILITY_ID, "Discover"),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Discover")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Discover")'),
    )
    SEARCH_FIELD = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(0)')
    CONNECT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Connect").instance(4)')
    ANY_CONNECT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Connect")')
    OK_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Ok")')
    ACCEPT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Accept")')
    DECLINE_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Decline")')
    DELETE_CONNECTION_LOCATORS = (
        (AppiumBy.ACCESSIBILITY_ID, "Delete connection"),
        (AppiumBy.ACCESSIBILITY_ID, "Remove connection"),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Delete")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Remove")'),
    )
    CONFIRM_DELETE_LOCATORS = (
        (AppiumBy.ACCESSIBILITY_ID, "Confirm"),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Confirm")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Confirm")'),
        (AppiumBy.ACCESSIBILITY_ID, "Yes"),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Yes")'),
    )
    OK_BUTTON_LOCATORS = (
        OK_BUTTON,
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("OK")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Ok")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("OK")'),
    )

    def __init__(self, driver, timeout: float | None = None):
        self.driver = driver
        self.timeout = get_wait_timeout_seconds() if timeout is None else timeout
        self.wait = WebDriverWait(driver, self.timeout)
        self.profile = MyProfilePage(driver, timeout=self.timeout)

    def _click(self, locator) -> None:
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def _tab_is_visible(self, locator) -> bool:
        return any(element.is_displayed() for element in self.driver.find_elements(*locator))

    def _confirm_connection_delete(self) -> None:
        """Tap the confirmation control shown after requesting connection removal."""
        for locator in self.CONFIRM_DELETE_LOCATORS:
            try:
                WebDriverWait(self.driver, get_short_wait_timeout_seconds()).until(
                    EC.element_to_be_clickable(locator)
                ).click()
                return
            except TimeoutException:
                continue
        raise TimeoutException("Connection delete confirmation was not displayed")

    def open(self) -> None:
        """Open My Connections from the signed-in Profile drawer."""
        if self._tab_is_visible(self.MY_CONNECTIONS_TAB):
            print("My Connections is already open")
            return

        print("📍 Opening My Connections...")
        try:
            self.profile.open_my_connections()
            print("✓ My Connections opened successfully")
        except TimeoutException as exc:
            raise AssertionError("My Connections did not open after selecting it from Profile") from exc

    def select_my_connections(self) -> None:
        """Select My Connections tab"""
        print("📍 Selecting My Connections tab...")
        self._click(self.MY_CONNECTIONS_TAB)
        print("✓ My Connections tab selected")

    def delete_one_connection_if_present(self) -> bool:
        """Delete one existing connection, returning False when none are listed."""
        for locator in self.DELETE_CONNECTION_LOCATORS:
            for button in self.driver.find_elements(*locator):
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    self._confirm_connection_delete()
                    return True

        window = self.driver.get_window_size()
        connection_rows = []
        for row in self.driver.find_elements(
            AppiumBy.XPATH,
            '//*[@class="android.widget.ImageView" and @content-desc] | '
            '//*[@class="android.view.View" and @content-desc]',
        ):
            try:
                rect = row.rect
                description = (row.get_attribute("content-desc") or "").strip()
                if (
                    description
                    and rect["width"] >= window["width"] * 0.9
                    and 100 <= rect["height"] <= 180
                    and row.is_displayed()
                    and row.get_attribute("clickable") == "true"
                ):
                    connection_rows.append((row, description))
            except Exception:
                continue

        if connection_rows:
            row, description = connection_rows[0]
            rect = row.rect
            self.driver.execute_script(
                "mobile: clickGesture",
                {
                    "x": int(window["width"] * 0.622),
                    "y": rect["y"] + rect["height"] // 2,
                },
            )
            self._confirm_connection_delete()
            self.wait.until(
                lambda driver: all(
                    (element.get_attribute("content-desc") or "").strip() != description
                    for element in driver.find_elements(
                        AppiumBy.XPATH,
                        '//*[@class="android.widget.ImageView" and @content-desc] | '
                        '//*[@class="android.view.View" and @content-desc]',
                    )
                )
            )
            return True

        print("No connection delete control was found; skipping removal")
        return False

    def select_requests(self) -> None:
        """Select Requests tab"""
        print("📍 Selecting Requests tab...")
        self._click(self.REQUESTS_TAB)
        print("✓ Requests tab selected")

    def select_add_connections(self) -> None:
        """Select Discover, falling back to the older Add Connections label."""
        print("📍 Selecting Discover tab...")
        locators = self.DISCOVER_TAB_LOCATORS + (self.ADD_CONNECTIONS_TAB,)
        for locator in locators:
            try:
                WebDriverWait(self.driver, get_short_wait_timeout_seconds()).until(
                    EC.element_to_be_clickable(locator)
                ).click()
                print("✓ Discover tab selected")
                return
            except TimeoutException:
                continue
        raise TimeoutException("Discover tab was not visible")

    def pending_request_count(self) -> int:
        """Count visible pending requests by their Accept controls."""
        return sum(
            1
            for button in self.driver.find_elements(*self.ACCEPT_BUTTON)
            if button.is_displayed() and button.is_enabled()
        )

    def check_if_requests_available(self) -> bool:
        """Check whether at least one pending connection request is visible."""
        count = self.pending_request_count()
        if count:
            print(f"✓ Found {count} pending request(s)")
            return True
        print("⚠ No pending requests found")
        return False

    def accept_one_request_if_present(self) -> bool:
        """Accept one pending request, returning False when the tab is empty."""
        if not self.check_if_requests_available():
            print("No pending requests; skipping acceptance")
            return False

        accept_button = self.wait.until(EC.element_to_be_clickable(self.ACCEPT_BUTTON))
        accept_button.click()
        self._click_ok_if_popup_is_shown()
        print("Connection request accepted")
        return True

    def decline_one_request_if_present(self) -> bool:
        """Decline one pending request, returning False when none are visible."""
        decline_buttons = [
            button
            for button in self.driver.find_elements(*self.DECLINE_BUTTON)
            if button.is_displayed() and button.is_enabled()
        ]
        if not decline_buttons:
            print("No pending request to decline")
            return False

        decline_buttons[0].click()
        self._click_ok_if_popup_is_shown()
        print("Connection request declined")
        return True

    def handle_pending_requests(self) -> int:
        """Accept one request and, when there are at least two, decline another."""
        count = self.pending_request_count()
        if count == 0:
            print("No pending requests; continuing to Discover")
            return 0

        self.accept_one_request_if_present()
        if count >= 2 and not self.decline_one_request_if_present():
            raise TimeoutException(
                "Two or more pending requests were found, but none could be declined"
            )
        return count

    def handle_requests_and_continue(self, target_users: list[str]) -> list[str]:
        """Handle an available request, then send requests to supplied test users.
        
        This is the main workflow:
        1. Check Connections and Requests
        2. Accept one request, declining one more when there are at least two
        3. Go to Discover and send the supplied connection requests
        """
        print("\n" + "="*70)
        print("🚀 STARTING REQUESTS & ADD CONNECTIONS WORKFLOW")
        print("="*70 + "\n")
        
        try:
            # Step 1: Open My Connections
            self.open()
            
            # Step 2: Check connections, then process requests
            self.select_my_connections()
            self.select_requests()
            self.handle_pending_requests()
            
            # Step 3: Go to Discover
            print("\n📍 Moving to Discover tab...")
            self.select_add_connections()
            
            # Step 5: Send connection requests
            print("\n📍 Sending connection requests to 2 random users...")
            users = self.send_connection_requests(target_users)
            
            print("\n" + "="*70)
            print("✅ WORKFLOW COMPLETED SUCCESSFULLY")
            print("="*70)
            print(f"📊 Summary:")
            print(f"   - Requests processed (if available)")
            print(f"   - Connection requests sent to: {', '.join(users)}")
            print("="*70 + "\n")
            return users
            
        except Exception as e:
            print(f"\n❌ Workflow failed: {e}")
            raise

    def send_connection_requests(self, users: list[str]) -> list[str]:
        """Send requests to the user names supplied by the test scenario."""
        if not users:
            raise ValueError("At least one target username is required")
        print(f"🔍 Searching for users: {users}\n")
        
        for user in users:
            print(f"  📌 Processing user: {user}")
            search_field = self._find_search_field_after_scrolling()
            search_field.clear()
            search_field.send_keys(user)
            print(f"  ✓ Searched for: {user}")
            
            # Submit the search so the filtered user result is loaded before
            # selecting its Connect control.
            self.driver.press_keycode(66)  # Android KEYCODE_ENTER

            self._click_connect_button_with_scroll()
            print(f"  ✓ Connect button clicked for {user}")
            
            self._click_ok_if_popup_is_shown()
            print(f"  ✓ Connection request sent to {user}")

        return users

    def _find_search_field_after_scrolling(self, max_swipes: int = 8) -> WebElement:
        """Scroll Discover back to its search field before locating it."""
        window = self.driver.get_window_size()
        x = window["width"] // 2
        for swipe_count in range(max_swipes + 1):
            for field in self.driver.find_elements(*self.SEARCH_FIELD):
                if field.is_displayed() and field.is_enabled():
                    return field
            if swipe_count < max_swipes:
                self.driver.swipe(
                    x,
                    int(window["height"] * 0.28),
                    x,
                    int(window["height"] * 0.82),
                    500,
                )
        raise TimeoutException(
            "Discover search field was not visible after scrolling to the top"
        )

    def _click_ok_if_popup_is_shown(self) -> bool:
        """Confirm the optional request popup without failing when none is shown."""
        popup_wait = WebDriverWait(self.driver, get_short_wait_timeout_seconds())

        def find_clickable_ok(driver):
            for locator in self.OK_BUTTON_LOCATORS:
                for button in driver.find_elements(*locator):
                    if button.is_displayed() and button.is_enabled():
                        return button, locator
            return False

        try:
            button, locator = popup_wait.until(find_clickable_ok)
        except TimeoutException:
            return False

        button.click()
        self.wait.until(EC.invisibility_of_element_located(locator))
        return True

    def _click_connect_button_with_scroll(self, max_swipes: int = 8) -> None:
        """Click Connect instance 4, or scroll until any Discover result is visible."""
        window = self.driver.get_window_size()
        x = window["width"] // 2
        for _ in range(max_swipes + 1):
            # The app currently exposes the requested fifth Connect button as
            # instance(4).  If it is not present, use any visible Connect item.
            for locator in (self.CONNECT_BUTTON, self.ANY_CONNECT_BUTTON):
                for button in self.driver.find_elements(*locator):
                    try:
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            return
                    except Exception:
                        # Native rows can redraw while the list scrolls.
                        continue
            self.driver.swipe(x, int(window["height"] * 0.82), x, int(window["height"] * 0.35), 500)

        raise AssertionError("No Connect button was found after scrolling Discover")

    def visible_ui_signatures(self) -> set[str]:
        """Return a current, non-empty UI snapshot for the selected tab."""
        root = ElementTree.fromstring(self.driver.page_source)
        signatures = {
            "|".join(node.attrib.get(a, "") for a in ("text", "content-desc", "resource-id", "class", "bounds"))
            for node in root.iter()
            if node.attrib.get("displayed", "true").lower() == "true"
        }
        assert signatures, "No UI elements are visible in the selected My Connections tab"
        return signatures

    def audit_visible_ui_to_end(self, max_swipes: int = 12) -> set[str]:
        """Verify a tab renders and scroll it until its contents stop changing."""
        seen: set[str] = set()
        unchanged_swipes = 0
        window = self.driver.get_window_size()
        x = window["width"] // 2
        for _ in range(max_swipes):
            prior_size = len(seen)
            seen.update(self.visible_ui_signatures())
            self.driver.swipe(x, int(window["height"] * 0.82), x, int(window["height"] * 0.30), 500)
            seen.update(self.visible_ui_signatures())
            unchanged_swipes = unchanged_swipes + 1 if len(seen) == prior_size else 0
            if unchanged_swipes >= 2:
                break
        return seen

    def scroll_to_top(self, max_swipes: int = 12) -> None:
        """Restore the tab to its top before selecting another tab."""
        window = self.driver.get_window_size()
        x = window["width"] // 2
        unchanged_swipes = 0
        for _ in range(max_swipes):
            before = self.visible_ui_signatures()
            self.driver.swipe(x, int(window["height"] * 0.30), x, int(window["height"] * 0.82), 500)
            after = self.visible_ui_signatures()
            unchanged_swipes = unchanged_swipes + 1 if after == before else 0
            if unchanged_swipes >= 2:
                return