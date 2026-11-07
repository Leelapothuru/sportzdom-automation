import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.configuration import AppiumConfiguration
from utils.football_sch_texts import FootballScheduleTexts as Texts
from utils.waits import wait_until


class FootballSchedulePage:
    PLAY_BUTTON = (
        AppiumBy.XPATH,
        '//android.widget.Button[@content-desc="%s"]' % Texts.PLAY_BUTTON,
    )
    FOOTBALL_CARD = (
        AppiumBy.XPATH,
        '//android.widget.ImageView[@content-desc="%s"]' % Texts.FOOTBALL,
    )
    START_MATCH_BUTTON = (AppiumBy.ACCESSIBILITY_ID, Texts.START_MATCH)
    SCHEDULE_LATER_CARD = (
        AppiumBy.XPATH,
        '//android.view.View[@content-desc="%s"]' % Texts.SCHEDULE_LATER,
    )
    CONTINUE_TO_SCHEDULE_BUTTON = (
        AppiumBy.ACCESSIBILITY_ID,
        Texts.CONTINUE_TO_SCHEDULE,
    )
    TEAM_ROWS = (
        AppiumBy.XPATH,
        "//*[@clickable='true' and contains(@content-desc, '%s')]"
        % Texts.TEAM_MEMBERS_MARKER,
    )
    SELECT_TEAM_BUTTON = (
        AppiumBy.XPATH,
        '//android.widget.Button[@content-desc="%s"]' % Texts.SELECT_TEAM,
    )
    SEARCH_FIELD = (AppiumBy.XPATH, "//android.widget.EditText")
    PLAYER_COUNT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, Texts.FIVE_PLAYERS)
    DURATION_FIELD = (AppiumBy.XPATH, "//android.widget.EditText")
    DATE_TIME_SECTION = (
        AppiumBy.XPATH,
        '//android.view.View[@content-desc="%s"]' % Texts.DATE_TIME_PROMPT,
    )
    CALENDAR_TITLE = (
        AppiumBy.XPATH,
        "//android.widget.Button[starts-with(@content-desc, '%s')]"
        % Texts.SELECT_YEAR_PREFIX,
    )
    HOUR_FIELD = (
        AppiumBy.XPATH,
        "//android.widget.EditText[@hint='%s']" % Texts.HOUR_HINT,
    )
    MINUTE_FIELD = (
        AppiumBy.XPATH,
        "//android.widget.EditText[@hint='%s']" % Texts.MINUTE_HINT,
    )
    SAVED_DATE_TIME_SECTION = (
        AppiumBy.XPATH,
        "//android.view.View[contains(@content-desc, '%s')]" % Texts.DATE_TIME,
    )
    VENUE_SECTION = (
        AppiumBy.XPATH,
        "//android.view.View[starts-with(@content-desc, '%s')]"
        % Texts.VENUE_PREFIX,
    )
    SELECT_OFFICIAL_BUTTON = (
        AppiumBy.ACCESSIBILITY_ID,
        Texts.SELECT_OFFICIAL,
    )
    OFFICIAL_BACK_BUTTON = (
        AppiumBy.XPATH,
        '//android.widget.FrameLayout[@resource-id="android:id/content"]'
        '/android.widget.FrameLayout/android.widget.FrameLayout'
        '/android.view.View/android.view.View/android.view.View'
        '/android.view.View/android.view.View[1]/android.widget.Button',
    )
    SCHEDULE_MATCH_BUTTON = (
        AppiumBy.ACCESSIBILITY_ID,
        Texts.SCHEDULE_MATCH,
    )
    CONFIRMATION_BUTTON = (
        AppiumBy.ACCESSIBILITY_ID,
        Texts.CONFIRM_OK,
    )
    DATE_TIME_CONFIRMATION_BUTTON = (
        AppiumBy.ACCESSIBILITY_ID,
        Texts.OK,
    )

    def __init__(self, driver):
        self.driver = driver

    @property
    def timeout(self):
        return AppiumConfiguration.from_env().wait_timeout

    def open_schedule_match_flow(self):
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.PLAY_BUTTON),
        ).click()
        self._scroll_down_until_football_found()
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.FOOTBALL_CARD),
        ).click()
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.START_MATCH_BUTTON),
        ).click()
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.SCHEDULE_LATER_CARD),
        ).click()
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.CONTINUE_TO_SCHEDULE_BUTTON),
        ).click()

    def select_gender(self):
        wait_until(
            self.driver,
            EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, Texts.GENDER)),
        ).click()

    def select_team(self, side, search_term=None, team_identifier=None):
        if side not in (Texts.YOUR_SIDE, Texts.OPPONENT):
            raise ValueError(Texts.UNSUPPORTED_TEAM_SIDE.format(side))
        self._click_team_select_button(side)

        if side == Texts.YOUR_SIDE:
            team = self._click_first_displayed_team()
            team_description = team.get_attribute("contentDescription") or ""
            team.click()
        else:
            if search_term is None or team_identifier is None:
                raise ValueError(Texts.OPPONENT_SELECTION_REQUIRES_DATA)
            search = WebDriverWait(
                self.driver,
                self.timeout,
                ignored_exceptions=(StaleElementReferenceException,),
            ).until(EC.element_to_be_clickable(self.SEARCH_FIELD))
            search.click()
            search.send_keys(search_term)
            team_locator = self._opponent_team_locator(team_identifier)
            team = wait_until(
                self.driver,
                EC.element_to_be_clickable(team_locator),
            )
            team_description = team.get_attribute("contentDescription") or ""
            team.click()

        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.SELECT_TEAM_BUTTON),
        ).click()

        if side == Texts.YOUR_SIDE:
            self.driver.back()
            wait_until(
                self.driver,
                EC.element_to_be_clickable(self._team_select_locator(Texts.OPPONENT)),
            )
        else:
            self._return_to_match_setup()

        return team_description

    def select_player_format(self):
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.PLAYER_COUNT_BUTTON),
        ).click()

    def set_duration(self, duration):
        self._scroll_until_visible(self.DURATION_FIELD, "up", "Duration field")
        field = wait_until(
            self.driver,
            EC.element_to_be_clickable(self.DURATION_FIELD),
        )
        field.click()
        field.clear()
        field.send_keys(str(duration))
        value = field.get_attribute("text")
        self._dismiss_keyboard()
        return value

    def set_match_start(self, match_start):
        self._scroll_until_visible(
            self.DATE_TIME_SECTION,
            "up",
            "Date and Time section",
        )
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.DATE_TIME_SECTION),
        ).click()

        month_year = match_start.strftime("%B %Y")
        calendar_title = wait_until(
            self.driver,
            EC.presence_of_element_located(self.CALENDAR_TITLE),
        )
        if month_year not in (
            calendar_title.get_attribute("contentDescription") or ""
        ):
            wait_until(
                self.driver,
                EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, Texts.NEXT_MONTH)),
            ).click()

        date_label = "%s, %s %d, %d" % (
            match_start.strftime("%A"),
            match_start.strftime("%B"),
            match_start.day,
            match_start.year,
        )
        date_locator = (
            AppiumBy.XPATH,
            "//android.widget.Button[contains(@content-desc, %s)]"
            % self._xpath_literal(date_label),
        )
        wait_until(
            self.driver,
            EC.element_to_be_clickable(date_locator),
        ).click()
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.DATE_TIME_CONFIRMATION_BUTTON),
        ).click()

        wait_until(
            self.driver,
            EC.element_to_be_clickable(
                (AppiumBy.ACCESSIBILITY_ID, Texts.SWITCH_TO_TEXT_INPUT)
            ),
        ).click()
        hour_field = wait_until(
            self.driver,
            EC.element_to_be_clickable(self.HOUR_FIELD),
        )
        hour_field.click()
        hour_field.clear()
        hour_field.send_keys(str(match_start.hour % 12 or 12))

        minute_field = wait_until(
            self.driver,
            EC.element_to_be_clickable(self.MINUTE_FIELD),
        )
        minute_field.click()
        minute_field.clear()
        minute_field.send_keys(match_start.strftime("%M"))

        expected_hour = str(match_start.hour % 12 or 12)
        actual_hour = hour_field.get_attribute("text")
        actual_minute = minute_field.get_attribute("text")
        period = Texts.AM if match_start.hour < 12 else Texts.PM
        period_button = wait_until(
            self.driver,
            EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, period)),
        )
        if period_button.get_attribute("checked") != "true":
            period_button.click()
        actual_period_selected = period_button.get_attribute("checked") == "true"

        if self.driver.is_keyboard_shown():
            self.driver.press_keycode(66)
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.DATE_TIME_CONFIRMATION_BUTTON),
        ).click()
        wait_until(
            self.driver,
            EC.presence_of_element_located(self.SAVED_DATE_TIME_SECTION),
        )

        return actual_hour, actual_minute, expected_hour, actual_period_selected

    def select_venue(self, search_term, expected_location):
        self._scroll_until_visible(self.VENUE_SECTION, "up", "Venue section")
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.VENUE_SECTION),
        ).click()
        search = wait_until(
            self.driver,
            EC.element_to_be_clickable(self.SEARCH_FIELD),
        )
        search.click()
        search.send_keys(search_term)
        self._dismiss_keyboard()
        venue_locator = (
            AppiumBy.XPATH,
            "//android.view.View[contains(@content-desc, %s) "
            "and contains(@content-desc, %s)]"
            % (
                self._xpath_literal(search_term),
                self._xpath_literal(expected_location),
            ),
        )
        venue = wait_until(
            self.driver,
            EC.element_to_be_clickable(venue_locator),
        )
        description = venue.get_attribute("contentDescription") or ""
        venue.click()
        return description

    def select_official(self, role, search_term, user_identifier):
        if role not in (Texts.REFEREE, Texts.SCORER):
            raise ValueError(Texts.UNSUPPORTED_OFFICIAL_ROLE.format(role))
        role_locator = (AppiumBy.ACCESSIBILITY_ID, role)
        if role == Texts.SCORER:
            self._scroll_until_visible(role_locator, "down", "Scorer button")

        wait_until(
            self.driver,
            EC.element_to_be_clickable(role_locator),
        ).click()

        if role == Texts.REFEREE:
            wait_until(
                self.driver,
                EC.element_to_be_clickable(self.CONFIRMATION_BUTTON),
            ).click()

        search = wait_until(
            self.driver,
            EC.element_to_be_clickable(self.SEARCH_FIELD),
        )
        search.click()
        search.clear()
        search.send_keys(search_term)

        official_locator = self._official_locator(user_identifier, role)
        official = wait_until(
            self.driver,
            EC.element_to_be_clickable(official_locator),
        )
        description = official.get_attribute("contentDescription") or ""
        official.click()
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.SELECT_OFFICIAL_BUTTON),
        ).click()

        if role == Texts.REFEREE:
            wait_until(
                self.driver,
                EC.element_to_be_clickable(self.OFFICIAL_BACK_BUTTON),
            ).click()
        else:
            if self.driver.is_keyboard_shown():
                self.driver.hide_keyboard()
            self.driver.back()
            wait_until(
                self.driver,
                EC.presence_of_element_located(self.SCHEDULE_MATCH_BUTTON),
            )
        return description

    def submit_schedule(self):
        self._scroll_until_visible(
            self.SCHEDULE_MATCH_BUTTON,
            "down",
            "Schedule match button",
        )
        schedule_button = wait_until(
            self.driver,
            EC.presence_of_element_located(self.SCHEDULE_MATCH_BUTTON),
        )
        if schedule_button.get_attribute("enabled") != "true":
            self.select_player_format()

        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.SCHEDULE_MATCH_BUTTON),
        ).click()
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.CONFIRMATION_BUTTON),
        ).click()
        return wait_until(
            self.driver,
            EC.invisibility_of_element_located(self.CONFIRMATION_BUTTON),
        )

    def _scroll_down_until_football_found(self):
        deadline = time.monotonic() + self.timeout
        size = self.driver.get_window_size()
        scroll_views = self.driver.find_elements(
            AppiumBy.CLASS_NAME,
            "android.widget.ScrollView",
        )
        if not scroll_views:
            raise RuntimeError(Texts.FOOTBALL_SCROLL_CONTAINER_NOT_FOUND)

        scroll_bounds = scroll_views[0].rect
        navigation = wait_until(
            self.driver,
            EC.presence_of_element_located(self.PLAY_BUTTON),
        )
        navigation_top = navigation.rect["y"]
        scroll_top = scroll_bounds["y"] + 20
        scroll_height = min(
            scroll_bounds["height"] - 40,
            int(size["height"] * 0.55),
            navigation_top - scroll_top - 20,
        )
        if scroll_height <= 0:
            raise RuntimeError(Texts.FOOTBALL_SCROLL_AREA_INVALID)

        scroll_area = {
            "left": scroll_bounds["x"] + 10,
            "top": scroll_top,
            "width": scroll_bounds["width"] - 20,
            "height": scroll_height,
            "direction": "down",
            "percent": 0.65,
        }

        while time.monotonic() < deadline:
            if self._football_is_in_safe_area(scroll_top, navigation_top):
                return
            can_scroll_more = self.driver.execute_script(
                "mobile: scrollGesture",
                scroll_area,
            )
            if not can_scroll_more:
                break
            try:
                WebDriverWait(
                    self.driver,
                    min(0.5, max(deadline - time.monotonic(), 0.1)),
                    poll_frequency=0.1,
                ).until(
                    lambda _driver: self._football_is_in_safe_area(
                        scroll_top,
                        navigation_top,
                    )
                )
                return
            except TimeoutException:
                continue

        raise RuntimeError(Texts.FOOTBALL_NOT_VISIBLE)

    def _football_is_in_safe_area(self, scroll_top, navigation_top):
        for element in self.driver.find_elements(*self.FOOTBALL_CARD):
            bounds = element.rect
            center_y = bounds["y"] + bounds["height"] / 2
            if element.is_displayed() and scroll_top <= center_y < navigation_top:
                return True
        return False

    def _click_first_displayed_team(self):
        try:
            return WebDriverWait(
                self.driver,
                self.timeout,
                poll_frequency=0.3,
            ).until(
                lambda driver: next(
                    (
                        element
                        for element in driver.find_elements(*self.TEAM_ROWS)
                        if element.is_displayed() and element.is_enabled()
                    ),
                    False,
                )
            )
        except TimeoutException as error:
            raise TimeoutException(Texts.TEAM_NOT_FOUND) from error

    def _click_team_select_button(self, side):
        locator = self._team_select_locator(side)
        card = wait_until(
            self.driver,
            EC.element_to_be_clickable(locator),
        )
        bounds = card.rect
        horizontal_position = 0.23 if side == Texts.YOUR_SIDE else 0.77
        self.driver.execute_script(
            "mobile: clickGesture",
            {
                "x": round(bounds["x"] + bounds["width"] * horizontal_position),
                "y": round(bounds["y"] + bounds["height"] * 0.68),
            },
        )

    @staticmethod
    def _team_select_locator(side):
        return (
            AppiumBy.XPATH,
            "//android.view.View[contains(@content-desc, '%s') "
            "and contains(@content-desc, '%s')]"
            % (side, Texts.SELECT),
        )

    def _opponent_team_locator(self, team_identifier):
        target = "%s%s" % (team_identifier.casefold(), Texts.TEAM_ACCESSIBILITY_SUFFIX)
        return (
            AppiumBy.XPATH,
            "//*[@clickable='true' and "
            "contains(translate(normalize-space(@content-desc), '%s', '%s'), %s)]"
            % (
                Texts.ASCII_UPPERCASE,
                Texts.ASCII_LOWERCASE,
                self._xpath_literal(target),
            ),
        )

    @staticmethod
    def _official_locator(user_identifier, role):
        return (
            AppiumBy.XPATH,
            '//android.widget.ImageView[@content-desc="%s"]'
            % Texts.OFFICIAL_ACCESSIBILITY_TEMPLATE.format(user_identifier, role),
        )

    def _return_to_match_setup(self):
        if self.driver.is_keyboard_shown():
            self.driver.hide_keyboard()
        for _ in range(2):
            if self.driver.find_elements(*self.PLAYER_COUNT_BUTTON):
                return
            self.driver.back()
            try:
                wait_until(
                    self.driver,
                    EC.presence_of_element_located(self.PLAYER_COUNT_BUTTON),
                    min(self.timeout, 3),
                )
                return
            except TimeoutException:
                continue
        raise RuntimeError(Texts.TEAM_SETUP_NOT_REOPENED)

    def _scroll_until_visible(self, locator, direction, description):
        deadline = time.monotonic() + self.timeout
        size = self.driver.get_window_size()
        scroll_area = {
            "left": int(size["width"] * 0.05),
            "top": int(size["height"] * 0.15),
            "width": int(size["width"] * 0.90),
            "height": int(size["height"] * 0.70),
            "direction": direction,
            "percent": 0.65,
        }

        while time.monotonic() < deadline:
            if any(
                element.is_displayed()
                for element in self.driver.find_elements(*locator)
            ):
                return
            self.driver.execute_script("mobile: scrollGesture", scroll_area)
            try:
                wait_until(
                    self.driver,
                    lambda _driver: any(
                        element.is_displayed()
                        for element in self.driver.find_elements(*locator)
                    ),
                    min(0.5, max(deadline - time.monotonic(), 0.1)),
                )
                return
            except TimeoutException:
                continue
        raise TimeoutException(
            Texts.ELEMENT_NOT_VISIBLE.format(description, direction)
        )

    def _dismiss_keyboard(self):
        if self.driver.is_keyboard_shown():
            self.driver.press_keycode(66)
        if self.driver.is_keyboard_shown():
            self.driver.hide_keyboard()
        if self.driver.is_keyboard_shown():
            raise RuntimeError(Texts.KEYBOARD_NOT_DISMISSED)

    @staticmethod
    def _xpath_literal(value):
        if "'" not in value:
            return "'%s'" % value
        if '"' not in value:
            return '"%s"' % value
        return "concat(%s)" % ", \"'\", ".join(
            "'%s'" % part for part in value.split("'")
        )
