import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from drivers.driver_manager import get_driver
from pages.login_page import LoginPage


MY_PROFILE_LOCATOR = (AppiumBy.ACCESSIBILITY_ID, "My Profile")

driver = get_driver()
login = LoginPage(driver)

try:
    print("App initialized. Current Activity:", driver.current_activity)

    edit_profile_header = (
        AppiumBy.XPATH,
        "//*[contains(@content-desc, 'Edit Profile') "
        "and contains(@content-desc, 'Manage Your Personal Information')]",
    )
    edit_profile_button = (
        AppiumBy.XPATH,
        '//android.widget.Button[@content-desc="Edit Profile"]',
    )
    edit_profile_open = bool(driver.find_elements(*edit_profile_header))

    if not edit_profile_open and driver.find_elements(*edit_profile_button):
        print("Resuming from My Profile and opening Edit Profile...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(edit_profile_button)
        ).click()
        edit_profile_open = True

    if not edit_profile_open:
        if not login.is_home_page() and not login.is_signin_page():
            for _ in range(4):
                driver.back()
                time.sleep(1)
                if login.is_home_page() or login.is_signin_page():
                    break

        if not login.is_logged_in():
            login.login()
            time.sleep(3)

        if not login.is_home_page():
            login.click_home()

        if not login.is_home_page():
            raise RuntimeError("Home page was not displayed")

        print("Opening the Profile drawer...")
        login.click_profile()

        WebDriverWait(driver, 10).until(
            lambda current_driver: (
                current_driver.find_elements(
                    AppiumBy.XPATH,
                    "//*[@text='GENERAL' or @content-desc='GENERAL']",
                )
                or current_driver.find_elements(*MY_PROFILE_LOCATOR)
            )
        )
        driver.save_screenshot("screenshots/profile_drawer_opened.png")

        print("Scrolling down in the Profile drawer to find My Profile...")
        size = driver.get_window_size()
        for _ in range(5):
            driver.swipe(
                size["width"] // 2,
                int(size["height"] * 0.75),
                size["width"] // 2,
                int(size["height"] * 0.25),
                600,
            )
            time.sleep(0.5)

        driver.save_screenshot("screenshots/profile_drawer_scrolled.png")
        target = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(MY_PROFILE_LOCATOR)
        )
        target.click()
        driver.save_screenshot("screenshots/my_profile_screen.png")
        print("My Profile opened successfully")

        edit_profile = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(edit_profile_button)
        )
        edit_profile.click()
        print("Edit Profile opened successfully")

    first_name_label_locator = (
        AppiumBy.XPATH,
        "//*[@content-desc='First name *' or @text='First name *']",
    )
    screen = driver.get_window_size()
    first_name = None
    for scroll_count in range(11):
        labels = driver.find_elements(*first_name_label_locator)
        if labels and labels[0].is_displayed():
            fields = driver.find_elements(
                AppiumBy.XPATH,
                "//*[@content-desc='First name *' or @text='First name *']"
                "/following-sibling::android.widget.EditText[1]",
            )
            if fields and fields[0].is_displayed():
                first_name = fields[0]
                break

        if scroll_count < 10:
            driver.execute_script(
                "mobile: scrollGesture",
                {
                    "left": int(screen["width"] * 0.10),
                    "top": int(screen["height"] * 0.20),
                    "width": int(screen["width"] * 0.80),
                    "height": int(screen["height"] * 0.60),
                    "direction": "up",
                    "percent": 0.65,
                },
            )
            time.sleep(0.3)

    if first_name is None:
        raise RuntimeError("First Name field was not found after scrolling up")

    first_name.click()
    first_name.clear()
    if first_name.get_attribute("text"):
        raise RuntimeError("First Name field was not cleared")
    for character in "Navin":
        first_name.send_keys(character)
        time.sleep(0.1)
    first_name_value = first_name.get_attribute("text")
    if first_name_value != "Navin":
        raise RuntimeError(
            "First Name field does not contain exactly 'Navin': %r"
            % first_name_value
        )
    print("First Name cleared and updated to Navin")

    for _ in range(2):
        driver.press_keycode(66)

    jersey_number_xpath = (
        "//*[@content-desc='Jersey number' or @text='Jersey number']"
        "/following-sibling::android.widget.EditText[1]"
    )
    jersey_number = login._scroll_vertically_until_visible(
        (AppiumBy.XPATH, jersey_number_xpath),
        "Jersey Number",
    )
    jersey_number.click()
    jersey_number.clear()
    if jersey_number.get_attribute("text"):
        raise RuntimeError("Jersey Number field was not cleared")
    jersey_number.send_keys("17")
    if jersey_number.get_attribute("text") != "17":
        raise RuntimeError("Jersey Number field does not contain exactly '17'")

    next_button_locators = [
        (AppiumBy.ACCESSIBILITY_ID, "Next"),
        (AppiumBy.XPATH, "//*[@text='Next' or @content-desc='Next']"),
        (AppiumBy.XPATH, "//android.widget.Button[@text='Next']"),
    ]
    next_button = next(
        (
            element
            for locator in next_button_locators
            for element in driver.find_elements(*locator)
            if element.is_displayed()
        ),
        None,
    )
    if next_button is not None:
        next_button.click()
    else:
        driver.press_keycode(66)

    use_location = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.XPATH,
                '//android.widget.Button[@content-desc="Use my location"]',
            )
        )
    )
    use_location.click()
    print("Jersey Number updated to 17 and Use my location selected")

    time.sleep(15)
    save_changes = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (AppiumBy.ACCESSIBILITY_ID, "Save changes")
        )
    )
    save_changes.click()
    print("Profile changes saved")
finally:
    driver.quit()