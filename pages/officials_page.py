from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class OfficialsPage:
    MENU_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Menu\nMenu")
    OFFICIALS_MENU_ITEM = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionContains("Referees")',
    )
    BACK_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Back")
    SPORT_FILTER = (AppiumBy.ACCESSIBILITY_ID, "Sport")
    LOCATION_FILTER = (AppiumBy.ACCESSIBILITY_ID, "Location")
    GENDER_FILTER = (AppiumBy.ACCESSIBILITY_ID, "Gender")
    CLEAR_FILTERS_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Clear filters")
    SEARCH_FIELD = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.EditText")',
    )
    FEE_FIELD = SEARCH_FIELD
    ADD_FEE_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionContains("Add fee")',
    )
    EDIT_FEE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Edit")
    CANCEL_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Cancel")
    SAVE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Save")
    SCROLL_VIEW = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.ScrollView")',
    )
    DEFAULT_TIMEOUT = 20

    def __init__(self, driver, timeout=DEFAULT_TIMEOUT):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def open_from_menu(self):
        self._click(self.MENU_BUTTON)
        self.driver.execute_script(
            "mobile: swipeGesture",
            {
                "left": 40,
                "top": 500,
                "width": 1000,
                "height": 1400,
                "direction": "up",
                "percent": 0.16,
            },
        )
        self._click(self.OFFICIALS_MENU_ITEM)

    def go_back(self):
        self._click(self.BACK_BUTTON)

    def select_filters(self, sport, location, gender):
        for filter_locator, option in (
            (self.SPORT_FILTER, sport),
            (self.LOCATION_FILTER, location),
            (self.GENDER_FILTER, gender),
        ):
            self._click(filter_locator)
            self._click((AppiumBy.ACCESSIBILITY_ID, option))

    def clear_filters(self):
        self._click(self.CLEAR_FILTERS_BUTTON)
        self.wait.until(EC.invisibility_of_element_located(self.CLEAR_FILTERS_BUTTON))

    def search_official(self, identifier):
        search_field = self._clickable(self.SEARCH_FIELD)
        search_field.click()
        search_field.clear()
        search_field.send_keys(identifier)
        self.driver.press_keycode(66)
        return self._clickable(self._official_locator(identifier))

    def open_official(self, identifier):
        official = self.search_official(identifier)
        description = official.get_attribute("contentDescription") or ""
        official.click()
        self._clickable(self.ADD_FEE_BUTTON)
        return description

    def open_add_fee_form(self):
        self._click(self.ADD_FEE_BUTTON)
        self._clickable(self.FEE_FIELD)
        self._clickable(self.CANCEL_BUTTON)

    def cancel_add_fee(self):
        self._click(self.CANCEL_BUTTON)
        self._clickable(self.ADD_FEE_BUTTON)

    def enter_fee(self, fee):
        fee_field = self._clickable(self.FEE_FIELD)
        fee_field.click()
        fee_field.clear()
        fee_field.send_keys(fee)
        return fee_field.get_attribute("text")

    def save_fee(self):
        self._click(self.SAVE_BUTTON)
        self.wait.until(EC.invisibility_of_element_located(self.SAVE_BUTTON))

    def scroll_to_bottom(self):
        for _ in range(20):
            if not self._scroll("down"):
                return
        raise TimeoutException("Officials details did not reach the bottom after 20 scrolls")

    def open_tab(self, tab_name, direction="down"):
        locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().descriptionContains("{tab_name}")',
        )
        tab = self._scroll_until_clickable(locator, direction)
        tab.click()

    def open_edit_fee_form(self):
        self._scroll_until_clickable(self.EDIT_FEE_BUTTON, "up").click()
        self._clickable(self.FEE_FIELD)
        self._clickable(self.SAVE_BUTTON)

    def is_fee_form_displayed(self):
        return bool(
            self._is_visible(self.FEE_FIELD)
            and self._is_visible(self.SAVE_BUTTON)
        )

    def is_add_fee_available(self):
        return self._is_visible(self.ADD_FEE_BUTTON)

    def is_edit_fee_available(self):
        return self._is_visible(self.EDIT_FEE_BUTTON)

    def _click(self, locator):
        self._clickable(locator).click()

    def _clickable(self, locator):
        return self.wait.until(EC.element_to_be_clickable(locator))

    def _is_visible(self, locator):
        return any(
            element.is_displayed()
            for element in self.driver.find_elements(*locator)
        )

    def _scroll(self, direction):
        scroll_view = self.driver.find_element(*self.SCROLL_VIEW)
        return self.driver.execute_script(
            "mobile: scrollGesture",
            {
                "elementId": scroll_view.id,
                "direction": direction,
                "percent": 0.7,
            },
        )

    def _scroll_until_clickable(self, locator, direction, max_scrolls=8):
        if direction not in ("up", "down"):
            raise ValueError("direction must be 'up' or 'down'")

        for scroll_count in range(max_scrolls + 1):
            try:
                return WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable(locator)
                )
            except TimeoutException:
                if scroll_count == max_scrolls or not self._scroll(direction):
                    raise

    @staticmethod
    def _official_locator(identifier):
        return (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().descriptionContains("{identifier}")',
        )
