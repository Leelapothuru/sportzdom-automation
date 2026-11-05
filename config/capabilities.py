"""Appium capabilities for the Sportzdom Android app."""

from appium.options.android import UiAutomator2Options

from config import settings


def android_options() -> UiAutomator2Options:
    """UiAutomator2 options for the device named in config.settings."""
    options = UiAutomator2Options()

    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = settings.DEVICE_NAME
    if settings.DEVICE_UDID:
        # Without a UDID, Appium uses the only connected device/emulator.
        options.udid = settings.DEVICE_UDID

    options.app_package = settings.APP_PACKAGE
    options.app_activity = settings.APP_ACTIVITY

    options.no_reset = True
    options.full_reset = False
    # Bring the running app to the front instead of force-stopping it when a
    # session starts: a restart shows the fingerprint "Unlock Sportzdom" screen.
    options.set_capability("appium:dontStopAppOnReset", True)
    options.new_command_timeout = settings.NEW_COMMAND_TIMEOUT

    options.ignore_hidden_api_policy_error = True
    return options
