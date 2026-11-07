import re

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from utils.configuration import AppiumConfiguration
from utils.favourites_texts import FavouritesTexts
from utils.waits import wait_until


class FavouritesPage:
    def __init__(self, driver):
        self.driver = driver

    @property
    def timeout(self):
        return AppiumConfiguration.from_env().wait_timeout

    def open(self):
        menu_locators = (
            (AppiumBy.ACCESSIBILITY_ID, FavouritesTexts.MENU_LABELS[0]),
            (AppiumBy.ACCESSIBILITY_ID, FavouritesTexts.MENU_LABELS[1]),
            (
                AppiumBy.XPATH,
                "//*[contains(@content-desc, '%s') or contains(@content-desc, '%s')]"
                % FavouritesTexts.MENU_LABELS,
            ),
            (
                AppiumBy.XPATH,
                "//*[contains(@text, '%s') or contains(@text, '%s')]"
                % FavouritesTexts.MENU_LABELS,
            ),
        )
        for locator in menu_locators:
            try:
                target = wait_until(
                    self.driver,
                    EC.element_to_be_clickable(locator),
                    self.timeout,
                )
            except TimeoutException:
                continue
            target.click()
            wait_until(
                self.driver,
                lambda _driver: self.is_my_favourites_page(),
                self.timeout,
            )
            return

        raise TimeoutException(FavouritesTexts.FAVOURITES_ELEMENT_NOT_FOUND)

    def is_my_favourites_page(self):
        favourites_tab = self.driver.find_elements(
            AppiumBy.XPATH,
            "//android.view.View[contains(@content-desc, '%s') "
            "and contains(@content-desc, '%s')]"
            % (FavouritesTexts.FAVOURITES_TAB_PREFIX, FavouritesTexts.TAB_POSITION),
        )
        all_sports_tab = self.driver.find_elements(
            AppiumBy.XPATH,
            '//android.view.View[@content-desc="%s"]'
            % FavouritesTexts.ALL_SPORTS_TAB_DESCRIPTION,
        )
        return bool(favourites_tab and all_sports_tab)

    def is_all_sports_tab(self):
        tabs = self.driver.find_elements(
            AppiumBy.XPATH,
            '//android.view.View[@content-desc="%s"]'
            % FavouritesTexts.ALL_SPORTS_TAB_DESCRIPTION,
        )
        return any(
            tab.is_displayed() and tab.get_attribute("selected") == "true"
            for tab in tabs
        )

    def is_favourite_sports_tab(self):
        tabs = self.driver.find_elements(
            AppiumBy.XPATH,
            "//android.view.View[contains(@content-desc, '%s') "
            "and contains(@content-desc, '%s')]"
            % (FavouritesTexts.FAVOURITES_TAB_PREFIX, FavouritesTexts.TAB_POSITION),
        )
        return any(
            tab.is_displayed() and tab.get_attribute("selected") == "true"
            for tab in tabs
        )

    def click_all_sports(self):
        locators = (
            (
                AppiumBy.XPATH,
                '//android.view.View[@content-desc="%s"]'
                % FavouritesTexts.ALL_SPORTS_TAB_DESCRIPTION,
            ),
            (AppiumBy.ACCESSIBILITY_ID, FavouritesTexts.ALL_SPORTS_LABELS[0]),
            (AppiumBy.XPATH, "//*[@text='%s']" % FavouritesTexts.ALL_SPORTS_LABELS[0]),
            (
                AppiumBy.XPATH,
                "//*[contains(@content-desc, '%s')]"
                % FavouritesTexts.ALL_SPORTS_LABELS[1],
            ),
        )
        self._click_first_available(
            locators,
            FavouritesTexts.ALL_SPORTS_TAB_NOT_FOUND,
        )

    def click_favourite_sports(self):
        locators = (
            (
                AppiumBy.XPATH,
                "//android.view.View[contains(@content-desc, '%s') "
                "and contains(@content-desc, '%s')]"
                % (FavouritesTexts.FAVOURITES_TAB_PREFIX, FavouritesTexts.TAB_POSITION),
            ),
            (
                AppiumBy.ACCESSIBILITY_ID,
                FavouritesTexts.FAVOURITE_SPORTS_LABELS[0],
            ),
            (
                AppiumBy.XPATH,
                "//*[@text='%s']" % FavouritesTexts.FAVOURITE_SPORTS_LABELS[0],
            ),
            (
                AppiumBy.XPATH,
                "//*[contains(@content-desc, '%s')]"
                % FavouritesTexts.FAVOURITE_SPORTS_LABELS[0],
            ),
        )
        self._click_first_available(
            locators,
            FavouritesTexts.FAVOURITE_SPORTS_TAB_NOT_FOUND,
        )

    def click_browse_all_sports(self):
        wait_until(
            self.driver,
            EC.element_to_be_clickable(
                (AppiumBy.ACCESSIBILITY_ID, FavouritesTexts.BROWSE_ALL_SPORTS_LABEL)
            ),
        ).click()

    def click_favourite_for_sport(self, sport):
        self._toggle_sport_favourite(sport, 1)

    def remove_favourite_for_sport(self, sport):
        self._toggle_sport_favourite(sport, -1)

    def _toggle_sport_favourite(self, sport, count_delta):
        count_before = self.get_favourite_count()
        count_after = count_before + count_delta
        if count_after < 0 or count_after > 3:
            raise RuntimeError(
                FavouritesTexts.FAVOURITE_COUNT_LIMIT_ERROR.format(
                    sport, count_before
                )
            )

        card = wait_until(
            self.driver,
            EC.element_to_be_clickable(self._sport_card_locator(sport)),
        )
        card.click()
        self._dismiss_sport_feedback()
        wait_until(
            self.driver,
            lambda _driver: self.get_favourite_count() == count_after,
            self.timeout,
        )

    def get_favourite_count(self):
        locator = (
            AppiumBy.XPATH,
            "//android.widget.ProgressBar[contains(@content-desc, '%s')]"
            % FavouritesTexts.FAVOURITES_COUNT_DESCRIPTION,
        )
        description = self.driver.find_element(*locator).get_attribute("content-desc")
        match = re.search(FavouritesTexts.FAVOURITES_COUNT_PATTERN, description or "")
        if match is None:
            raise RuntimeError(FavouritesTexts.FAVOURITE_COUNT_NOT_READABLE)
        return int(match.group(1))

    def is_sport_card_displayed(self, sport):
        elements = self.driver.find_elements(*self._sport_card_locator(sport))
        scroll_views = self.driver.find_elements(
            AppiumBy.CLASS_NAME,
            "android.widget.ScrollView",
        )
        if not scroll_views:
            return any(element.is_displayed() for element in elements)

        viewport = scroll_views[0].rect
        padding = int(viewport["height"] * 0.05)
        safe_top = viewport["y"] + padding
        safe_bottom = viewport["y"] + viewport["height"] - padding
        return any(
            element.is_displayed()
            and safe_top
            <= element.rect["y"] + element.rect["height"] / 2
            <= safe_bottom
            for element in elements
        )

    def _sport_card_locator(self, sport):
        return (
            AppiumBy.XPATH,
            "//*[starts-with(@content-desc, %s)]" % self._xpath_literal(sport),
        )

    @staticmethod
    def _xpath_literal(value):
        if "'" not in value:
            return "'%s'" % value
        if '"' not in value:
            return '"%s"' % value
        return "concat(%s)" % ", \"'\", ".join(
            "'%s'" % part for part in value.split("'")
        )

    def click_favourite_buttons_by_paths(self):
        paths = []
        for sport in FavouritesTexts.SPORTS_WITH_FAVOURITE_BUTTONS:
            paths.extend(
                (
                    (
                        AppiumBy.XPATH,
                        '//android.widget.ImageView[@content-desc="%s\n'
                        '%s\n%s"]/android.widget.Button'
                        '[@content-desc="%s"]'
                        % (
                            sport,
                            FavouritesTexts.CHALLENGE_LABEL,
                            FavouritesTexts.NEW_TEAMS_LABEL,
                            FavouritesTexts.FAVOURITE_BUTTON_LABEL,
                        ),
                    ),
                    (
                        AppiumBy.XPATH,
                        "//android.widget.ImageView[contains(@content-desc, '%s')]"
                        "/android.widget.Button[@content-desc='%s']"
                        % (sport, FavouritesTexts.FAVOURITE_BUTTON_LABEL),
                    ),
                )
            )

        for sport, start in zip(
            FavouritesTexts.SPORTS_WITH_FAVOURITE_BUTTONS,
            range(0, len(paths), 2),
        ):
            for locator in paths[start : start + 2]:
                try:
                    wait_until(
                        self.driver,
                        EC.element_to_be_clickable(locator),
                    ).click()
                    self._dismiss_sport_feedback()
                    break
                except TimeoutException:
                    continue
            else:
                raise RuntimeError(
                    FavouritesTexts.FAVOURITE_BUTTON_NOT_FOUND.format(sport)
                )

    def scroll_to_sport(self, sport):
        if self.is_sport_card_displayed(sport):
            return

        scroll_view = self.driver.find_element(
            AppiumBy.CLASS_NAME,
            "android.widget.ScrollView",
        )
        bounds = scroll_view.rect
        screen = self.driver.get_window_size()
        scroll_area = {
            "left": bounds["x"] + 10,
            "top": bounds["y"] + 20,
            "width": bounds["width"] - 20,
            "height": min(
                bounds["height"] - 40,
                int(screen["height"] * 0.50),
            ),
            "percent": 0.75,
        }

        for direction in ("up", "down"):
            for _ in range(20):
                if self.is_sport_card_displayed(sport):
                    return

                can_scroll_more = self.driver.execute_script(
                    "mobile: scrollGesture",
                    dict(scroll_area, direction=direction),
                )
                if self.is_sport_card_displayed(sport):
                    return
                if not can_scroll_more:
                    break

        raise RuntimeError(FavouritesTexts.SPORT_CARD_NOT_FOUND.format(sport))

    def swipe_left(self):
        size = self.driver.get_window_size()
        self.driver.swipe(
            int(size["width"] * 0.85),
            int(size["height"] * 0.5),
            int(size["width"] * 0.15),
            int(size["height"] * 0.5),
            500,
        )

    def _dismiss_sport_feedback(self):
        locators = (
            (AppiumBy.ACCESSIBILITY_ID, FavouritesTexts.FEEDBACK_DISMISS_LABELS[0]),
            (
                AppiumBy.XPATH,
                "//*[@text='%s' or @content-desc='%s']"
                % (
                    FavouritesTexts.FEEDBACK_DISMISS_LABELS[0],
                    FavouritesTexts.FEEDBACK_DISMISS_LABELS[1],
                ),
            ),
        )
        for locator in locators:
            try:
                wait_until(
                    self.driver,
                    EC.element_to_be_clickable(locator),
                    timeout=min(self.timeout, 3),
                ).click()
                return
            except TimeoutException:
                continue

    def _click_first_available(self, locators, error_message):
        for locator in locators:
            try:
                wait_until(
                    self.driver,
                    EC.element_to_be_clickable(locator),
                ).click()
                return
            except TimeoutException:
                continue
        raise TimeoutException(error_message)
