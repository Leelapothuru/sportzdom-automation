from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from appium.webdriver.common.appiumby import AppiumBy


class MyProfilePage:

    def __init__(self, driver):
        self.driver = driver

    def click_profile_icon(self):
        profile_icon = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable(
                (
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().className("android.widget.ImageView")'
                )
            )
        )
        profile_icon.click()

    def click_my_connections(self):
        my_connections = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable(
                (AppiumBy.ACCESSIBILITY_ID, "My Connections")
            )
        )
        my_connections.click()

    def open_my_connections(self):
        self.click_profile_icon()
        self.click_my_connections()
