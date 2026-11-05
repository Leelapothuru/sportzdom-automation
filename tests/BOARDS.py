import sys
import time
from pathlib import Path

# Make this script runnable directly with: python tests/BOARDS.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from drivers.driver_manager import get_driver
from pages.login_page import LoginPage


BOARDS_BUTTON_XPATH = '//android.widget.Button[@content-desc="Boards\nBoards"]'
SPORT_DROPDOWN_XPATH = '//android.view.View[@content-desc="Sport"]'
SEARCH_BAR_XPATH = "//android.widget.EditText"


def swipe_page(driver, direction, duration=500):
    size = driver.get_window_size()
    start_y, end_y = (
        (int(size["height"] * 0.30), int(size["height"] * 0.80))
        if direction == "up"
        else (int(size["height"] * 0.80), int(size["height"] * 0.30))
    )
    driver.swipe(
        size["width"] // 2,
        start_y,
        size["width"] // 2,
        end_y,
        duration,
    )


def dismiss_keyboard(driver):
    done_locators = [
        (AppiumBy.ACCESSIBILITY_ID, "Done"),
        (AppiumBy.XPATH, "//*[@text='Done' or @content-desc='Done']"),
        (AppiumBy.XPATH, "//android.widget.Button[@text='Done']"),
    ]

    for locator in done_locators:
        buttons = driver.find_elements(*locator)
        if buttons:
            buttons[0].click()
            break
    else:
        driver.press_keycode(66)

    if driver.is_keyboard_shown():
        driver.hide_keyboard()
    if driver.is_keyboard_shown():
        raise RuntimeError("Mobile keyboard could not be dismissed")


def scroll_continuously(driver, direction, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        swipe_page(driver, direction)


def scroll_up_until_found(driver, locator, description, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        elements = driver.find_elements(*locator)
        if any(element.is_displayed() for element in elements):
            return
        swipe_page(driver, "up")
        time.sleep(0.3)

    raise RuntimeError("%s was not found after scrolling up" % description)


driver = get_driver()
login = LoginPage(driver)

try:
    if not login.is_logged_in():
        login.login()
        time.sleep(5)
    elif not login.is_home_page():
        login.click_home()
        time.sleep(2)

    if not login.is_home_page():
        raise RuntimeError("Home page was not displayed")

    print("Clicking Boards in the Home bottom navigation...")
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, BOARDS_BUTTON_XPATH))
    ).click()
    time.sleep(2)

    print("Scrolling down continuously for 5 seconds...")
    scroll_continuously(driver, "down", 5)

    print("Scrolling up until the Sport dropdown is found...")
    scroll_up_until_found(
        driver,
        (AppiumBy.XPATH, SPORT_DROPDOWN_XPATH),
        "Sport dropdown",
    )

    print("Opening the Sport dropdown...")
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, SPORT_DROPDOWN_XPATH))
    ).click()

    print('Searching for "Football"...')
    search_bar = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, SEARCH_BAR_XPATH))
    )
    search_bar.click()
    search_bar.send_keys("Football")
    dismiss_keyboard(driver)

    print('Selecting "Football" from the results...')
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Football"))
    ).click()

    print("Scrolling down continuously for 5 seconds on filtered Boards...")
    scroll_continuously(driver, "down", 5)

    print("Continuing to scroll up until the Clear button is found...")
    scroll_up_until_found(
        driver,
        (AppiumBy.ACCESSIBILITY_ID, "Clear"),
        "Clear button",
    )

    print('Clicking the "Clear" button...')
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Clear"))
    ).click()
    print("Boards filter flow completed")
finally:
    driver.quit()
