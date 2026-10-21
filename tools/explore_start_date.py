import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

start_date = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select Date").instance(0)')
    )
)
start_date.click()
time.sleep(1)

dump_state(driver, "start_date_picker")

driver.quit()
