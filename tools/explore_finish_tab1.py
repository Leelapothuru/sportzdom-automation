import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()


def edit_text(instance, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().className("android.widget.EditText").instance({instance})',
            )
        )
    )


def by_id(label, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, label))
    )


second_prize = edit_text(2)
second_prize.click()
second_prize = edit_text(2)
second_prize.send_keys("3000")
driver.tap([(190, 754)])
time.sleep(1)

dump_state(driver, "tab1_second_prize_filled")

driver.quit()
