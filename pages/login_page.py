
import time




from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from appium.webdriver.common.appiumby import AppiumBy

class LoginPage:
    
    def __init__(self, driver):
        self.driver = driver

    def click_signin_text(self):
        signin = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable(
                (AppiumBy.ACCESSIBILITY_ID, "Sign In")
            )
        )

        signin.click()

    def click_checkbox(self):
        # time.sleep(5)

        checkbox = self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.CheckBox")'
        )
        checkbox.click()
    
    def click_emailfield(self):
      

        click_emailField = self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.EditText")'
        )
        click_emailField.click()

    def enter_email(self, email):
        email_field = self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.EditText")'
        )
        email_field.send_keys(email)

    def click_passwordfield(self):
      

        click_password_field = self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.EditText").instance(1)'
        )
        click_password_field.click()

    def enter_password(self, password):
        password_field = self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.EditText").instance(1)'
        )
        password_field.send_keys(password)

    def click_signin_button(self):
        signin_button = self.driver.find_element(
            AppiumBy.ACCESSIBILITY_ID,
            "Sign in"
        )
        signin_button.click()

