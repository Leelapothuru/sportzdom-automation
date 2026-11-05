import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Make this script runnable directly with: python tests/GOAL_SPORTS.py
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
SCHEDULE_LATER_XPATH = (
    '//android.view.View[@content-desc="Schedule for later\n'
    'Pick a date and time, invite players and officials"]'
)
CONTINUE_TO_SCHEDULE_ACCESSIBILITY_ID = "Continue to schedule"
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
        for candidate in team_rows:
            if not candidate.is_displayed() or not candidate.is_enabled():
                continue

            candidate.click()
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


def scroll_down_until_visible(driver, locator, description, timeout=WAIT_SECONDS):
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
                "direction": "down",
                "percent": 0.65,
            },
        )
        time.sleep(0.3)

    raise RuntimeError("%s was not found after scrolling down" % description)


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
            if (
                login.is_home_page()
                or login.is_signin_page()
                or login.is_logged_in()
            ):
                break

    login_state = login.wait_for_login_state()
    if login_state in ("signin", "signin_entry"):
        login.login()
    elif login_state == "logged_in":
        login.click_home()
    if not login.is_home_page():
        login.wait_for_home_page()

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

    print("Selecting Schedule for later...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, SCHEDULE_LATER_XPATH))
    ).click()

    print("Continuing to schedule...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (AppiumBy.ACCESSIBILITY_ID, CONTINUE_TO_SCHEDULE_ACCESSIBILITY_ID)
        )
    ).click()

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

    date_time_locator = (
        AppiumBy.XPATH,
        '//android.view.View[@content-desc="DATE & TIME\nTap to choose"]',
    )
    print("Scrolling up until Date and Time is visible...")
    scroll_up_until_visible(driver, date_time_locator, "Date and Time section")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(date_time_locator)
    ).click()

    current_time = datetime.now().astimezone()
    match_start = current_time + timedelta(minutes=10)
    if match_start.second or match_start.microsecond:
        match_start = (match_start + timedelta(minutes=1)).replace(
            second=0, microsecond=0
        )

    month_year = match_start.strftime("%B %Y")
    calendar_title = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                "//android.widget.Button[starts-with(@content-desc, 'Select year')]",
            )
        )
    )
    if month_year not in (calendar_title.get_attribute("contentDescription") or ""):
        WebDriverWait(driver, WAIT_SECONDS).until(
            EC.element_to_be_clickable(
                (AppiumBy.ACCESSIBILITY_ID, "Next month")
            )
        ).click()

    target_date_label = "%s, %s %d, %d" % (
        match_start.strftime("%A"),
        match_start.strftime("%B"),
        match_start.day,
        match_start.year,
    )
    print("Selecting match date %s..." % target_date_label)
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.XPATH,
                "//android.widget.Button[contains(@content-desc, %r)]"
                % target_date_label,
            )
        )
    ).click()
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "OK"))
    ).click()

    print("Setting match time to %s..." % match_start.strftime("%I:%M %p"))
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (AppiumBy.ACCESSIBILITY_ID, "Switch to text input mode")
        )
    ).click()
    hour_field = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (AppiumBy.XPATH, "//android.widget.EditText[@hint='Hour']")
        )
    )
    hour_field.click()
    hour_field.clear()
    hour_field.send_keys(str(match_start.hour % 12 or 12))

    minute_field = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (AppiumBy.XPATH, "//android.widget.EditText[@hint='Minute']")
        )
    )
    minute_field.click()
    minute_field.clear()
    minute_field.send_keys(match_start.strftime("%M"))

    expected_hour = str(match_start.hour % 12 or 12)
    if (
        hour_field.get_attribute("text") != expected_hour
        or minute_field.get_attribute("text") != match_start.strftime("%M")
    ):
        raise RuntimeError("The time picker did not accept the requested hour and minute")

    period = "AM" if match_start.hour < 12 else "PM"
    period_button = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, period))
    )
    if period_button.get_attribute("checked") != "true":
        period_button.click()
    if period_button.get_attribute("checked") != "true":
        raise RuntimeError("The time picker did not select %s" % period)

    if driver.is_keyboard_shown():
        driver.press_keycode(66)
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "OK"))
    ).click()

    print("Verifying the saved date and time section...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                "//android.view.View[contains(@content-desc, 'DATE & TIME')]",
            )
        )
    )

    venue_locator = (
        AppiumBy.XPATH,
        "//android.view.View[starts-with(@content-desc, 'VENUE')]",
    )
    print("Scrolling until the Venue section is visible...")
    scroll_up_until_visible(driver, venue_locator, "Venue section")
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

    print("Opening the Referee selector...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Referee"))
    ).click()
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Ok"))
    ).click()

    print("Searching for referee user380...")
    referee_search = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, "//android.widget.EditText"))
    )
    referee_search.click()
    referee_search.clear()
    referee_search.send_keys("380")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.XPATH,
                '//android.widget.ImageView[@content-desc="U\nuser380\nReferee"]',
            )
        )
    ).click()
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Select official"))
    ).click()

    print("Returning from the referee selector...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.XPATH,
                '//android.widget.FrameLayout[@resource-id="android:id/content"]'
                '/android.widget.FrameLayout/android.widget.FrameLayout'
                '/android.view.View/android.view.View/android.view.View'
                '/android.view.View/android.view.View[1]/android.widget.Button',
            )
        )
    ).click()

    print("Opening the Scorer selector...")
    scorer_locator = (AppiumBy.ACCESSIBILITY_ID, "Scorer")
    scroll_down_until_visible(driver, scorer_locator, "Scorer button")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(scorer_locator)
    ).click()
    scorer_search = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, "//android.widget.EditText"))
    )
    scorer_search.click()
    scorer_search.clear()
    scorer_search.send_keys("405")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.XPATH,
                '//android.widget.ImageView[@content-desc="U\nuser405\nScorer"]',
            )
        )
    ).click()
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Select official"))
    ).click()

    print("Returning from the scorer selector...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.XPATH,
                '//android.view.View[@content-desc="Ad Loading... \n\n"]'
                "/android.view.View[1]/android.widget.Button",
            )
        )
    ).click()

    print("Scrolling down until Schedule match is visible...")
    schedule_match_locator = (AppiumBy.ACCESSIBILITY_ID, "Schedule match")
    scroll_down_until_visible(
        driver,
        schedule_match_locator,
        "Schedule match button",
    )
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(schedule_match_locator)
    ).click()

    print("Confirming the schedule...")
    WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Ok"))
    ).click()
    print("Match scheduled successfully")
finally:
    driver.quit()
