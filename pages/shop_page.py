from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from utils.configuration import AppiumConfiguration
from utils.waits import wait_until


class ShopPage:
    MENU_LOCATORS = (
        (AppiumBy.XPATH, '//android.widget.Button[@content-desc="Menu\nMenu"]'),
        (AppiumBy.ACCESSIBILITY_ID, "Menu"),
        (AppiumBy.XPATH, "//*[@text='Menu']"),
        (AppiumBy.XPATH, "//*[contains(@content-desc, 'Menu')]"),
    )
    MENU_SEARCH = (AppiumBy.XPATH, "//android.widget.EditText")
    SHOP_ITEM = (
        AppiumBy.XPATH,
        '//android.view.View[@content-desc="Shop\nBrowse sports equipment"]',
    )
    SHOP_SEARCH = (AppiumBy.XPATH, "//android.widget.EditText")

    def __init__(self, driver):
        self.driver = driver

    def open_menu(self):
        timeout = min(AppiumConfiguration.from_env().wait_timeout, 3)
        for locator in self.MENU_LOCATORS:
            try:
                wait_until(
                    self.driver,
                    EC.element_to_be_clickable(locator),
                    timeout,
                ).click()
                return
            except TimeoutException:
                continue

        bottom_items = [
            element
            for element in self.driver.find_elements(
                AppiumBy.XPATH, "//*[@clickable='true']"
            )
            if element.is_displayed()
            and element.location["y"] > self.driver.get_window_size()["height"] * 0.75
        ]
        if len(bottom_items) >= 5:
            sorted_items = sorted(bottom_items, key=lambda element: element.location["x"])
            sorted_items[4].click()
            return
        raise TimeoutException("Menu option was not found in the bottom navigation bar")

    def search_menu(self, query):
        field = wait_until(
            self.driver,
            EC.element_to_be_clickable(self.MENU_SEARCH),
        )
        field.click()
        field.clear()
        field.send_keys(query)
        self.driver.press_keycode(66)

    def open_shop(self):
        shop = self._scroll_until_visible(self.SHOP_ITEM, "Shop")
        shop.click()
        return wait_until(
            self.driver,
            EC.element_to_be_clickable(self.SHOP_SEARCH),
        )

    def wait_for_category(self, name):
        locator = (AppiumBy.ACCESSIBILITY_ID, name)
        return self._scroll_until_visible(locator, name)

    def open_category(self, name):
        category = self.wait_for_category(name)
        category.click()
        wait_until(
            self.driver,
            EC.staleness_of(category),
        )

    def _scroll_until_visible(self, locator, target_name, max_scrolls=20):
        screen = self.driver.get_window_size()
        scroll_area = {
            "left": int(screen["width"] * 0.40),
            "top": int(screen["height"] * 0.20),
            "width": int(screen["width"] * 0.20),
            "height": int(screen["height"] * 0.48),
            "direction": "down",
            "percent": 0.65,
        }

        for scroll_count in range(max_scrolls + 1):
            try:
                return wait_until(
                    self.driver,
                    EC.visibility_of_element_located(locator),
                    timeout=0.5,
                )
            except TimeoutException:
                if scroll_count == max_scrolls:
                    break
                self.driver.execute_script("mobile: scrollGesture", scroll_area)

        raise TimeoutException(
            f"{target_name} was not visible after {max_scrolls} vertical scrolls"
        )
