import time
from appium.webdriver.common.appiumby import AppiumBy
from tools.helpers import by_id
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

# Click hour "6"
hour6 = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("6")')
hour6.click()
time.sleep(1)

dump_state(driver, "ground_open_hour_set")

driver.quit()
