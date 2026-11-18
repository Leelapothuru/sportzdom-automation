"""Creates Appium sessions for the Sportzdom Android app."""

from appium import webdriver

from config import settings
from config.capabilities import android_options


def get_driver() -> webdriver.Remote:
    """Start an Appium session on the configured device."""
    driver = webdriver.Remote(command_executor=settings.APPIUM_URL, options=android_options())
    # UiAutomator2 driver 8.1.0 crashes ("Cannot set AccessibilityNodeInfo's
    # field 'mSealed'") when it adds an on-screen toast to the page source on
    # this device. The tests do not read toasts, so switch the listener off.
    driver.update_settings({"enableNotificationListener": False})
    return driver
