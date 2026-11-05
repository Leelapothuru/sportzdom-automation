"""Page object for verifying the Sportzdom Grounds page UI and navigation."""

from pathlib import Path
import os

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class GroundPage:
    """Page object for the Grounds screen and its navigation entry."""

    def __init__(self, driver, timeout: int = 10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    @property
    def menu_button_locators(self):
        return [
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Menu").clickable(true)'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("open").clickable(true)'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.ImageButton").clickable(true)'),
            (AppiumBy.XPATH, "//android.widget.ImageButton[@clickable='true']"),
        ]

    @property
    def grounds_button_locators(self):
        return [
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().descriptionContains("Grounds").clickable(true)',
            ),
            (
                AppiumBy.XPATH,
                '//android.view.View[@clickable="true" and contains(@content-desc, "Grounds")]',
            ),
            (AppiumBy.ACCESSIBILITY_ID, "Grounds"),
            (AppiumBy.XPATH, '//android.widget.ImageView[@content-desc="Grounds"]'),
            (
                AppiumBy.XPATH,
                '//android.widget.ImageView[@content-desc="Grounds"]'
                '/ancestor::*[@clickable="true"][1]',
            ),
        ]

    @property
    def grounds_page_title(self):
        return (AppiumBy.ACCESSIBILITY_ID, "Grounds")

    @property
    def grounds_option_xpath(self):
        return (AppiumBy.XPATH, '//android.widget.ImageView[@content-desc="Grounds"]')

    @property
    def add_button_locator(self):
        return (AppiumBy.XPATH, '//*[@content-desc="Add"]')

    @property
    def add_button_locators(self):
        return [
            self.add_button_locator,
            (AppiumBy.ACCESSIBILITY_ID, "Add"),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Add").clickable(true)'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Add").clickable(true)'),
            (AppiumBy.XPATH, '//*[contains(@content-desc, "Add") and @clickable="true"]'),
        ]

    @property
    def grounds_page_message(self):
        return (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().descriptionContains("Can\'t find your venue?")',
        )

    @property
    def grounds_items(self):
        return (
            AppiumBy.XPATH,
            '//android.view.View[@content-desc and @clickable="true" '
            'and not(contains(@content-desc, "Can\'t find your venue?"))]',
        )

    @property
    def search_ground_field(self):
        return (AppiumBy.CLASS_NAME, "android.widget.EditText")

    @property
    def registration_title(self):
        return (AppiumBy.ACCESSIBILITY_ID, "Grounds Registration")

    @property
    def register_button(self):
        return (AppiumBy.ACCESSIBILITY_ID, "Register")

    @property
    def success_ok_button(self):
        return (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Ok")')

    @property
    def ground_name_field(self):
        return (AppiumBy.XPATH, '//*[@content-desc="GROUND NAME"]/following::android.widget.EditText[1]')

    @property
    def type_dropdown(self):
        return (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select...")')

    @property
    def state_dropdown(self):
        return (AppiumBy.XPATH, '(//android.widget.Button[@content-desc="Select..."])[1]')

    @property
    def district_dropdown(self):
        return (AppiumBy.XPATH, '(//android.widget.Button[@content-desc="Select..."])[1]')

    @property
    def city_field(self):
        return (AppiumBy.XPATH, '//android.widget.EditText[@hint="select city"]')

    @property
    def landmark_field(self):
        return (AppiumBy.XPATH, '//*[@content-desc="LANDMARK"]/following::android.widget.EditText[1]')

    @property
    def pricing_field(self):
        return (AppiumBy.XPATH, '//*[@content-desc="PRICE FOR BOOKING"]/following::android.widget.EditText[1]')

    @property
    def owner_name_field(self):
        return (AppiumBy.XPATH, '//*[@content-desc="OWNER NAME"]/following::android.widget.EditText[1]')

    @property
    def description_field(self):
        return (AppiumBy.XPATH, '//android.widget.EditText[@hint="Description"]')

    @property
    def ground_preview(self):
        return (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Ground")')

    @property
    def location_preview(self):
        return (AppiumBy.ACCESSIBILITY_ID, "Current Location")

    def _click(self, locator):
        element = self.wait.until(EC.element_to_be_clickable(locator))
        element.click()

    def _try_click_any(self, locators, timeout=None):
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        for locator in locators:
            try:
                wait.until(EC.element_to_be_clickable(locator)).click()
                return True
            except TimeoutException:
                continue
        return False

    def _scroll_to_element(self, locator):
        try:
            return self.wait.until(EC.presence_of_element_located(locator))
        except TimeoutException:
            self.driver.swipe(300, 1400, 300, 400, 800)
            return self.wait.until(EC.presence_of_element_located(locator))

    def _is_visible(self, locator):
        try:
            return self.wait.until(EC.visibility_of_element_located(locator)).is_displayed()
        except TimeoutException:
            return False

    def _is_any_visible(self, locators):
        return any(self._is_visible(locator) for locator in locators)

    def _press_done(self):
        try:
            self.driver.execute_script("mobile: performEditorAction", {"action": "done"})
        except Exception:
            self.driver.press_keycode(66)

    def _dismiss_keyboard(self):
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

    def _type(self, locator, value):
        element = self.wait.until(EC.visibility_of_element_located(locator))
        element.click()
        try:
            element.clear()
        except Exception:
            pass
        element.send_keys(str(value))
        self._press_done()

    def _type_after_scroll(self, locator, value):
        for _ in range(6):
            try:
                element = self.driver.find_element(*locator)
                if element.is_displayed() and element.is_enabled():
                    self._type(locator, value)
                    return
            except Exception:
                pass
            self.driver.swipe(360, 1350, 360, 650, 500)
        self._type(locator, value)

    def _click_after_scroll(self, locator):
        for _ in range(6):
            try:
                element = self.driver.find_element(*locator)
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    return
            except Exception:
                pass
            self.driver.swipe(360, 1350, 360, 650, 500)
        raise TimeoutException(f"Unable to find registration control: {locator}")

    def _select_option(self, value):
        locators = [
            (AppiumBy.ACCESSIBILITY_ID, value),
            (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().description("{value}")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{value}")'),
        ]
        if not self._try_click_any(locators):
            raise TimeoutException(f"Unable to select form option: {value}")

    def _scroll_and_select(self, text):
        locators = [
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiScrollable(new UiSelector().scrollable(true))'
                f'.scrollIntoView(new UiSelector().text("{text}"));',
            ),
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiScrollable(new UiSelector().scrollable(true))'
                f'.scrollIntoView(new UiSelector().description("{text}"));',
            ),
        ]
        if not self._try_click_any(locators):
            raise TimeoutException(f"Unable to select location option: {text}")

    def enter_city_and_select_suggestion(self, city):
        """Type a city prefix and select the matching autocomplete suggestion."""
        field = self.wait.until(EC.visibility_of_element_located(self.city_field))
        field.click()
        try:
            field.clear()
        except Exception:
            pass
        field.send_keys(city.strip())

        suggestion_locator = (AppiumBy.ACCESSIBILITY_ID, city)
        try:
            self.wait.until(EC.element_to_be_clickable(suggestion_locator)).click()
        except TimeoutException:
            suggestion_locators = [
                (
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().text("{city}").clickable(true)',
                ),
                (
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().description("{city}").clickable(true)',
                ),
                (AppiumBy.XPATH, f'//*[@content-desc="{city}" and @clickable="true"]'),
            ]
            self._try_click_any(suggestion_locators, timeout=5)

        self._dismiss_keyboard()
        try:
            self.wait.until(EC.presence_of_element_located(self.landmark_field))
        except TimeoutException:
            self.driver.back()
            self.wait.until(EC.presence_of_element_located(self.landmark_field))

    def navigate_to_grounds_page(self):
        """Open the navigation menu and tap the Grounds entry."""
        if self.verify_registration_page_displayed():
            self._dismiss_keyboard()
            self.driver.back()
            if self.verify_grounds_page_displayed():
                return

        if self.verify_grounds_page_displayed():
            return

        self.driver.activate_app(os.getenv("SPORTZDOM_APP_PACKAGE", "com.sportzdom.app"))
        try:
            WebDriverWait(self.driver, 45).until(
                lambda driver: any(
                    driver.find_elements(*locator)
                    for locator in self.menu_button_locators
                )
            )
        except TimeoutException as exc:
            self._dump_page_source("grounds_app_startup_failure")
            raise TimeoutException("Sportzdom did not finish loading its menu") from exc

        if not self._try_click_any(self.menu_button_locators):
            raise TimeoutException("Unable to open the navigation menu")

        if self._try_click_any(self.grounds_button_locators, timeout=2):
            return

        self.driver.swipe(500, 1200, 500, 650, 700)
        if not self._try_click_any(self.grounds_button_locators, timeout=2):
            self._dump_page_source("grounds_navigation_failure")
            raise TimeoutException("Unable to find the Grounds entry in the navigation menu")

    def _dump_page_source(self, prefix: str = 'grounds'):
        try:
            Path('screenshots').mkdir(exist_ok=True)
            filename = Path('screenshots') / f'{prefix}_page_source.xml'
            filename.write_text(self.driver.page_source, encoding='utf-8')
        except Exception:
            pass

    def verify_grounds_page_displayed(self):
        """Verify that the Grounds page is displayed."""
        return self._is_visible(self.grounds_page_title) or self._is_visible(self.grounds_page_message)

    def verify_all_ui_elements_visible(self):
        """Verify that the key UI elements on the Grounds page are visible."""
        return all(
            [
                self.verify_grounds_page_displayed(),
                self._is_any_visible(self.add_button_locators),
                self._is_visible(self.search_ground_field),
            ]
        )

    def verify_all_grounds_are_visible(self):
        """Verify that all grounds items visible on the page are displayed."""
        try:
            grounds = self.driver.find_elements(*self.grounds_items)
            return bool(grounds) and all(element.is_displayed() for element in grounds)
        except Exception as exc:
            raise AssertionError("One or more grounds items are not visible") from exc

    def verify_navigation_successful(self):
        """Verify that navigation to the Grounds page succeeded."""
        return self.verify_grounds_page_displayed()

    def open_registration_from_grounds(self):
        """Open the ground registration form from the Grounds page."""
        try:
            if not self._try_click_any(self.add_button_locators):
                raise TimeoutException("Add button was not found on the Grounds page")
            self.wait.until(EC.visibility_of_element_located(self.registration_title))
            return self
        except TimeoutException as exc:
            raise TimeoutException("Unable to open the ground registration form") from exc

    def verify_registration_page_displayed(self):
        """Verify the ground registration form is displayed."""
        return self._is_visible(self.registration_title)

    def enter_ground_name(self, ground_name):
        """Enter the name for the new ground."""
        self._type(self.ground_name_field, ground_name)

    def select_ground_type(self, ground_type="Public"):
        """Select the ground access type from the form."""
        self._click(self.type_dropdown)
        self._select_option(ground_type)

    def select_environment(self, environment="Outdoor"):
        """Select the ground environment from the form."""
        locator = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().description("{environment}")')
        self._click_after_scroll(locator)

    def _set_location(self, state, district, city, landmark):
        """Use live location and verify the resulting location preview."""
        for description in ("Get Live Location", "Update Location"):
            locator = (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().description("{description}")',
            )
            self._click_after_scroll(locator)

        if self.driver.find_elements(*self.state_dropdown):
            self._click_after_scroll(self.state_dropdown)
            self._scroll_and_select(state)
            self._click_after_scroll(self.district_dropdown)
            self._scroll_and_select(district)
            self.enter_city_and_select_suggestion(city)
            self._dismiss_keyboard()
        self.enter_landmark(landmark)

    def enter_landmark(self, landmark):
        """Enter the ground's landmark."""
        self._type_after_scroll(self.landmark_field, landmark)

    def enter_pricing(self, amount):
        """Enter the booking price."""
        self._type_after_scroll(self.pricing_field, amount)

    def enter_owner_name(self, owner_name):
        """Enter the ground owner's name."""
        self._type_after_scroll(self.owner_name_field, owner_name)

    def enter_description(self, description):
        """Tap the description field, enter its text, and dismiss the keyboard."""
        self._type_after_scroll(self.description_field, description)
        self._dismiss_keyboard()

    def verify_registration_preview_visible(self):
        """Verify the ground preview is visible before submission."""
        return self._is_visible(self.ground_preview)

    def submit_registration(self):
        """Enable Register with one tap, then tap again to submit."""
        self._dismiss_keyboard()
        register = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located(self.register_button)
        )
        rect = register.rect
        self.driver.execute_script(
            "mobile: clickGesture",
            {
                "x": rect["x"] + rect["width"] // 2,
                "y": rect["y"] + rect["height"] // 2,
            },
        )

        register = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable(self.register_button)
        )
        register.click()
        self._click(self.success_ok_button)

    def register_ground(
        self,
        ground_name,
        state,
        district,
        city,
        landmark="near petrol bunk",
        pricing=500,
        owner_name="Sportzdom Owner",
        description="best grounds",
        ground_type="Public",
        environment="Outdoor",
    ):
        """Complete and submit the ground registration form."""
        if not self.verify_registration_page_displayed():
            self.open_registration_from_grounds()

        self.enter_ground_name(ground_name)
        self.select_ground_type(ground_type)
        self.select_environment(environment)
        self._set_location(state, district, city, landmark)
        self.enter_description(description)

        if not self.verify_registration_preview_visible():
            raise AssertionError("Ground and location previews are not visible")

        self.submit_registration()
        return True
