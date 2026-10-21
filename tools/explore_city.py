import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

city_field = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(1)')
    )
)
city_field.click()

city_field = driver.find_element(
    AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(1)'
)
city_field.send_keys("Kurnool")
driver.back()
time.sleep(1)

dump_state(driver, "after_city_entered")

driver.quit()
