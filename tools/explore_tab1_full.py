import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()


def by_id(label, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, label))
    )


def edit_text(instance, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().className("android.widget.EditText").instance({instance})',
            )
        )
    )


# Modal: choose Single Tournament, then Next
by_id("Single Tournament\nCreate a tournament for one \nsport. Manually set matchups \nand schedule matches").click()
time.sleep(1)
by_id("NEXT").click()
time.sleep(1)

# Tournament Name
edit_text(0).send_keys("Automation Test Tournament")
driver.hide_keyboard()
time.sleep(1)

# Sport -> FootBall
by_id("Select Sport").click()
time.sleep(1)
by_id("FootBall").click()
time.sleep(1)

# Tournament Type -> KnockOut
by_id("Select Type").click()
time.sleep(1)
by_id("KnockOut").click()
time.sleep(1)

# Match Type -> Team
by_id("Select Level").click()
time.sleep(1)
by_id("Team").click()
time.sleep(1)

# Age Group -> Open
by_id("Select Group").click()
time.sleep(1)
by_id("Open").click()
time.sleep(1)

# Category -> Mixed
by_id("Select Category").click()
time.sleep(1)
by_id("Mixed").click()
time.sleep(1)

dump_state(driver, "tab1_full_checkpoint1")

# Area -> District
by_id("Select Area").click()
time.sleep(1)
by_id("District").click()
time.sleep(1)

# State -> Andhra Pradesh
WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select Here").instance(0)')
    )
).click()
time.sleep(1)
by_id("Andhra Pradesh").click()
time.sleep(1)

# District -> Anantapur
WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select Here").instance(0)')
    )
).click()
time.sleep(1)
by_id("Anantapur").click()
time.sleep(1)

dump_state(driver, "tab1_full_checkpoint2")

# City
edit_text(0).send_keys("Kurnool")
driver.hide_keyboard()
time.sleep(1)

# Prizes (re-find indices after each dump to avoid staleness)
edit_text(1).send_keys("5000")
edit_text(2).send_keys("3000")
edit_text(3).send_keys("1000")
driver.hide_keyboard()
time.sleep(1)

dump_state(driver, "tab1_full_checkpoint3")

# Next -> Tab 2
by_id("Next").click()
time.sleep(1)

dump_state(driver, "tab2_landing")

driver.quit()
