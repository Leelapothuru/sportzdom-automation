import time

import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from drivers.driver_manager import get_driver


OFFICIAL_SEARCH = "user2026.09"
OFFICIAL_FEE = "2500"
ACTION_DELAY_SECONDS = 3


def perform_action(action, *args, **kwargs):
    result = action(*args, **kwargs)
    time.sleep(ACTION_DELAY_SECONDS)
    return result


def wait_for_element(driver, by, value, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


def click_element(driver, by, value, timeout=20):
    perform_action(wait_for_element(driver, by, value, timeout=timeout).click)


def scroll_page_down(driver):
    return scroll_page(driver, "down")


def scroll_page_up(driver):
    return scroll_page(driver, "up")


def scroll_page(driver, direction):
    scroll_view = driver.find_element(
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.ScrollView")',
    )
    return perform_action(
        driver.execute_script,
        "mobile: scrollGesture",
        {
            "elementId": scroll_view.id,
            "direction": direction,
            "percent": 0.7,
        },
    )


def scroll_to_bottom(driver):
    while scroll_page_down(driver):
        pass


def scroll_until_clickable(driver, by, value, max_scrolls=8, direction="down"):
    for scroll_count in range(max_scrolls + 1):
        try:
            return wait_for_element(driver, by, value, timeout=2)
        except TimeoutException:
            scroll = scroll_page_down if direction == "down" else scroll_page_up
            if scroll_count == max_scrolls or not scroll(driver):
                raise


def open_referees_from_menu(driver):
    click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Menu\nMenu")
    perform_action(
        driver.execute_script,
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
    referees = wait_for_element(
        driver,
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionContains("Referees")',
    )
    perform_action(referees.click)


def test_officials_info_navigation_flow():
    try:
        driver = get_driver()
    except RuntimeError as error:
        if "No Android device/emulator" not in str(error):
            raise
        pytest.skip(
            "No Android device/emulator is connected through ADB. "
            "Connect a device or start an emulator before running this test."
        )

    try:
        open_referees_from_menu(driver)
        click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Back")
        open_referees_from_menu(driver)

        click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Sport")
        click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Archery")
        click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Location")
        click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Andhra Pradesh")
        click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Gender")
        click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Male")
        click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Clear filters")

        search_field = wait_for_element(
            driver,
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.EditText")',
        )
        perform_action(search_field.click)
        perform_action(search_field.clear)
        perform_action(search_field.send_keys, OFFICIAL_SEARCH)
        perform_action(driver.press_keycode, 66)

        official = wait_for_element(
            driver,
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().descriptionContains("user2026.09")',
        )
        perform_action(official.click)

        click_element(
            driver,
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().descriptionContains("Add fee")',
        )
        fee_field = wait_for_element(
            driver,
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.EditText")',
        )
        perform_action(fee_field.click)
        perform_action(fee_field.clear)
        click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Cancel")

        click_element(
            driver,
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().descriptionContains("Add fee")',
        )
        fee_field = wait_for_element(
            driver,
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.EditText")',
        )
        perform_action(fee_field.click)
        perform_action(fee_field.clear)
        perform_action(fee_field.send_keys, OFFICIAL_FEE)
        click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Save")
        scroll_to_bottom(driver)

        reviews_tab = scroll_until_clickable(
            driver,
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().descriptionContains("Reviews")',
        )
        perform_action(reviews_tab.click)
        gallery_tab = scroll_until_clickable(
            driver,
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().descriptionContains("Gallery")',
        )
        perform_action(gallery_tab.click)

        edit_fee = scroll_until_clickable(
            driver,
            AppiumBy.ACCESSIBILITY_ID,
            "Edit",
            direction="up",
        )
        perform_action(edit_fee.click)
        fee_field = wait_for_element(
            driver,
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.EditText")',
        )
        perform_action(fee_field.click)
        perform_action(fee_field.clear)
        perform_action(fee_field.send_keys, OFFICIAL_FEE)
        click_element(driver, AppiumBy.ACCESSIBILITY_ID, "Save")
    finally:
        driver.quit()
