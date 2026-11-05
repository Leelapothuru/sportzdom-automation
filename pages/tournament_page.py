"""Page object for the Sportzdom Single Tournament creation wizard.

Locators were verified with Appium Inspector on Sportzdom 1.4.6 (3-4 Nov 2026)
following the manually tested flow in reports/manual/.
"""

import logging
import re
import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import APP_PACKAGE
from test_data.tournament_data import OFFICIAL_TEST_USER, PROTECTED_OFFICIALS
from utils.helpers import (
    after_label,
    by_label,
    by_uia,
    by_xpath,
    calendar_label,
    description_contains,
)

log = logging.getLogger(__name__)

STEP_HEADER = re.compile(r"step (\d) of 8", re.IGNORECASE)
ATTENTION = re.compile(r"(\d+) fields? needs? your attention")


def official_name(description):
    """Name from a picker row such as 'user102\\nFootBall' or 'A\\nAchuth\\nFootBall'."""
    lines = description.split("\n")
    if len(lines) > 2 and len(lines[0]) == 1:
        return lines[1].strip()
    return lines[0].strip()


class TournamentsPage:
    # -- entry points ------------------------------------------------------
    TOURNAMENTS_NAV = description_contains("Tournaments")
    CREATE_TOURNAMENT = description_contains("Create tournament")
    MY_DRAFTS_TAB = by_label("My drafts")
    SINGLE_TOURNAMENT = description_contains("Single Tournament")
    TYPE_DIALOG_NEXT = by_label("NEXT")
    APP_LOCKED = by_label("Unlock Sportzdom")

    # -- wizard chrome -----------------------------------------------------
    PRIMARY_BUTTONS = ("Save & back to review", "Save & continue", "Continue")

    # -- Step 1: Basic details ---------------------------------------------
    NAME_FIELD = after_label("Tournament name *", element="android.widget.EditText")
    NAME_LIMIT_HINT = by_label("Up to 60 characters")
    SPORT_FIELD = after_label("Sport *")
    SPORT_NOT_CHOSEN = by_label("Choose a sport")
    SELECT_STATE = by_label("Select state")
    SELECT_DISTRICT = by_label("Select district")
    CITY_FIELD = after_label("City / town *", element="android.widget.EditText")
    PRIZE_TOO_HIGH = by_label("Cannot be more than the 1st prize")

    # -- date and time pickers ---------------------------------------------
    CALENDAR_OK = by_label("OK")
    CALENDAR_CANCEL = by_label("CANCEL")
    NEXT_MONTH = by_label("Next month")
    TIME_TEXT_MODE = by_label("Switch to text input mode")
    TIME_HOUR = by_xpath('//android.widget.EditText[@hint="Hour"]')
    TIME_MINUTE = by_xpath('//android.widget.EditText[@hint="Minute"]')

    # -- Step 2: Schedule --------------------------------------------------
    START_DATE = after_label("Ends on *", 1)
    END_DATE = after_label("Ends on *", 2)
    MATCH_MINUTES = after_label("Match duration (minutes) *", element="android.widget.EditText")
    GROUND_OPENS = after_label("Ground closes *", 1)
    GROUND_CLOSES = after_label("Ground closes *", 2)
    # The count is the node immediately before its label. Appium's XPath engine
    # resolves preceding-sibling::*[1] to the first sibling, not the nearest,
    # so match the node whose next sibling is the label instead.
    TOURNAMENT_DAYS = by_xpath('//*[following-sibling::*[1][@content-desc="Tournament days"]]')
    PLAYING_DAYS = by_xpath('//*[following-sibling::*[1][@content-desc="Playing days"]]')

    # -- Step 3: Registration ----------------------------------------------
    REGISTRATION_OPENS = after_label("Closes on *", 1)
    REGISTRATION_CLOSES = after_label("Closes on *", 2)
    ENTRY_FEE = after_label("Fee per team (optional)", element="android.widget.EditText")

    # -- Step 4: Officials -------------------------------------------------
    PICKER_SEARCH = by_xpath('//android.widget.EditText[@hint="Search name or phone number"]')
    PICKER_HEADER = description_contains("TOURNAMENT OFFICIALS")
    PICKER_ROWS = (AppiumBy.CLASS_NAME, "android.widget.CheckBox")
    PICKER_CONFIRM = by_uia(
        'new UiSelector().className("android.widget.Button").descriptionMatches("Add [0-9]+ .*")'
    )
    PICKER_NO_MATCH = by_uia('new UiSelector().descriptionStartsWith("No matching")')
    GROUND_AREA = description_contains("Choose where to browse grounds")
    GROUND_ROWS = by_xpath('//android.widget.ScrollView/android.view.View[@clickable="true"]')
    GROUND_SUBMIT = by_label("Submit")
    GROUNDS_REQUIRED = by_label("Add grounds")
    CONFIRM_REMOVE = by_label("Remove")

    # -- Popups ------------------------------------------------------------
    # Shown after sign-in when one of the account's tournaments is past its start date.
    OVERDUE_POPUP = by_uia('new UiSelector().descriptionStartsWith("Your tournament is overdue")')
    REMIND_ME_LATER = by_label("Remind Me Later")

    # -- Step 5: Rules -----------------------------------------------------
    # The Step 5 button has been seen labelled both "Add rule" and "Add rules".
    # The picker's confirm button (before anything is ticked) can read "Add rules"
    # too; the picker is told apart by its title.
    ADD_RULE = by_uia('new UiSelector().className("android.widget.Button").descriptionMatches("Add rules?")')
    RULES_SCREEN = description_contains("tick the ones you need")
    # Confirm button reads "Add 2 rules" once rules are ticked.
    RULES_CONFIRM = by_uia('new UiSelector().className("android.widget.Button").descriptionMatches("Add [0-9]+ rules?")')

    # -- Step 6: Budget ----------------------------------------------------
    ADD_EXPENSE = by_label("Add expense")
    EXPENSE_SUBMIT = by_xpath('(//android.widget.Button[@content-desc="Add expense"])[last()]')
    EXPENSE_ITEM = by_xpath('//android.widget.EditText[@hint="e.g. Balls, trophies, ground rent"]')
    EXPENSE_QUANTITY = by_xpath("(//android.widget.EditText)[2]")
    EXPENSE_COST = by_xpath("(//android.widget.EditText)[3]")
    EXPENSE_ITEM_REQUIRED = description_contains("Enter what the expense is for")
    EXPENSE_COST_REQUIRED = description_contains("Enter the cost")
    ESTIMATED_TOTAL = after_label("Estimated total")

    # -- Step 8: Review and creation ---------------------------------------
    CREATE_BUTTON = by_label("Create tournament")
    CREATE_DIALOG = by_label("Create tournament?")
    CONFIRM_CREATE = by_label("Create")
    CANCEL_CREATE = by_label("Cancel")
    SAVED_TITLE = by_label("Tournament saved")
    # The message sits inside an unlabelled container, so take the first
    # described element after the title rather than the next node.
    SAVED_MESSAGE = by_xpath(
        '(//*[@content-desc="Tournament saved"]/following::*[string-length(@content-desc) > 0])[1]'
    )
    DONE = by_label("Done")
    RESUME_DRAFT = by_label("Resume Tournament")

    def __init__(self, driver, timeout=20):
        self.driver = driver
        self.timeout = timeout

    # -- generic helpers ---------------------------------------------------

    def wait_for(self, locator, timeout=None):
        return WebDriverWait(self.driver, timeout or self.timeout).until(
            EC.presence_of_element_located(locator),
            message=f"Element not found: {locator[1]}",
        )

    def click(self, locator, timeout=None):
        WebDriverWait(self.driver, timeout or self.timeout).until(
            EC.element_to_be_clickable(locator),
            message=f"Element not clickable: {locator[1]}",
        ).click()

    def is_present(self, locator):
        return bool(self.driver.find_elements(*locator))

    def description(self, locator):
        return self.wait_for(locator).get_attribute("content-desc")

    def _swipe(self, direction, percent=0.7):
        """Scroll the visible content area; returns False once the screen stops changing."""
        # scrollGesture's own "can scroll more" result is unreliable on this
        # app's Compose screens, so compare the hierarchy before and after.
        before = self.driver.page_source
        size = self.driver.get_window_size()
        self.driver.execute_script(
            "mobile: scrollGesture",
            {
                "left": int(size["width"] * 0.1),
                "top": int(size["height"] * 0.3),
                "width": int(size["width"] * 0.8),
                "height": int(size["height"] * 0.4),
                "direction": direction,
                "percent": percent,
            },
        )
        return self.driver.page_source != before

    def scroll_to(self, locator, max_swipes=8, directions=("down", "up")):
        """Find an element on a scrolling form, searching down first and then up."""
        for direction in directions:
            for _ in range(max_swipes):
                found = self.driver.find_elements(*locator)
                if found:
                    return self._clear_of_footer(locator, found[0])
                if not self._swipe(direction):
                    break
        found = self.driver.find_elements(*locator)
        if found:
            return self._clear_of_footer(locator, found[0])
        raise NoSuchElementException(f"Not found after scrolling: {locator[1]}")

    def _clear_of_footer(self, locator, element):
        # Elements just above the fixed Continue footer report clipped bounds;
        # nudge them up so a tap cannot land on the footer instead.
        try:
            rect = element.rect
        except StaleElementReferenceException:
            # The screen re-rendered between finding and measuring the element.
            element = self.wait_for(locator)
            rect = element.rect
        if rect["y"] + rect["height"] > self.driver.get_window_size()["height"] * 0.78:
            self._swipe("down", percent=0.3)
            return self.wait_for(locator)
        return element

    def wait_until_stable(self, timeout=10, interval=1.0):
        """Wait until the widget hierarchy stops changing (lists finished loading).

        Returns without failing if the screen keeps changing for the whole timeout.
        """
        previous = self.driver.page_source
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            time.sleep(interval)
            current = self.driver.page_source
            if current == previous:
                return
            previous = current
        log.info("Screen still changing after %ss; continuing", timeout)

    def hide_keyboard(self):
        # Pressing Back without an open keyboard would leave the wizard step.
        if self.driver.is_keyboard_shown():
            self.driver.back()

    def fill(self, locator, value, hide_keyboard=True):
        # Fields ignore send_keys until clicked, and the keyboard re-lays out
        # the form, so the element is located again after the click.
        self.scroll_to(locator).click()
        field = self.wait_for(locator)
        field.clear()
        field.send_keys(value)
        if hide_keyboard:
            self.hide_keyboard()

    def field_text(self, locator):
        return self.scroll_to(locator).get_attribute("text")

    def has_message(self, text):
        try:
            self.scroll_to(description_contains(text), max_swipes=6)
            return True
        except NoSuchElementException:
            return False

    # -- wizard state ------------------------------------------------------

    def current_step(self):
        """Visible wizard step number, or None outside the wizard."""
        match = STEP_HEADER.search(self.driver.page_source)
        return int(match.group(1)) if match else None

    def wait_for_step(self, step, timeout=30):
        # Saving a step takes a few seconds on the current build.
        WebDriverWait(self.driver, timeout).until(
            lambda _: self.current_step() == step,
            message=f"Wizard did not reach step {step} (now on {self.current_step()})",
        )

    def attention_count(self):
        """Number from the header's 'N fields need your attention', 0 when absent."""
        match = ATTENTION.search(self.driver.page_source)
        return int(match.group(1)) if match else 0

    def save_step(self):
        for label in self.PRIMARY_BUTTONS:
            if self.is_present(by_label(label)):
                self.click(by_label(label))
                return
        raise NoSuchElementException("No Save/Continue button on the current step")

    def continue_to(self, step):
        self.save_step()
        self.wait_for_step(step)

    # -- entry points ------------------------------------------------------

    def open_type_dialog(self):
        self.click(self.TOURNAMENTS_NAV)
        # The Tournaments screen re-renders while its lists load, which makes
        # elements found too early go stale.
        self.wait_until_stable()
        # The Tournaments screen keeps its scroll position (e.g. scrolled down
        # to a draft card after a creation), which can hide the entry card.
        self.scroll_to(self.CREATE_TOURNAMENT, directions=("up", "down")).click()
        self.wait_for(self.SINGLE_TOURNAMENT)

    def is_type_dialog_next_enabled(self):
        return self.wait_for(self.TYPE_DIALOG_NEXT).get_attribute("enabled") == "true"

    def choose_single_tournament(self):
        self.click(self.SINGLE_TOURNAMENT)
        self.click(self.TYPE_DIALOG_NEXT)
        self.wait_for_step(1)

    def open_create_wizard(self):
        self.open_type_dialog()
        self.choose_single_tournament()

    def open_my_drafts(self):
        self.click(self.TOURNAMENTS_NAV)
        self.scroll_to(self.MY_DRAFTS_TAB, directions=("up", "down")).click()

    def _assert_unlocked(self):
        # A restarted app opens on a fingerprint lock that tests cannot pass,
        # which is why the tests never restart the app themselves.
        assert not self.is_present(self.APP_LOCKED), (
            "Sportzdom is showing its fingerprint lock ('Unlock Sportzdom'). "
            "Unlock the app on the device, then run the tests again."
        )

    def on_main_screen(self):
        # Checking only for the bottom navigation is not enough: it can still
        # match for a moment while a wizard step is opening.
        return self.current_step() is None and self.is_present(self.TOURNAMENTS_NAV)

    def leave_wizard(self, max_presses=3):
        """Go back from the wizard (or a dialog) to the screen with bottom navigation.

        Uses the Back button only; the app is never restarted.
        """
        self._assert_unlocked()
        self.hide_keyboard()
        for _ in range(max_presses):
            if self.on_main_screen():
                return
            self.driver.back()
            try:
                WebDriverWait(self.driver, 5).until(lambda _: self.on_main_screen())
                return
            except TimeoutException:
                self._assert_unlocked()
        raise AssertionError(
            "Back did not return to the main screen; the app may be showing a dialog. "
            "See the failure screenshot."
        )

    def dismiss_overdue_popup(self):
        """Close the 'Your tournament is overdue' popup, which hides the bottom navigation."""
        if not self.is_present(self.OVERDUE_POPUP):
            return
        self.click(self.REMIND_ME_LATER)
        self.wait_until_gone(self.OVERDUE_POPUP)

    def ensure_main_screen(self):
        """Start from a screen with bottom navigation without restarting the app."""
        self._assert_unlocked()
        self.dismiss_overdue_popup()
        try:
            WebDriverWait(self.driver, 10).until(lambda _: self.on_main_screen())
        except TimeoutException:
            step = self.current_step()
            if step is not None:
                # Inside the form, Back moves to the previous step and changes the
                # saved draft, so never press it here.
                raise AssertionError(
                    f"A tournament form is open at step {step} of 8 (left by an earlier "
                    "failed flow or a manual session). Close it on the device and run again."
                ) from None
            log.info("App is not on a main screen; going back to it")
            self.leave_wizard()

    # -- Step 1: Basic details ---------------------------------------------

    def enter_name(self, name):
        self.fill(self.NAME_FIELD, name)

    def name_value(self):
        return self.field_text(self.NAME_FIELD)

    def sport_is_selected(self):
        return not self.is_present(self.SPORT_NOT_CHOSEN)

    def select_sport(self, sport):
        if self.sport_is_selected():
            return
        self.scroll_to(self.SPORT_FIELD).click()
        self.click(by_uia(
            f'new UiSelector().className("android.widget.Button").description("{sport}")'
        ))
        WebDriverWait(self.driver, self.timeout).until(
            lambda _: self.sport_is_selected(), message="Sport selection was not applied"
        )

    def choose(self, group, value):
        """Tap an option button such as 'Age group: U-19' unless already selected."""
        option = self.scroll_to(by_label(f"{group}: {value}"))
        if option.get_attribute("selected") != "true":
            option.click()

    def is_option_selected(self, group, value):
        return self.scroll_to(by_label(f"{group}: {value}")).get_attribute("selected") == "true"

    def select_location(self, state, district, city):
        self.scroll_to(self.SELECT_STATE).click()
        self.click(by_label(state))
        self.scroll_to(self.SELECT_DISTRICT).click()
        self.click(by_label(district))
        self.fill(self.CITY_FIELD, city)

    def prize_field(self, position):
        """position 1 = 1st prize, 2 = 2nd prize, 3 = 3rd prize."""
        return after_label("Prize money", position, "android.widget.EditText")

    def enter_prize(self, position, amount):
        self.fill(self.prize_field(position), amount)

    def complete_basic_details(self, data, save=True):
        self.enter_name(data.name)
        self.select_sport(data.sport)
        self.choose("Tournament type", data.tournament_type)
        self.choose("Match type", data.match_type)
        self.choose("Age group", data.age_group)
        self.choose("Category", data.category)
        self.choose("Level", data.level)
        self.select_location(data.state, data.district, data.city)
        if data.first_prize:
            self.enter_prize(1, data.first_prize)
        if data.second_prize:
            self.enter_prize(2, data.second_prize)
        if save:
            self.continue_to(2)

    # -- date / time pickers -----------------------------------------------

    def _show_calendar_day(self, day, max_months=14):
        """Advance the open date picker to the month containing day."""
        label = by_uia(f'new UiSelector().descriptionStartsWith("{calendar_label(day)}")')
        for _ in range(max_months):
            found = self.driver.find_elements(*label)
            if found:
                return found[0]
            next_month = self.wait_for(self.NEXT_MONTH)
            if next_month.get_attribute("enabled") != "true":
                return None
            next_month.click()
        return None

    def calendar_day_enabled(self, day):
        """Whether day can be picked in the open date picker (unreachable counts as disabled)."""
        cell = self._show_calendar_day(day)
        return cell is not None and cell.get_attribute("enabled") == "true"

    def open_date_field(self, field):
        self.scroll_to(field).click()
        self.wait_for(self.CALENDAR_OK)

    def pick_date(self, field, day):
        self.open_date_field(field)
        cell = self._show_calendar_day(day)
        assert cell is not None, f"{calendar_label(day)} is not offered by the date picker"
        cell.click()
        self.click(self.CALENDAR_OK)

    def cancel_date_picker(self):
        self.click(self.CALENDAR_CANCEL)

    def set_time(self, field, hour, meridiem, minute="00"):
        self.scroll_to(field).click()
        self.click(self.TIME_TEXT_MODE)
        self.fill(self.TIME_HOUR, hour, hide_keyboard=False)
        self.fill(self.TIME_MINUTE, minute, hide_keyboard=False)
        self.click(by_label(meridiem))
        self.click(self.CALENDAR_OK)

    # -- Step 2: Schedule --------------------------------------------------

    def set_count(self, kind, value):
        """kind is 'grounds', 'referees' or 'scorers'."""
        self.fill(by_xpath(f'//android.widget.EditText[contains(@hint,"Number of {kind}")]'), str(value))

    def schedule_day_counts(self):
        tournament_days = self.scroll_to(self.TOURNAMENT_DAYS).get_attribute("content-desc")
        playing_days = self.scroll_to(self.PLAYING_DAYS).get_attribute("content-desc")
        return int(tournament_days), int(playing_days)

    def complete_schedule(self, data, save=True):
        self.pick_date(self.START_DATE, data.start)
        self.pick_date(self.END_DATE, data.end)
        self.choose("Playing days", data.playing_days)
        self.fill(self.MATCH_MINUTES, data.match_minutes)
        self.choose("Players per side", data.players_per_side)
        self.choose("Expected teams", data.expected_teams)
        self.set_time(self.GROUND_OPENS, *data.ground_opens)
        self.set_time(self.GROUND_CLOSES, *data.ground_closes)
        self.set_count("grounds", data.grounds)
        self.set_count("referees", data.referees)
        self.set_count("scorers", data.scorers)
        if save:
            self.continue_to(3)

    # -- Step 3: Registration ----------------------------------------------

    def complete_registration(self, data, save=True):
        self.pick_date(self.REGISTRATION_OPENS, data.registration_opens)
        self.pick_date(self.REGISTRATION_CLOSES, data.registration_closes)
        if data.entry_fee:
            self.fill(self.ENTRY_FEE, data.entry_fee)
        if save:
            self.continue_to(4)

    # -- Step 4: Officials -------------------------------------------------

    def section_counter(self, section):
        """Counter text under an Officials section, e.g. '2 of 2 added'."""
        return self.scroll_to(after_label(section)).get_attribute("content-desc")

    def open_official_picker(self, role):
        """role is 'referee' or 'scorer'."""
        self.scroll_to(by_label(f"Add {role}")).click()
        self.wait_for(self.PICKER_SEARCH)

    def close_official_picker(self):
        """Leave the picker without adding anyone."""
        self.hide_keyboard()
        self.driver.back()
        self.wait_until_gone(self.PICKER_HEADER)

    def search_officials(self, text):
        self.fill(self.PICKER_SEARCH, text)

    def picker_confirm_enabled(self, role):
        button = self.wait_for(by_uia(
            f'new UiSelector().className("android.widget.Button").descriptionContains("{role}")'
        ))
        return button.get_attribute("enabled") == "true"

    def _select_test_users(self, count, max_swipes=10):
        """Tick unchecked picker rows for test accounts only (see OFFICIAL_TEST_USER)."""
        selected = []
        for _ in range(max_swipes):
            clicked = False
            for row in self.driver.find_elements(*self.PICKER_ROWS):
                try:
                    name = official_name(row.get_attribute("content-desc"))
                    # Rows for people already on the tournament are disabled ("Already added").
                    unchecked = (row.get_attribute("checked") != "true"
                                 and row.get_attribute("enabled") == "true")
                except StaleElementReferenceException:
                    break
                if name in PROTECTED_OFFICIALS or not OFFICIAL_TEST_USER.fullmatch(name):
                    continue
                if unchecked and name not in selected:
                    row.click()
                    selected.append(name)
                    log.info("Selected official %s", name)
                    clicked = True
                    break  # the list re-renders after each tick
            if len(selected) == count:
                return selected
            if not clicked and not self._swipe("down"):
                break
        raise AssertionError(f"Only found {len(selected)} of {count} test-account officials: {selected}")

    def wait_until_gone(self, locator, timeout=None):
        WebDriverWait(self.driver, timeout or self.timeout).until(
            lambda _: not self.is_present(locator),
            message=f"Still showing: {locator[1]}",
        )

    def add_officials(self, role, count):
        self.open_official_picker(role)
        names = self._select_test_users(count)
        self.click(self.PICKER_CONFIRM)
        # The picker stays open showing "Adding referees…" while invitations
        # are sent, and Officials then reopens scrolled to the top, so wait
        # for the whole picker screen to close rather than for an Add button.
        self.wait_until_gone(self.PICKER_HEADER, timeout=60)
        return names

    def add_grounds(self, state, count):
        self.scroll_to(by_label("Add ground")).click()
        area = self.wait_for(self.GROUND_AREA)
        if not area.get_attribute("content-desc").startswith(state):
            area.click()
            self.click(by_label(state))
        self.wait_for(self.GROUND_ROWS)
        for index in range(count):
            self.driver.find_elements(*self.GROUND_ROWS)[index].click()
        self.click(self.GROUND_SUBMIT)
        self.wait_until_gone(self.GROUND_AREA)

    def complete_officials(self, data, save=True):
        self.add_officials("referee", data.referees)
        self.add_officials("scorer", data.scorers)
        self.add_grounds(data.state, data.grounds)
        if save:
            self.continue_to(5)

    # -- Step 5: Rules -----------------------------------------------------

    def _tick(self, checkbox, timeout=15):
        """Tick a checkbox once and wait for the tick to show.

        A second tap would toggle the selection back off, so never retry the tap.
        """
        self.scroll_to(checkbox).click()
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda _: self.wait_for(checkbox).get_attribute("checked") == "true"
            )
        except TimeoutException:
            raise AssertionError(
                f"Checkbox not ticked {timeout}s after one tap: {checkbox[1]}"
            ) from None

    def add_rules(self, codes):
        """Tick the given rule codes on the Add rules screen and confirm them."""
        self.scroll_to(self.ADD_RULE).click()
        self.wait_for(self.RULES_SCREEN)
        # Each rule's checkbox is labelled with its code, e.g. "FB01".
        checkboxes = [by_xpath(f'//android.widget.CheckBox[@content-desc="{code}"]') for code in codes]
        self.wait_for(checkboxes[0])
        for checkbox in checkboxes:
            self._tick(checkbox)
        # "Add 1 rule" / "Add 2 rules"
        count = f"{len(codes)} rule" + ("" if len(codes) == 1 else "s")
        confirm = self.wait_for(self.RULES_CONFIRM)
        label = confirm.get_attribute("content-desc")
        assert label == f"Add {count}", (
            f"Confirm button reads {label!r} after ticking {list(codes)}"
        )
        confirm.click()
        try:
            self.wait_for(by_label(count))
        except TimeoutException:
            raise AssertionError(
                f"Rules {list(codes)} were confirmed but Step 5 does not show "
                f"'{count}' - possible app defect"
            ) from None
        missing = [code for code in codes if not self.has_message(code)]
        assert not missing, f"Rules missing from the Step 5 list: {missing}"

    # -- Step 6: Budget ----------------------------------------------------

    def open_expense_sheet(self):
        self.click(self.ADD_EXPENSE)
        self.wait_for(self.EXPENSE_ITEM)

    def fill_expense(self, item, quantity, cost):
        self.fill(self.EXPENSE_ITEM, item)
        self.fill(self.EXPENSE_QUANTITY, quantity)
        self.fill(self.EXPENSE_COST, cost)

    def submit_expense(self):
        self.click(self.EXPENSE_SUBMIT)

    def add_expense(self, item, quantity, cost):
        self.open_expense_sheet()
        self.fill_expense(item, quantity, cost)
        self.submit_expense()
        self.wait_for(by_label(item))

    def estimated_total(self):
        return self.description(self.ESTIMATED_TOTAL)

    # -- Step 8: Review and creation ---------------------------------------

    def review_value(self, label):
        """Value shown next to a Review row label such as 'Name' or 'Prizes'."""
        return self.scroll_to(after_label(label)).get_attribute("content-desc")

    def edit_review_section(self, section):
        """section as labelled on its Edit button, e.g. 'basic details', 'schedule'."""
        self.scroll_to(by_label(f"Edit {section}")).click()

    def open_create_dialog(self):
        self.click(self.CREATE_BUTTON)
        self.wait_for(self.CREATE_DIALOG)

    def cancel_create(self):
        self.click(self.CANCEL_CREATE)
        # While the dialog animates away the page underneath is not exposed,
        # so the step header only reappears once the dialog has closed.
        self.wait_until_gone(self.CREATE_DIALOG)

    def confirm_create(self):
        """Create the tournament and return the confirmation message."""
        self.click(self.CONFIRM_CREATE)
        self.wait_for(self.SAVED_TITLE, timeout=40)
        return self.description(self.SAVED_MESSAGE)

    def finish(self):
        self.click(self.DONE)

    # -- My drafts ---------------------------------------------------------

    def draft_card(self, name):
        return self.scroll_to(description_contains(name)).get_attribute("content-desc")

    def resume_draft(self, name):
        card = self.scroll_to(description_contains(name)).rect
        for button in self.driver.find_elements(*self.RESUME_DRAFT):
            centre = button.rect["y"] + button.rect["height"] / 2
            if card["y"] <= centre <= card["y"] + card["height"]:
                button.click()
                return
        raise NoSuchElementException(f"No Resume Tournament button on the draft card for {name}")
