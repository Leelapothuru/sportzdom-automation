import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from drivers.driver_manager import get_driver


APPLICATION_DESCRIPTION = (
    "I am interested in contributing to the sport as an Archery referee."
)


def report_step(step_number, description):
    print(f"Step {step_number}: {description}", flush=True)


def wait_for_element(driver, by, value, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


def click_element(driver, step_number, description, by, value, timeout=20):
    report_step(step_number, description)
    wait_for_element(driver, by, value, timeout=timeout).click()


def scroll_form_down(driver):
    scroll_view = driver.find_element(
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.ScrollView")',
    )
    return driver.execute_script(
        "mobile: scrollGesture",
        {
            "elementId": scroll_view.id,
            "direction": "down",
            "percent": 0.7,
        },
    )


def scroll_until_clickable(driver, by, value, step_number, description, max_scrolls=6):
    report_step(step_number, description)
    for scroll_count in range(max_scrolls + 1):
        try:
            return wait_for_element(driver, by, value, timeout=2)
        except TimeoutException:
            if scroll_count == max_scrolls or not scroll_form_down(driver):
                raise


def test_archery_referee_role_registration_flow():
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
        click_element(
            driver,
            1,
            "Open the menu from the home page",
            AppiumBy.ACCESSIBILITY_ID,
            "Menu\nMenu",
        )
        click_element(
            driver,
            2,
            "Open My roles",
            AppiumBy.ACCESSIBILITY_ID,
            "My roles\nManage how you take part",
        )
        click_element(
            driver,
            3,
            "Open the Register role tab",
            AppiumBy.ACCESSIBILITY_ID,
            "Register role\nTab 2 of 2",
        )
        click_element(
            driver,
            4,
            "Open the sport selector",
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.view.View").instance(22)',
        )
        click_element(
            driver,
            5,
            "Select BasketBall",
            AppiumBy.ACCESSIBILITY_ID,
            "FootBall",
        )
        click_element(
            driver,
            "6.1",
            "Open the role selector",
            AppiumBy.ACCESSIBILITY_ID,
            "Select role",
        )
        click_element(
            driver,
            "6.2",
            "Select Referee",
            AppiumBy.ACCESSIBILITY_ID,
            "Referee",
        )

        playing_level = scroll_until_clickable(
            driver,
            AppiumBy.ACCESSIBILITY_ID,
            "Select playing level",
            7,
            "Scroll down to the playing level and open its selector",
        )
        playing_level.click()
        click_element(
            driver,
            8,
            "Select South Zone",
            AppiumBy.ACCESSIBILITY_ID,
            "South Zone",
        )
        click_element(
            driver,
            9,
            "Add one year of experience",
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.Button").instance(5)',
        )
        scroll_until_clickable(
            driver,
            AppiumBy.ACCESSIBILITY_ID,
            "Select education",
            10,
            "Scroll down to the education and state fields",
        )
        click_element(
            driver,
            11,
            "Open the education selector",
            AppiumBy.ACCESSIBILITY_ID,
            "Select education",
        )
        click_element(
            driver,
            12,
            "Select Post Graduate",
            AppiumBy.ACCESSIBILITY_ID,
            "Post Graduate",
        )
        click_element(
            driver,
            13,
            "Open the state selector",
            AppiumBy.ACCESSIBILITY_ID,
            "Select state",
        )
        click_element(
            driver,
            14,
            "Select Andhra Pradesh",
            AppiumBy.ACCESSIBILITY_ID,
            "Andhra Pradesh",
        )

        scroll_until_clickable(
            driver,
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.EditText")',
            15,
            "Scroll down to the application description",
        )
        report_step(16, "Enter a short role application description")
        description_field = wait_for_element(
            driver,
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.EditText")',
        )
        description_field.click()
        description_field.clear()
        description_field.send_keys(APPLICATION_DESCRIPTION)

        report_step(17, "Dismiss the keyboard by tapping the page")
        window_size = driver.get_window_size()
        driver.execute_script(
            "mobile: clickGesture",
            {
                "x": window_size["width"] // 2,
                "y": window_size["height"] // 10,
            },
        )
        click_element(
            driver,
            18,
            "Accept the application declaration",
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.CheckBox")',
        )
        click_element(
            driver,
            19,
            "Submit the role application",
            AppiumBy.ACCESSIBILITY_ID,
            "Submit Application",
        )
        click_element(
            driver,
            20,
            "Confirm the application submission",
            AppiumBy.ACCESSIBILITY_ID,
            "Ok",
        )
    finally:
        driver.quit()
