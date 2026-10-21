import time
from appium.webdriver.common.appiumby import AppiumBy

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

# Real coordinate tap (not accessibility click) at center of the "Select Level" field
driver.tap([(773, 1401)])
time.sleep(2)

dump_state(driver, "level_after_coord_tap")

driver.quit()
