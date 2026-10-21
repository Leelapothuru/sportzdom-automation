from appium import webdriver
from appium.options.android import UiAutomator2Options


def get_driver():
    options = UiAutomator2Options()

    options.platform_name = "Android"
    options.device_name = "Nothing Phone (3a) - Model A059"
    options.udid = "001613556000110"
    options.automation_name = "UiAutomator2"

    options.app_package = "com.sportzdom.app"
    options.app_activity = ".MainActivity"

    options.no_reset = True
    options.full_reset = False

    options.ignore_hidden_api_policy_error = True

    driver = webdriver.Remote(
        command_executor="http://127.0.0.1:4723",
        options=options
    )

    return driver