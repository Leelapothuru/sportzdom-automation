import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from utils.configuration import AppiumConfiguration
from utils.waits import wait_until


class BoardsPage:
    BOARDS_BUTTON_LOCATORS = (
        (AppiumBy.ACCESSIBILITY_ID, "Boards"),
        (AppiumBy.XPATH, "//*[@text='Boards']"),
        (AppiumBy.XPATH, "//*[contains(@content-desc, 'Boards')]"),
    )
    SPORT_DROPDOWN = (AppiumBy.XPATH, '//android.view.View[@content-desc="Sport"]')
    SEARCH_FIELD = (AppiumBy.XPATH, "//android.widget.EditText")
    CLEAR_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Clear")
    KEYBOARD_DONE_LOCATORS = (
        (AppiumBy.ACCESSIBILITY_ID, "Done"),
        (AppiumBy.XPATH, "//*[@text='Done' or @content-desc='Done']"),
        (AppiumBy.XPATH, "//android.widget.Button[@text='Done']"),
    )

    def __init__(self, driver):
        self.driver = driver

    def open(self):
        timeout = AppiumConfiguration.from_env().wait_timeout
        last_error = None
        for locator in self.BOARDS_BUTTON_LOCATORS:
            try:
                wait_until(
                    self.driver,
                    EC.element_to_be_clickable(locator),
                    timeout,
                ).click()
                return
            except TimeoutException as error:
                last_error = error
        raise TimeoutException("Boards navigation was not clickable") from last_error

    def wait_for_sport_filter(self):
        return wait_until(
            self.driver,
            EC.visibility_of_element_located(self.SPORT_DROPDOWN),
        )

    def open_sport_filter(self):
        self.wait_for_sport_filter().click()

    def select_sport(self, sport):
        search_field = wait_until(
            self.driver,
            EC.element_to_be_clickable(self.SEARCH_FIELD),
        )
        search_field.click()
        search_field.send_keys(sport)
        self.dismiss_keyboard()
        wait_until(
            self.driver,
            EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, sport)),
        ).click()
        return wait_until(
            self.driver,
            EC.visibility_of_element_located(self.CLEAR_BUTTON),
        )

    def clear_filter(self):
        wait_until(
            self.driver,
            EC.element_to_be_clickable(self.CLEAR_BUTTON),
        ).click()
        return wait_until(
            self.driver,
            EC.invisibility_of_element_located(self.CLEAR_BUTTON),
        )

    def scroll_page(self, direction="down"):
        size = self.driver.get_window_size()
        if direction == "down":
            start_y, end_y = int(size["height"] * 0.80), int(size["height"] * 0.30)
        elif direction == "up":
            start_y, end_y = int(size["height"] * 0.30), int(size["height"] * 0.80)
        else:
            raise ValueError("direction must be 'up' or 'down'")

        self.driver.swipe(
            size["width"] // 2,
            start_y,
            size["width"] // 2,
            end_y,
            500,
        )

    def scroll_for(self, direction, seconds):
        if seconds <= 0:
            raise ValueError("seconds must be greater than zero")

        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self.scroll_page(direction)

    def scroll_until_visible(self, locator):
        timeout = AppiumConfiguration.from_env().wait_timeout
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            elements = self.driver.find_elements(*locator)
            for element in elements:
                if element.is_displayed():
                    return element
            self.scroll_page("up")
        raise TimeoutException(f"Element was not visible after scrolling: {locator}")

    def dismiss_keyboard(self):
        for locator in self.KEYBOARD_DONE_LOCATORS:
            buttons = self.driver.find_elements(*locator)
            if buttons:
                buttons[0].click()
                break
        else:
            self.driver.press_keycode(66)

        if self.driver.is_keyboard_shown():
            self.driver.hide_keyboard()
        if self.driver.is_keyboard_shown():
            raise RuntimeError("Mobile keyboard could not be dismissed")
