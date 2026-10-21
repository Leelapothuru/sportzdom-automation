from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

single_tournament = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Single Tournament")')
    )
)
single_tournament.click()

dump_state(driver, "single_tournament_selected")

next_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "NEXT"))
)
next_button.click()

dump_state(driver, "tournament_form_tab1")

driver.quit()
