import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

teams_count = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Teams Count").instance(0)')
    )
)
teams_count.click()
time.sleep(1)

dump_state(driver, "teams_count_dropdown")

driver.quit()
