import sys
import time
from pathlib import Path

# Make this script runnable directly with: python tests/test_shop_tabletennis.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from drivers.driver_manager import get_driver
from pages.login_page import LoginPage


driver = get_driver()
login = LoginPage(driver)

try:
    if not login.is_home_page() and not login.is_signin_page():
        for _ in range(8):
            driver.back()
            time.sleep(1)
            if login.is_home_page():
                break

    if login.is_logged_in():
        if not login.is_home_page():
            login.click_home()
    else:
        login.login()
        time.sleep(5)

    if not login.is_home_page():
        raise RuntimeError("Home page was not displayed after login")

    driver.save_screenshot("screenshots/homepage_screen.png")

    print("Clicking Menu using the requested XPath...")
    login.click_menu()
    time.sleep(2)
    driver.save_screenshot("screenshots/menu_screen.png")
    print("Menu clicked successfully")

    print("Searching the Menu for Shop and dismissing the keyboard...")
    login.search_menu("shop")
    time.sleep(1)

    print("Scrolling down and clicking Shop using the requested XPath...")
    login.click_shop()
    time.sleep(3)
    driver.save_screenshot("screenshots/shop_screen.png")
    print("Shop page opened successfully")

    print("Scrolling down to Table Tennis and selecting accessibility ID 'Shop TableTennis'...")
    login.click_shop_item("Shop TableTennis")
    time.sleep(3)
    driver.save_screenshot("screenshots/tabletennis_page.png")
    print("Table Tennis page opened successfully")

    print("Finding Clothing (scrolling if needed) and selecting accessibility ID 'Clothing'...")
    login.click_clothing()
    time.sleep(2)
    driver.save_screenshot("screenshots/clothing_page.png")
    print("Clothing clicked successfully")

    print("Finding Jerseys (scrolling if needed) and selecting accessibility ID 'jerseys'...")
    login.click_shop_item("jerseys")
    time.sleep(2)
    driver.save_screenshot("screenshots/jerseys_page.png")
    print("Jerseys page opened successfully")
finally:
    driver.quit()
