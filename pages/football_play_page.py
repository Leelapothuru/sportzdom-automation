import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.configuration import AppiumConfiguration
from utils.football_play_texts import FootballPlayTexts as Texts
from utils.waits import wait_until


class FootballPlayPage:
    PLAY_BUTTON = (
        AppiumBy.XPATH,
        '//android.widget.Button[@content-desc="%s"]' % Texts.PLAY_BUTTON,
    )
    FOOTBALL_CARD = (
        AppiumBy.XPATH,
        '//android.widget.ImageView[@content-desc="%s"]' % Texts.FOOTBALL,
    )
    START_MATCH_BUTTON = (AppiumBy.ACCESSIBILITY_ID, Texts.START_MATCH)
    PLAY_NOW_CARD = (
        AppiumBy.XPATH,
        '//android.view.View[@content-desc="%s"]' % Texts.PLAY_NOW,
    )
    MYSELF_CARD = (
        AppiumBy.XPATH,
        "//android.view.View[starts-with(@content-desc, '%s')]"
        % Texts.MYSELF_PREFIX,
    )
    CONTINUE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, Texts.CONTINUE_TO_PLAY_NOW)
    TEAM_ROWS = (
        AppiumBy.XPATH,
        "//*[@clickable='true' and contains(@content-desc, '%s')]"
        % Texts.TEAM_MEMBERS_MARKER,
    )
    SELECT_TEAM_BUTTON = (
        AppiumBy.XPATH,
        '//android.widget.Button[@content-desc="%s"]' % Texts.SELECT_TEAM,
    )
    BACK_BUTTON = (AppiumBy.XPATH, "//android.widget.Button")
    SEARCH_FIELD = (AppiumBy.XPATH, "//android.widget.EditText")
    PLAYER_COUNT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, Texts.FIVE_PLAYERS)
    DURATION_FIELD = (AppiumBy.XPATH, "//android.widget.EditText")
    VENUE_SECTION = (
        AppiumBy.XPATH,
        "//android.view.View[contains(@content-desc, '%s')]" % Texts.VENUE_PREFIX,
    )
    CREATE_MATCH_BUTTON = (AppiumBy.ACCESSIBILITY_ID, Texts.CREATE_MATCH)

    def __init__(self, driver):
        self.driver = driver

    @property
    def timeout(self):
        return AppiumConfiguration.from_env().wait_timeout

    def activate_app(self):
        self.driver.activate_app(AppiumConfiguration.from_env().app_package)

    def open_play_now_flow(self):
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
            EC.element_to_be_clickable(self.PLAY_NOW_CARD),
        ).click()
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.MYSELF_CARD),
        ).click()
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.CONTINUE_BUTTON),
        ).click()
        wait_until(
            self.driver,
            EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, Texts.GENDER)),
        )

    def select_gender(self):
        wait_until(
            self.driver,
            EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, Texts.GENDER)),
        ).click()

    def select_team(self, side, search_term=None, team_identifier=None):
        if side not in (Texts.YOUR_SIDE, Texts.OPPONENT):
            raise ValueError(Texts.UNSUPPORTED_TEAM_SIDE.format(side))
        if side == Texts.OPPONENT and (
            search_term is None or team_identifier is None
        ):
            raise ValueError(Texts.OPPONENT_SELECTION_REQUIRES_DATA)

        self._click_team_select_button(side)
        if side == Texts.YOUR_SIDE:
            team = self._first_displayed_team()
            team_description = team.get_attribute("contentDescription") or ""
            team.click()
        else:
            search = wait_until(
                self.driver,
                EC.element_to_be_clickable(self.SEARCH_FIELD),
            )
            search.click()
            search.send_keys(search_term)
            team = wait_until(
                self.driver,
                EC.element_to_be_clickable(
                    self._opponent_team_locator(team_identifier)
                ),
            )
            team_description = team.get_attribute("contentDescription") or ""
            team.click()

        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.SELECT_TEAM_BUTTON),
        ).click()

        if side == Texts.YOUR_SIDE:
            wait_until(
                self.driver,
                EC.element_to_be_clickable(self.BACK_BUTTON),
            ).click()
            wait_until(
                self.driver,
                EC.element_to_be_clickable(
                    self._team_select_locator(Texts.OPPONENT)
                ),
            )
        else:
            wait_until(
                self.driver,
                EC.element_to_be_clickable(self.BACK_BUTTON),
            ).click()
            wait_until(
                self.driver,
                EC.presence_of_element_located(self.PLAYER_COUNT_BUTTON),
            )
        return team_description

    def select_player_format(self):
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.PLAYER_COUNT_BUTTON),
        ).click()

    def set_duration(self, duration):
        self._scroll_until_visible(
            self.DURATION_FIELD,
            "up",
            Texts.DURATION_FIELD_LABEL,
        )
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

    def select_venue(self, search_term, expected_location):
        self._scroll_until_visible(
            self.VENUE_SECTION,
            "up",
            Texts.VENUE_SECTION_LABEL,
        )
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

    def submit_match(self):
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.CREATE_MATCH_BUTTON),
        ).click()
        return wait_until(
            self.driver,
            EC.invisibility_of_element_located(self.CREATE_MATCH_BUTTON),
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
        return any(
            element.is_displayed()
            and scroll_top
            <= element.rect["y"] + element.rect["height"] / 2
            < navigation_top
            for element in self.driver.find_elements(*self.FOOTBALL_CARD)
        )

    def _first_displayed_team(self):
        team = WebDriverWait(
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
        return team

    def _click_team_select_button(self, side):
        card = wait_until(
            self.driver,
            EC.element_to_be_clickable(self._team_select_locator(side)),
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
        target = "%s%s" % (
            team_identifier.casefold(),
            Texts.TEAM_ACCESSIBILITY_SUFFIX,
        )
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
        raise TimeoutException(Texts.ELEMENT_NOT_VISIBLE.format(description, direction))

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
