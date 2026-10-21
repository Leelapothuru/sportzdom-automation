from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

nav_tournaments = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Tournaments"))
)
nav_tournaments.click()

dump_state(driver, "tournaments_page")

driver.quit()
