"""Page object for creating a badminton singles match from Play Now."""

from __future__ import annotations

import re
import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SetMatchCreation:
    """Create a badminton set match with category, opponent, sets, and ground selection."""

    # Home page locators
    AD_LOADING = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Ad Loading... ")')
    PLAY_ICON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().description("Play\nPlay")',
    )
    HOME_TAB = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Home\nHome")')
    
    # Sport selection
    BADMINTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Badminton")')
    PLAY_BUTTON_AFTER_FLIP = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Play").instance(1)')
    
    # Play mode selection
    CONTINUE_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Continue")')
    PLAY_NOW_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Play Now")')
    CURRENT_PLAY_NOW_OPTION = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionContains("Play now")',
    )
    CURRENT_CONTINUE_PLAY_NOW = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().description("Continue to play now")',
    )
    CURRENT_START_MATCH = (
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Start a match")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Start a Match")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Start a match")'),
    )
    
    # Match creation page locators
    SELECT_CATEGORY_DROPDOWN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select Category")')
    SINGLES_OPTION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Singles")')
    DOUBLES_OPTION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Doubles")')
    
    # Opponent selection
    OPPONENT_SECTION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.view.View").instance(10)')
    SELECT_PLAYER_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select Player")')
    CURRENT_OPPONENT_CARD = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionContains("Tap Opponent to pick who you play against.")',
    )
    CURRENT_OPPONENT_CARD_LABEL = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionContains("Opponent")',
    )
    CURRENT_MALE_OPTION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Male")')
    CURRENT_MIXED_OPTION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Mixed")')
    CURRENT_PLAYER_STATS_CLOSE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Close")')
    BACK_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.Button")')
    CURRENT_VENUE_LOCATORS = (
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("VENUE")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("VENUE")'),
    )
    
    # Set and ground selection
    SELECT_SET_DROPDOWN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select set")')
    SELECT_GROUND_DROPDOWN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select Ground")')
    CREATE_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Create")')
    CURRENT_CREATE_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().description("Create match")',
    )
    
    # Success indicators
    MATCH_CREATED_CONFIRMATION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Match Created")')

    def __init__(self, driver, timeout: int = 15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.selected_opponent: str | None = None
        self.selected_ground: str | None = None
        self._create_screen_source: str | None = None

    def _click(self, locator) -> None:
        """Click element with wait."""
        try:
            self.wait.until(EC.element_to_be_clickable(locator)).click()
        except TimeoutException as e:
            print(f"❌ Element not found: {locator}")
            raise

    def _element_exists(self, locator, timeout: int = 5) -> bool:
        """Check if element exists without failing."""
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def _has_visible_element(self, locator) -> bool:
        for element in self.driver.find_elements(*locator):
            try:
                if element.is_displayed():
                    return True
            except StaleElementReferenceException:
                continue
        return False

    def _click_first_visible(self, locators, label: str) -> None:
        for locator in locators:
            if self._has_visible_element(locator):
                self._click(locator)
                return
        raise TimeoutException(f"{label} was not visible")

    def _is_current_match_setup(self) -> bool:
        source = self.driver.page_source
        return "Create match" in source and (
            "Match setup" in source or "Pick an opponent" in source
        )

    def _is_current_flow_screen(self) -> bool:
        source = self.driver.page_source
        return any(
            label in source
            for label in (
                "Select Whom To Play",
                "Choose a category",
                "New match",
                "Pick an opponent",
                "Start a match",
                "PLAYER STATS",
                "1 PLAYER",
                "Play - Badminton",
            )
        )

    def _select_first_current_opponent(self) -> None:
        def find_opponent(_driver):
            for element in self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().clickable(true)',
            ):
                try:
                    if not element.is_displayed() or not element.is_enabled():
                        continue
                    label = (
                        element.text
                        or element.get_attribute("content-desc")
                        or ""
                    ).strip()
                    if re.search(r"\buser[\w.]*\b", label, re.IGNORECASE):
                        return element, label
                except StaleElementReferenceException:
                    continue
            return False

        try:
            selected = self.wait.until(find_opponent)
        except TimeoutException as exc:
            raise TimeoutException("No available opponent was visible in the picker") from exc

        element, label = selected
        element.click()
        self.selected_opponent = next(
            (
                line.strip()
                for line in label.splitlines()
                if re.search(r"\buser[\w.]*\b", line, re.IGNORECASE)
            ),
            label,
        )
        if self._has_visible_element(self.SELECT_PLAYER_BUTTON):
            self._click(self.SELECT_PLAYER_BUTTON)

    def _return_from_current_opponent_picker(self) -> None:
        source = self.driver.page_source
        if "PLAYER STATS" in source:
            if self._has_visible_element(self.SELECT_PLAYER_BUTTON):
                self._click(self.SELECT_PLAYER_BUTTON)
            elif self._has_visible_element(self.CURRENT_PLAYER_STATS_CLOSE):
                self._click(self.CURRENT_PLAYER_STATS_CLOSE)
            else:
                raise TimeoutException("Opponent stats did not expose a selection or close control")

        if not self._is_current_match_setup():
            if "1 PLAYER" not in self.driver.page_source:
                raise TimeoutException("Opponent picker did not return to the player list")
            self.click_back_button()
        self.wait.until(lambda _driver: self._is_current_match_setup())

    def _select_current_opponent(self) -> None:
        source = self.driver.page_source
        if "PLAYER STATS" in source:
            name = re.search(r"user[\w.]*", source, re.IGNORECASE)
            if name:
                self.selected_opponent = name.group(0)
            self._return_from_current_opponent_picker()
            return

        if "1 PLAYER" in source:
            self._select_first_current_opponent()
            self._return_from_current_opponent_picker()
            return

        if not self._is_current_match_setup():
            raise TimeoutException("Current opponent picker was not open")

        if "Tap Opponent to pick who you play against." not in source:
            selected_name = re.search(r"\buser[\w.]*\b", source, re.IGNORECASE)
            if selected_name:
                self.selected_opponent = selected_name.group(0)
            return

        opponent_card = None
        for locator in (self.CURRENT_OPPONENT_CARD, self.CURRENT_OPPONENT_CARD_LABEL):
            opponent_card = next(
                (
                    element
                    for element in self.driver.find_elements(*locator)
                    if element.is_displayed() and element.is_enabled()
                ),
                None,
            )
            if opponent_card:
                break
        if opponent_card is None:
            raise TimeoutException("Opponent card was not visible in match setup")

        bounds = opponent_card.rect
        self.driver.execute_script(
            "mobile: clickGesture",
            {
                "x": bounds["x"] + round(bounds["width"] * 0.76),
                "y": bounds["y"] + round(bounds["height"] * 0.69),
            },
        )
        self.wait.until(lambda _driver: "1 PLAYER" in self.driver.page_source)
        self._select_first_current_opponent()
        self._return_from_current_opponent_picker()

    def _select_current_ground(self, ground_name: str | None = None) -> str:
        """Scroll to the venue card and select a listed ground."""
        venue = None
        venue_label = ""
        for _ in range(6):
            for locator in self.CURRENT_VENUE_LOCATORS:
                venue = next(
                    (
                        element
                        for element in self.driver.find_elements(*locator)
                        if element.is_displayed()
                        and element.is_enabled()
                        and (
                            "TAP TO CHOOSE"
                            in (
                                element.text
                                or element.get_attribute("content-desc")
                                or ""
                            ).upper()
                            or re.search(
                                r"(?m)^\s*VENUE\s*$",
                                (
                                    element.text
                                    or element.get_attribute("content-desc")
                                    or ""
                                ),
                                re.IGNORECASE,
                            )
                        )
                    ),
                    None,
                )
                if venue:
                    if hasattr(self.driver, "get_window_size") and hasattr(
                        venue, "rect"
                    ):
                        minimum_height = self.driver.get_window_size()["height"] * 0.08
                        if venue.rect.get("height", 0) < minimum_height:
                            venue = None
                    if venue:
                        venue_label = (
                            venue.text or venue.get_attribute("content-desc") or ""
                        )
                        break
            if venue:
                break
            window = self.driver.get_window_size()
            self.driver.swipe(
                window["width"] // 2,
                round(window["height"] * 0.8),
                window["width"] // 2,
                round(window["height"] * 0.35),
                450,
            )
        if venue is None:
            raise TimeoutException("Venue card was not visible after scrolling the match setup")

        if "TAP TO CHOOSE" not in venue_label.upper():
            lines = [line.strip() for line in venue_label.splitlines() if line.strip()]
            try:
                venue_index = next(
                    index for index, line in enumerate(lines) if line.upper() == "VENUE"
                )
                selected_ground = lines[venue_index + 1]
            except (StopIteration, IndexError) as exc:
                raise TimeoutException("Selected venue name was not readable") from exc
            if ground_name and ground_name.casefold() not in selected_ground.casefold():
                raise TimeoutException(
                    f"Selected ground '{selected_ground}' does not match '{ground_name}'"
                )
            self.selected_ground = selected_ground
            return selected_ground

        venue.click()

        def available_grounds(_driver):
            options = []
            for element in self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().clickable(true)',
            ):
                try:
                    if not element.is_displayed() or not element.is_enabled():
                        continue
                    label = (
                        element.text
                        or element.get_attribute("content-desc")
                        or ""
                    ).strip()
                    if (
                        label
                        and "\n" in label
                        and "TAP TO CHOOSE" not in label.upper()
                        and not re.search(
                            r"(?m)^\s*VENUE\s*$", label, re.IGNORECASE
                        )
                        and "NOT LISTED" not in label.upper()
                        and "ADD A NEW VENUE" not in label.upper()
                    ):
                        options.append((element, label))
                except StaleElementReferenceException:
                    continue
            return options or False

        try:
            options = self.wait.until(available_grounds)
        except TimeoutException as exc:
            raise TimeoutException("No available venue or ground was listed") from exc

        selected = next(
            (
                option
                for option in options
                if ground_name and ground_name.casefold() in option[1].casefold()
            ),
            None,
        )
        if ground_name and selected is None:
            raise TimeoutException(f"Ground '{ground_name}' was not available in the venue list")
        if selected is None:
            selected = options[0]

        selected[0].click()
        self.wait.until(lambda _driver: self._is_current_match_setup())
        self.selected_ground = selected[1].splitlines()[0].strip()
        return self.selected_ground

    def close_ad_loading(self) -> None:
        """Close ad loading popup if present."""
        print("📍 Checking for ad loading popup...")
        if self._element_exists(self.AD_LOADING, timeout=3):
            try:
                self._click(self.AD_LOADING)
                print("✓ Ad loading closed")
            except Exception as e:
                print(f"⚠ Could not close ad: {e}")
        else:
            print("⚠ No ad loading found")

    def click_play_icon(self) -> None:
        """Click Play icon from home page."""
        print("📍 Clicking Play icon...")
        self._click(self.PLAY_ICON)
        print("✓ Play icon clicked")
        time.sleep(2)

    def select_badminton_sport(self) -> None:
        """Select Badminton as the sport."""
        print("📍 Selecting Badminton sport...")
        self._click(self.BADMINTON)
        print("✓ Badminton selected")
        time.sleep(2)

    def click_play_button_after_card_flip(self) -> None:
        """Click Play button after card flip animation."""
        print("📍 Clicking Play button after card flip...")
        self._click(self.PLAY_BUTTON_AFTER_FLIP)
        print("✓ Play button clicked")
        time.sleep(2)

    def select_play_myself(self) -> None:
        """Select 'Play Myself' option and click Continue."""
        print("📍 Selecting 'Play Myself' option...")
        self._click(self.CONTINUE_BUTTON)
        print("✓ Play Myself selected")
        time.sleep(2)

    def click_play_now(self) -> None:
        """Click Play Now button to proceed."""
        print("📍 Clicking Play Now button...")
        try:
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(self.PLAY_NOW_BUTTON)
            ).click()
            print("✓ Play Now clicked")
        except TimeoutException:
            print("❌ Play Now button not found. Trying alternative approaches...")
            raise
        time.sleep(2)

    def proceed_to_create_match_page(self) -> None:
        """Click Continue to navigate to create match page."""
        print("📍 Proceeding to Create Match page...")
        self._click(self.CONTINUE_BUTTON)
        print("✓ Navigated to Create Match page")
        time.sleep(2)

    def select_category(self, category: str = "Singles") -> None:
        """Select match category (Singles or Doubles).
        
        Args:
            category: Match type - "Singles" or "Doubles"
        """
        print(f"📍 Selecting {category} category...")
        self._click(self.SELECT_CATEGORY_DROPDOWN)
        print("✓ Category dropdown opened")
        time.sleep(1)
        
        if category.lower() == "singles":
            self._click(self.SINGLES_OPTION)
            print("✓ Singles category selected")
        elif category.lower() == "doubles":
            self._click(self.DOUBLES_OPTION)
            print("✓ Doubles category selected")
        else:
            raise ValueError(f"Invalid category: {category}")
        
        time.sleep(1)

    def select_opponent(self, opponent_username: str | None = None) -> None:
        """Select the first available generated user (``user100``-``user1000``).

        ``opponent_username`` is retained only for backward-compatible callers;
        it is intentionally not used to choose the player.
        """
        print("📍 Selecting an available opponent...")
        
        # Click on opponent section
        self._click(self.OPPONENT_SECTION)
        print("✓ Opponent section clicked")
        time.sleep(1)
        
        available_user_pattern = r".*user([1-9][0-9]{2}|1000).*"
        available_user_locators = [
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textMatches("{available_user_pattern}")',
            ),
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().descriptionMatches("{available_user_pattern}")',
            ),
        ]

        for user_locator in available_user_locators:
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(user_locator)
                )
                selected_opponent = (
                    element.text
                    or element.get_attribute("content-desc")
                    or "available user"
                )
                element.click()
                self.selected_opponent = selected_opponent
                print(f"✓ Opponent {selected_opponent} selected")
                break
            except TimeoutException:
                continue
        else:
            raise TimeoutException("No available user100-user1000 opponent found")
        
        time.sleep(1)

    def click_select_player_button(self) -> None:
        """Click Select Player button to confirm opponent."""
        print("📍 Clicking Select Player button...")
        self._click(self.SELECT_PLAYER_BUTTON)
        print("✓ Select Player confirmed")
        time.sleep(2)

    def click_back_button(self) -> None:
        """Click back button to return to previous screen."""
        print("📍 Clicking back button...")
        self._click(self.BACK_BUTTON)
        print("✓ Back button clicked")
        time.sleep(1)

    def select_sets(self, sets: str = "3") -> None:
        """Select number of sets.
        
        Args:
            sets: Number of sets - "1", "3", "5", or "7"
        """
        print(f"📍 Selecting {sets} sets...")
        self._click(self.SELECT_SET_DROPDOWN)
        print("✓ Set dropdown opened")
        time.sleep(1)
        
        # Create locator for the set value
        set_locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().description("{sets}")'
        )
        self._click(set_locator)
        print(f"✓ {sets} sets selected")
        time.sleep(1)

    def select_ground(self, ground_name: str | None = None) -> None:
        """Select the first available ground option.

        ``ground_name`` is retained only for backward-compatible callers; it
        is intentionally not used to choose the ground.
        """
        print("📍 Selecting an available ground...")
        self._click(self.SELECT_GROUND_DROPDOWN)
        print("✓ Ground dropdown opened")
        time.sleep(1)

        known_available_ground = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().description("subba Reddy ground ")',
        )
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(known_available_ground)
            ).click()
            print("✓ Ground subba Reddy ground selected")
            time.sleep(1)
            return
        except TimeoutException:
            print("Known ground is unavailable; selecting another available ground...")

        # Native dropdowns usually expose options as CheckedTextViews; other
        # app builds use clickable TextViews or Views.
        option_locators = [
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.CheckedTextView")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.TextView").clickable(true)'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.view.View").clickable(true)'),
        ]

        def first_clickable_option(driver):
            for option_locator in option_locators:
                for element in driver.find_elements(*option_locator):
                    if element.is_displayed() and element.is_enabled():
                        return element
            return False

        try:
            element = WebDriverWait(self.driver, 5).until(first_clickable_option)
            selected_ground = (
                element.text
                or element.get_attribute("content-desc")
                or "available ground"
            )
            element.click()
            print(f"✓ Ground {selected_ground} selected")
        except TimeoutException as exc:
            raise TimeoutException("No available ground option found") from exc
        time.sleep(1)

    def create_match(self) -> None:
        """Click Create button to finalize match creation."""
        print("📍 Clicking Create button...")
        self._create_screen_source = self.driver.page_source
        self._click(self.CREATE_BUTTON)
        print("✓ Create button clicked")
        time.sleep(2)

    def verify_match_created(self) -> bool:
        """Verify the generic post-creation screen, not a fixture username."""
        print("📍 Verifying match creation...")
        if self._element_exists(self.MATCH_CREATED_CONFIRMATION, timeout=5):
            print("✓ Match created successfully!")
            return True

        # Success screens vary by app build.  They may show a confirmation,
        # match details, or a match list containing the selected player.
        success_locators = [
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Match Created")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Match Created")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Match Details")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Match Details")'),
        ]
        if self.selected_opponent:
            success_locators.extend([
                (
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{self.selected_opponent}")',
                ),
                (
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().descriptionContains("{self.selected_opponent}")',
                ),
            ])

        if any(self._element_exists(locator, timeout=2) for locator in success_locators):
            print("✓ Match created successfully!")
            return True

        current_source = self.driver.page_source
        create_button_still_visible = self._element_exists(self.CREATE_BUTTON, timeout=1)
        if (
            self._create_screen_source
            and current_source != self._create_screen_source
            and not create_button_still_visible
        ):
            print("✓ Match creation navigated to a new screen")
            return True

        print("⚠ Could not verify match creation")
        return False

    def complete_match_creation_flow(
        self,
        category: str = "Singles",
        opponent: str | None = None,
        sets: str = "3",
        ground: str | None = None,
        match_type: str = "Male",
    ) -> None:
        """Complete entire match creation flow.
        
        Args:
            category: Match category - "Singles" or "Doubles"
            opponent: Ignored; retained for backward compatibility.
            sets: Number of sets - "1", "3", "5", or "7"
            ground: Ignored; retained for backward compatibility.
            match_type: Singles type - "Male" or "Mixed" on the current setup screen.
        """
        print("\n" + "="*70)
        print("🚀 STARTING SET MATCH CREATION FLOW")
        print("="*70 + "\n")
        
        try:
            if (
                self._is_current_flow_screen()
                or self._has_visible_element(self.PLAY_ICON)
                or self._has_visible_element(self.HOME_TAB)
            ):
                self._complete_current_match_creation_flow(category, sets, match_type, ground)
                return

            # Home page steps
            self.close_ad_loading()
            self.click_play_icon()
            self.select_badminton_sport()
            self.click_play_button_after_card_flip()
            
            # Play mode selection
            self.select_play_myself()
            self.click_play_now()
            self.proceed_to_create_match_page()
            
            # Match creation page
            self.select_category(category)
            self.select_opponent(opponent)
            self.click_select_player_button()
            self.click_back_button()
            self.select_sets(sets)
            self.select_ground(ground)
            self.create_match()
            
            # verification
            if self.verify_match_created():
                print("\n" + "="*70)
                print("✅ MATCH CREATION COMPLETED SUCCESSFULLY")
                print("="*70)
                print(f"📊 Summary:")
                print(f"   - Sport: Badminton")
                print(f"   - Category: {category}")
                print("   - Opponent: first available user")
                print(f"   - Sets: {sets}")
                print("   - Ground: first available ground")
                print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ Flow failed: {e}")
            raise

    def _complete_current_match_creation_flow(
        self,
        category: str,
        sets: str,
        match_type: str = "Male",
        ground: str | None = None,
    ) -> None:
        """Create a match using the current Sportzdom match-setup screens."""
        self.close_ad_loading()

        source = self.driver.page_source
        if "PLAYER STATS" in source or "1 PLAYER" in source:
            self._select_current_opponent()
            source = self.driver.page_source

        if not self._is_current_match_setup() and "Select Whom To Play" not in source:
            if "1 PLAYER" not in source:
                if self._has_visible_element(self.CURRENT_START_MATCH[0]) or self._has_visible_element(
                    self.CURRENT_START_MATCH[1]
                ):
                    self._click_first_visible(self.CURRENT_START_MATCH, "Start a match")
                else:
                    if self._has_visible_element(self.HOME_TAB):
                        self._click(self.HOME_TAB)
                    if not self._has_visible_element(self.PLAY_ICON):
                        self.driver.back()
                    self._click(self.PLAY_ICON)
                    self.select_badminton_sport()
                    self._click_first_visible(self.CURRENT_START_MATCH, "Start a match")

        if not self._is_current_match_setup():
            if "Select Whom To Play" in self.driver.page_source:
                self._click(self.CURRENT_PLAY_NOW_OPTION)
                self._click(self.CURRENT_CONTINUE_PLAY_NOW)

        if not self._is_current_match_setup():
            self.wait.until(lambda _driver: self._is_current_match_setup())

        if category.lower() != "singles":
            raise ValueError("The current match-creation flow supports Singles only")
        if match_type.lower() not in ("male", "mixed"):
            raise ValueError("match_type must be 'Male' or 'Mixed'")

        if self._has_visible_element(self.SINGLES_OPTION):
            self._click(self.SINGLES_OPTION)
        type_locator = (
            self.CURRENT_MALE_OPTION
            if match_type.lower() == "male"
            else self.CURRENT_MIXED_OPTION
        )
        if self._has_visible_element(type_locator):
            self._click(type_locator)

        self._select_current_opponent()

        set_locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().description("{sets} sets")',
        )
        self._click(set_locator)
        self.selected_ground = self._select_current_ground(ground)
        self._create_screen_source = self.driver.page_source
        self._click(self.CURRENT_CREATE_BUTTON)
        self.wait.until(
            lambda _driver: not self._has_visible_element(self.CURRENT_CREATE_BUTTON)
        )
        if not self.verify_match_created():
            raise TimeoutException("Match creation completed without a verifiable success screen")

        print("\n" + "=" * 70)
        print("MATCH CREATION COMPLETED SUCCESSFULLY")
        print(f"Sport: Badminton | Category: {category} | Type: {match_type}")
        print(
            f"Opponent: {self.selected_opponent or 'selected opponent'} | "
            f"Sets: {sets} | Ground: {self.selected_ground}"
        )
        print("=" * 70 + "\n")
