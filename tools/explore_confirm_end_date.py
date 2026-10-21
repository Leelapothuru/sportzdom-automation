import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

day7 = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (AppiumBy.ACCESSIBILITY_ID, "7, Monday, September 7, 2026")
    )
)
day7.click()
time.sleep(1)

ok_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "OK"))
)
ok_button.click()
time.sleep(1)

dump_state(driver, "after_end_date_ok")

driver.quit()
