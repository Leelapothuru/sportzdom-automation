from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()
driver.back()  # dismiss keyboard

select_type = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Select Type"))
)
select_type.click()

dump_state(driver, "tab1_type_dropdown")

driver.quit()
