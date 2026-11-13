from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class RoleRegistrationPage:
    MENU_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Menu\nMenu")
    MY_ROLES_MENU_ITEM = (
        AppiumBy.ACCESSIBILITY_ID,
        "My roles\nManage how you take part",
    )
    REGISTER_ROLE_TAB = (
        AppiumBy.ACCESSIBILITY_ID,
        "Register role\nTab 2 of 2",
    )
    SPORT_SELECTOR = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.view.View").instance(22)',
    )
    ROLE_SELECTOR = (AppiumBy.ACCESSIBILITY_ID, "Select role")
    PLAYING_LEVEL_SELECTOR = (AppiumBy.ACCESSIBILITY_ID, "Select playing level")
    EXPERIENCE_ADD_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.Button").instance(5)',
    )
    EDUCATION_SELECTOR = (AppiumBy.ACCESSIBILITY_ID, "Select education")
    STATE_SELECTOR = (AppiumBy.ACCESSIBILITY_ID, "Select state")
    DESCRIPTION_FIELD = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.EditText")',
    )
    DECLARATION_CHECKBOX = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.CheckBox")',
    )
    SUBMIT_APPLICATION_BUTTON = (
        AppiumBy.ACCESSIBILITY_ID,
        "Submit Application",
    )
    SUBMISSION_CONFIRMATION_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Ok")
    SCROLL_VIEW = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.ScrollView")',
    )
    DEFAULT_TIMEOUT = 20
    MAX_SCROLLS = 6

    def __init__(self, driver, timeout=DEFAULT_TIMEOUT):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def open_registration(self):
        self._click(self.MENU_BUTTON)
        self._click(self.MY_ROLES_MENU_ITEM)
        self._click(self.REGISTER_ROLE_TAB)

    def select_sport(self, sport):
        self._click(self.SPORT_SELECTOR)
        self._click((AppiumBy.ACCESSIBILITY_ID, sport))

    def select_role(self, role):
        self._click(self.ROLE_SELECTOR)
        self._click((AppiumBy.ACCESSIBILITY_ID, role))

    def select_playing_level(self, playing_level):
        self._scroll_until_clickable(self.PLAYING_LEVEL_SELECTOR).click()
        self._click((AppiumBy.ACCESSIBILITY_ID, playing_level))

    def add_one_year_experience(self):
        self._click(self.EXPERIENCE_ADD_BUTTON)

    def select_education(self, education):
        self._scroll_until_clickable(self.EDUCATION_SELECTOR).click()
        self._click((AppiumBy.ACCESSIBILITY_ID, education))

    def select_state(self, state):
        self._click(self.STATE_SELECTOR)
        self._click((AppiumBy.ACCESSIBILITY_ID, state))

    def enter_application_description(self, description):
        field = self._scroll_until_clickable(self.DESCRIPTION_FIELD)
        field.click()
        field.clear()
        field.send_keys(description)
        self._dismiss_keyboard()

    def accept_declaration(self):
        self._click(self.DECLARATION_CHECKBOX)

    def submit_application(self):
        self._click(self.SUBMIT_APPLICATION_BUTTON)

    def is_submission_confirmation_displayed(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.SUBMISSION_CONFIRMATION_BUTTON)
        ).is_displayed()

    def confirm_submission(self):
        self._click(self.SUBMISSION_CONFIRMATION_BUTTON)

    def _click(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def _scroll_until_clickable(self, locator):
        for scroll_count in range(self.MAX_SCROLLS + 1):
            try:
                return WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable(locator)
                )
            except TimeoutException:
                if scroll_count == self.MAX_SCROLLS or not self._scroll_form_down():
                    raise

    def _scroll_form_down(self):
        scroll_view = self.driver.find_element(*self.SCROLL_VIEW)
        return self.driver.execute_script(
            "mobile: scrollGesture",
            {
                "elementId": scroll_view.id,
                "direction": "down",
                "percent": 0.7,
            },
        )

    def _dismiss_keyboard(self):
        window_size = self.driver.get_window_size()
        self.driver.execute_script(
            "mobile: clickGesture",
            {
                "x": window_size["width"] // 2,
                "y": window_size["height"] // 10,
            },
        )
