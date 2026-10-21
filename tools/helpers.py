from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def by_id(driver, label, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, label))
    )


def edit_text(driver, instance, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().className("android.widget.EditText").instance({instance})',
            )
        )
    )


def dismiss_keyboard(driver, stable_label):
    """Blur the focused field by tapping a known, non-input label element.

    Never use a hardcoded pixel coordinate here: once a keyboard opens, the
    page scrolls to keep the focused field visible, so any coordinate
    captured from an earlier screenshot is stale and may land on the wrong
    control (e.g. the wizard's Previous/Next buttons instead of a label).
    Clicking an element found by accessibility id always resolves its
    current on-screen position at click time, so it can't go stale.
    """
    by_id(driver, stable_label).click()
