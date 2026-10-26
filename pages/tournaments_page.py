import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from appium.webdriver.common.appiumby import AppiumBy


class TournamentsPage:

    def __init__(self, driver):
        self.driver = driver

    # -- internal helpers -------------------------------------------------

    def _by_id(self, label, timeout=20):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, label))
        )

    def _by_uiautomator(self, selector, timeout=20):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((AppiumBy.ANDROID_UIAUTOMATOR, selector))
        )

    def _by_description_contains(self, text, timeout=20):
        """Return a clickable control whose Android content description contains text."""
        return self._by_uiautomator(
            f'new UiSelector().descriptionContains("{text}")', timeout
        )

    def _edit_text(self, instance, timeout=20):
        return self._by_uiautomator(
            f'new UiSelector().className("android.widget.EditText").instance({instance})',
            timeout,
        )

    def _fill_edit_text(self, instance, value):
        # This app's EditTexts silently ignore send_keys() unless the field
        # is explicitly clicked first, and re-finding after click() avoids
        # stale-element errors once the keyboard reshuffles the layout.
        field = self._edit_text(instance)
        field.click()
        field = self._edit_text(instance)
        field.send_keys(value)

    def dismiss_keyboard(self, stable_label):
        # Never tap a hardcoded coordinate to blur a field: once the keyboard
        # opens, the page scrolls and coordinates go stale. Clicking a known
        # label by accessibility id resolves its live on-screen position.
        self._by_id(stable_label).click()

    def scroll_form_down(self):
        """Scroll the wizard's content pane without relying on stale coordinates."""
        self.driver.execute_script(
            "mobile: scrollGesture",
            {"left": 100, "top": 760, "width": 880, "height": 1000,
             "direction": "down", "percent": 0.8},
        )

    def fill_field_by_hint(self, hint, value):
        """Fill a current visible input by its stable Android hint text."""
        fields = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
        field = next(field for field in fields if field.get_attribute("hint") == hint)
        field.click()
        field.clear()
        field.send_keys(value)

    # -- nav / entry point --------------------------------------------------

    def click_tournaments_nav(self):
        # The bottom navigation button exposes "Tournaments\nTournaments" on
        # current builds, so an exact accessibility-id lookup is not stable.
        self._by_description_contains("Tournaments").click()

    def click_here_button(self):
        # The entry card was renamed from "Click here" to "Create tournament".
        self._by_description_contains("Create tournament").click()

    # -- Create Tournament modal --------------------------------------------

    def select_single_tournament(self):
        self._by_description_contains("Single Tournament").click()

    def click_modal_next(self):
        self._by_id("NEXT").click()

    # -- Tab 1: Basic Details ------------------------------------------------

    def enter_tournament_name(self, name):
        self._fill_edit_text(0, name)

    def select_sport(self, sport):
        # A resumed draft exposes the selected sport instead of the picker.
        if not self.driver.find_elements(AppiumBy.ACCESSIBILITY_ID, sport):
            self._by_id("Choose a sport").click()
            time.sleep(1)
            self._by_id(sport).click()
        # Selecting a sport re-composes the dependent match-type buttons.
        time.sleep(1)

    def select_tournament_type(self, tournament_type):
        self._by_id(tournament_type).click()

    def select_match_type(self, match_type):
        # This control is rendered immediately below the tournament-type
        # explanation and is often below the viewport on physical devices.
        self.scroll_form_down()
        self._by_id(match_type).click()

    def select_age_group(self, age_group):
        self._by_id(age_group).click()

    def select_category(self, category):
        self._by_id(category).click()

    def select_area(self, area):
        self._by_id(area).click()

    def select_state(self, state):
        self._by_uiautomator(
            'new UiSelector().description("Select Here").instance(0)'
        ).click()
        time.sleep(1)
        self._by_id(state).click()

    def select_district(self, district):
        self._by_uiautomator(
            'new UiSelector().description("Select Here").instance(0)'
        ).click()
        time.sleep(1)
        self._by_id(district).click()

    def enter_city(self, city):
        self._fill_edit_text(0, city)

    def enter_prizes(self, first=None, second=None, third=None):
        # Prize fields sit below the keyboard fold and unmount from the
        # accessibility tree until scrolled/focused into view one at a time.
        if first:
            self._fill_edit_text(1, first)
        if second:
            self._fill_edit_text(2, second)
        if third:
            self._fill_edit_text(3, third)

    def click_basic_details_next(self):
        self._by_id("Save & continue").click()

    # -- Current eight-step wizard: recorded Step 1 -----------------------

    def complete_current_basic_details(self, name, state, district, city):
        """Complete the required fields on the live Basic details wizard page."""
        self.enter_tournament_name(name)
        # The keyboard shrinks the wizard viewport and makes the option rows
        # non-interactable on some devices.
        self.driver.press_keycode(4)
        self.select_sport("FootBall")
        self.select_tournament_type("Knockout")
        self.select_match_type("Team")
        self.select_age_group("Open")
        self.scroll_form_down()
        self.select_category("Mixed")
        self.select_area("District")
        self.scroll_form_down()
        self._by_id("Select state").click()
        self._by_id(state).click()
        self._by_id("Select district").click()
        self._by_id(district).click()
        self.fill_field_by_hint("Enter city or town", city)
        self.driver.press_keycode(4)  # hide keyboard; do not navigate the wizard
        self._by_id("Save & continue").click()

    def upload_banner_manually(self, wait_seconds=20):
        # Image selection needs a real photo from the device gallery, which
        # cannot be scripted reliably; this pauses so it can be done by hand.
        print(f"Waiting {wait_seconds}s - manually tap 'Tap to select image' and pick a photo now...")
        time.sleep(wait_seconds)
        self._by_id("Save Photo").click()

    # -- Tab 2: Scheduling Details -------------------------------------------

    def select_tournament_start_date_today(self):
        self._by_uiautomator(
            'new UiSelector().description("Select Date").instance(0)'
        ).click()
        time.sleep(1)
        self._by_id("OK").click()

    def select_tournament_end_date(self, day_accessibility_id):
        # e.g. "7, Monday, September 7, 2026" - read the exact label off the
        # calendar for the month/day you navigate to.
        self._by_uiautomator(
            'new UiSelector().description("Select Date").instance(0)'
        ).click()
        time.sleep(1)
        self._by_id("Next month").click()
        time.sleep(1)
        self._by_id(day_accessibility_id).click()
        time.sleep(1)
        self._by_id("OK").click()

    def select_tournament_schedule(self, schedule):
        self._by_id("Choose Days").click()
        time.sleep(1)
        self._by_id(schedule).click()

    def enter_match_minutes(self, minutes):
        self._fill_edit_text(0, minutes)

    def select_team_size(self, team_size):
        # "Team Size" content-desc matches both a disabled label and the
        # real button; instance(1) targets the clickable button.
        self._by_uiautomator(
            'new UiSelector().description("Team Size").instance(1)'
        ).click()
        time.sleep(1)
        self._by_id(team_size).click()

    def select_teams_count(self, count):
        self._by_uiautomator(
            'new UiSelector().description("Teams Count").instance(0)'
        ).click()
        time.sleep(1)
        self._by_id(count).click()

    def _set_time_picker(self, hour, minute, meridiem):
        self._by_id("Switch to text input mode").click()
        time.sleep(1)
        self._fill_edit_text_clearing(0, hour)
        self._fill_edit_text_clearing(1, minute)
        self._by_id(meridiem).click()
        time.sleep(1)
        self._by_id("OK").click()

    def _fill_edit_text_clearing(self, instance, value):
        field = self._edit_text(instance)
        field.click()
        field = self._edit_text(instance)
        field.clear()
        field.send_keys(value)

    def select_ground_open_time(self, hour, minute, meridiem):
        self._by_id("Select time").click()
        time.sleep(1)
        self._set_time_picker(hour, minute, meridiem)

    def select_ground_close_time(self, hour, minute, meridiem):
        self._by_id("Select Time").click()
        time.sleep(1)
        self._set_time_picker(hour, minute, meridiem)

    def enter_grounds_count(self, count):
        self._fill_edit_text(0, count)

    def enter_referee_count(self, count):
        self._fill_edit_text(1, count)

    def enter_scorer_count(self, count):
        self._fill_edit_text(2, count)

    def click_scheduling_details_next(self):
        self._by_id("Next").click()
