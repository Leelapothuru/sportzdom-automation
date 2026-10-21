import sys
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

label = sys.argv[1]
dump_name = sys.argv[2]

driver = get_driver()

el = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, label))
)
el.click()

dump_state(driver, dump_name)

driver.quit()
