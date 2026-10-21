import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()


def edit_text(instance):
    return WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().className("android.widget.EditText").instance({instance})',
            )
        )
    )


edit_text(1).send_keys("5000")
edit_text(2).send_keys("3000")
edit_text(3).send_keys("1000")

driver.back()
time.sleep(1)

dump_state(driver, "after_prizes_entered")

driver.quit()
