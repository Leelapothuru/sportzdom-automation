import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

team_size = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Team Size").instance(1)')
    )
)
team_size.click()
time.sleep(1)

dump_state(driver, "team_size_dropdown2")

driver.quit()
