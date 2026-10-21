import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

driver.hide_keyboard()
time.sleep(1)

next_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Next"))
)
next_button.click()
time.sleep(1)

dump_state(driver, "back_on_tab2")

driver.quit()
