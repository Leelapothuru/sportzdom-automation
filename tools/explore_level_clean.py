import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()
driver.back()  # clear any stuck invisible popup
time.sleep(2)

dump_state(driver, "before_level_click")

select_level = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Select Level"))
)
select_level.click()
time.sleep(2)

dump_state(driver, "after_level_click")

driver.quit()
