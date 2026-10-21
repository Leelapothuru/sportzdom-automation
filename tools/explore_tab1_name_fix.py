from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

name_field = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText")')
    )
)
name_field.click()
name_field.send_keys("Automation Test Tournament")

dump_state(driver, "tab1_name_fix")

driver.quit()
