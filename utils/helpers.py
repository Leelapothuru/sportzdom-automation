"""Shared locator builders and display-format helpers for page objects and tests."""

from datetime import date

from appium.webdriver.common.appiumby import AppiumBy


def by_label(label):
    return (AppiumBy.ACCESSIBILITY_ID, label)


def by_uia(selector):
    return (AppiumBy.ANDROID_UIAUTOMATOR, selector)


def by_xpath(path):
    return (AppiumBy.XPATH, path)


def description_contains(text):
    return by_uia(f'new UiSelector().descriptionContains("{text}")')


def after_label(label, index=1, element="*"):
    """The index-th element after a form label in document order.

    The wizard renders labels and their inputs as flat siblings, so the input
    for "Match duration (minutes) *" is the first EditText that follows it.
    """
    return by_xpath(f'(//*[@content-desc="{label}"]/following::{element})[{index}]')


def calendar_label(day: date) -> str:
    """Material date-picker label, e.g. '10, Tuesday, November 10, 2026'."""
    return f"{day.day}, {day:%A}, {day:%B} {day.day}, {day.year}"


def review_date(day: date) -> str:
    """Date format used on the Review step, e.g. '10 Nov 2026'."""
    return f"{day.day} {day:%b} {day.year}"


def rupees(amount) -> str:
    return f"₹{int(amount):,}"
