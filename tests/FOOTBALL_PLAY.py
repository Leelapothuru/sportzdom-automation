import sys
import time
from pathlib import Path

# Make this script runnable directly with: python tests/GOAL_SPORTS_PLAY.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from drivers.driver_manager import get_driver
from pages.login_page import LoginPage


PLAY_BUTTON_XPATH = '//android.widget.Button[@content-desc="Play\nPlay"]'
FOOTBALL_XPATH = '//android.widget.ImageView[@content-desc="Football"]'
START_MATCH_ACCESSIBILITY_ID = "Start a match"
WAIT_SECONDS = 10


def scroll_down_until_football_found(driver, timeout=WAIT_SECONDS):
    deadline = time.monotonic() + timeout
    size = driver.get_window_size()

    while time.monotonic() < deadline:
        football_elements = driver.find_elements(AppiumBy.XPATH, FOOTBALL_XPATH)
        if any(element.is_displayed() for element in football_elements):
            return

        driver.swipe(
            size["width"] // 2,
            int(size["height"] * 0.80),
            size["width"] // 2,
            int(size["height"] * 0.30),
            600,
        )
        time.sleep(0.3)

    raise RuntimeError("Football was not found after scrolling down")


def click_first_displayed_team(driver, timeout=WAIT_SECONDS):
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        team_rows = driver.find_elements(
            AppiumBy.XPATH,
            "//*[@clickable='true' and contains(@content-desc, 'members')]",
        )
        for team in team_rows:
            if team.is_displayed() and team.is_enabled():
                team.click()
                return
        time.sleep(0.3)

    raise RuntimeError("No displayed team option was found")


def click_team_select_button(driver, side, timeout=WAIT_SECONDS):
    side_label = "Your side" if side == "your side" else "Opponent"
    locator = (
        AppiumBy.XPATH,
        "//android.view.View[contains(@content-desc, '%s') "
        "and contains(@content-desc, 'Select')]" % side_label,
    )
    card = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(locator)
    )
    bounds = card.rect
    horizontal_position = 0.23 if side == "your side" else 0.77
    driver.execute_script(
        "mobile: clickGesture",
        {
            "x": round(bounds["x"] + bounds["width"] * horizontal_position),
            "y": round(bounds["y"] + bounds["height"] * 0.68),
        },
    )


def scroll_up_until_visible(driver, locator, description, timeout=WAIT_SECONDS):
    deadline = time.monotonic() + timeout
    size = driver.get_window_size()

    while time.monotonic() < deadline:
        elements = driver.find_elements(*locator)
        if any(element.is_displayed() for element in elements):
            return

        driver.execute_script(
            "mobile: scrollGesture",
            {
                "left": int(size["width"] * 0.05),
                "top": int(size["height"] * 0.15),
                "width": int(size["width"] * 0.90),
                "height": int(size["height"] * 0.70),
                "direction": "up",
                "percent": 0.65,
            },
        )
        time.sleep(0.3)

    raise RuntimeError("%s was not found after scrolling up" % description)


driver = get_driver()
driver.activate_app("com.sportzdom.app")
login = LoginPage(driver)

try:
    if (
        not login.is_home_page()
        and not login.is_signin_page()
        and not login.is_logged_in()
    ):
        for _ in range(8):
            driver.back()
            time.sleep(1)
            if login.is_home_page() or login.is_signin_page():
                break

    if not login.is_logged_in():
        login.login()
        time.sleep(5)
    elif not login.is_home_page():
        login.click_home()
        time.sleep(2)

    if not login.is_home_page():
        raise RuntimeError("Home page was not displayed")

    print("Clicking Play in the navigation bar...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, PLAY_BUTTON_XPATH))
    ).click()

    print("Scrolling down until Football is found...")
    scroll_down_until_football_found(driver)

    print("Selecting Football...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, FOOTBALL_XPATH))
    ).click()

    print("Clicking Start a match...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (AppiumBy.ACCESSIBILITY_ID, START_MATCH_ACCESSIBILITY_ID)
        )
    ).click()
    print("Start a match opened successfully")

    print("Selecting Play now...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.XPATH,
                '//android.view.View[@content-desc="Play now\n'
                'Start the match and score it live right away"]',
            )
        )
    ).click()

    print("Continuing to play now...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (AppiumBy.ACCESSIBILITY_ID, "Continue to play now")
        )
    ).click()
    print("Play now flow opened successfully")
    print("Selecting Male...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Male"))
    ).click()

    print("Clicking Select for Your side...")
    click_team_select_button(driver, "your side")

    print("Selecting the first displayed team...")
    click_first_displayed_team(driver)

    print("Confirming team selection...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (AppiumBy.XPATH, '//android.widget.Button[@content-desc="Select Team"]')
        )
    ).click()

    print("Clicking the Back icon...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, "//android.widget.Button"))
    ).click()

    print("Clicking Select for Opponent...")
    click_team_select_button(driver, "opponent")

    print("Searching for opponent team 367...")
    opponent_search = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, "//android.widget.EditText"))
    )
    opponent_search.click()
    opponent_search.send_keys("367")

    opponent_team = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.XPATH,
                "//*[@clickable='true' and "
                "contains(translate(normalize-space(@content-desc), "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
                "'367football team')]",
            )
        )
    )
    opponent_team.click()

    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (AppiumBy.XPATH, '//android.widget.Button[@content-desc="Select Team"]')
        )
    ).click()

    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, "//android.widget.Button"))
    ).click()

    print("Selecting 5 players per team...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "5"))
    ).click()

    duration_locator = (AppiumBy.XPATH, "//android.widget.EditText")
    print("Scrolling up until the Duration field is visible...")
    scroll_up_until_visible(driver, duration_locator, "Duration field")
    duration_field = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(duration_locator)
    )
    duration_field.click()
    duration_field.send_keys("45")

    print("Clicking Done on the keyboard...")
    driver.press_keycode(66)
    if driver.is_keyboard_shown():
        driver.hide_keyboard()
    if driver.is_keyboard_shown():
        raise RuntimeError("The keyboard could not be dismissed")

    venue_locator = (
        AppiumBy.XPATH,
        "//android.view.View[contains(@content-desc, 'VENUE')]",
    )
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(venue_locator)
    ).click()

    print("Searching for venue STBC...")
    venue_search = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, "//android.widget.EditText"))
    )
    venue_search.click()
    venue_search.send_keys("stbc")
    if driver.is_keyboard_shown():
        driver.press_keycode(66)
    if driver.is_keyboard_shown():
        driver.hide_keyboard()
    if driver.is_keyboard_shown():
        raise RuntimeError("The venue search keyboard could not be dismissed")

    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.XPATH,
                "//android.view.View[contains(@content-desc, 'stbc') "
                "and contains(@content-desc, 'Kalluru, Kurnool')]",
            )
        )
    ).click()

    print("Clicking Create match...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (AppiumBy.ACCESSIBILITY_ID, "Create match")
        )
    ).click()
finally:
    driver.quit()
