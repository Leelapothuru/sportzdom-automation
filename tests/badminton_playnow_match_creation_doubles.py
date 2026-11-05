"""Page object for creating a badminton doubles match from Play Now."""

from __future__ import annotations

import re
import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.badminton_playnow_match_creation_singles import SetMatchCreation as SinglesMatchCreation


class SetMatchCreationDoubles(SinglesMatchCreation):
    """Create a doubles match using an available self and opponent team."""

    TYPE_DROPDOWN_LOCATORS = [
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select Gender")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Select Gender")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionMatches("(?i).*select gender.*")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Type")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select Type")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Type")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionMatches("(?i).*type.*")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("(?i).*type.*")'),
    ]
    MALE_OPTION_LOCATORS = [
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Male")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Male ")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Male")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionMatches("(?i).*male.*")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("(?i).*male.*")'),
    ]
    SELECT_TEAM_SECTION = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select ")')
    SELECT_TEAM_BUTTON_LOCATORS = [
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select Team")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Select Team ")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Select Team")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Select Team")'),
    ]
    SELF_TEAM_LOCATORS = [
        (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().description("B\\nbadminton#2026.31🏸\\nRANK #0")',
        ),
        (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().descriptionContains("badminton#2026.31")',
        ),
    ]
    CHANGE_SECOND_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().description("Change").instance(1)',
    )
    OPPONENT_TEAM_TOO_LARGE_WARNING = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionContains("has more than  2 players")',
    )
    CURRENT_SELF_TEAM_CARD = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionContains("Tap your side to pick your team.")',
    )
    CURRENT_OPPONENT_TEAM_CARD = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionContains("Opponent")',
    )
    CURRENT_SELECT_TEAM = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().description("Select Team")',
    )

    def __init__(self, driver, timeout: int = 15):
        super().__init__(driver, timeout)
        self.selected_self_team: str | None = None
        self.selected_opponent_team: str | None = None

    def select_category(self, category: str = "Doubles") -> None:
        """Select Doubles; this page object does not support Singles."""
        if category.lower() != "doubles":
            raise ValueError("SetMatchCreationDoubles requires category='Doubles'")
        super().select_category("Doubles")

    def select_male_type(self) -> None:
        """Open Select Gender and choose Male."""
        print("Selecting Male gender...")
        for locator in self.TYPE_DROPDOWN_LOCATORS:
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable(locator)
                ).click()
                break
            except TimeoutException:
                continue
        else:
            raise TimeoutException("Select Gender dropdown not found")

        time.sleep(1)
        for locator in self.MALE_OPTION_LOCATORS:
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable(locator)
                ).click()
                break
            except TimeoutException:
                continue
        else:
            raise TimeoutException("Male type option not found")
        time.sleep(1)

    @staticmethod
    def _label(element) -> str:
        return (element.text or element.get_attribute("content-desc") or "").strip()

    def _first_team(self, require_two_players: bool = False, exclude: str | None = None):
        """Return the first visible team card, preferring a two-player team."""
        team_locators = [
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.view.View").clickable(true)'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.TextView").clickable(true)'),
        ]
        excluded_labels = {"select", "select team", "back", "change", "male", "female"}
        fallback = None
        player_counts_are_visible = False

        for locator in team_locators:
            for element in self.driver.find_elements(*locator):
                if not element.is_displayed() or not element.is_enabled():
                    continue
                label = self._label(element)
                if not label or label.lower() in excluded_labels:
                    continue
                if exclude and label == exclude:
                    continue
                player_count = re.search(r"\b(\d+)\s*(players?|members?)\b", label, re.IGNORECASE)
                if player_count:
                    player_counts_are_visible = True
                if player_count and player_count.group(1) == "2":
                    return element
                if fallback is None:
                    fallback = element

        # If the UI does not expose player counts on a team card, use the
        # first remaining visible team and let the Change warning recover it.
        if require_two_players and player_counts_are_visible:
            return None
        return fallback

    def select_available_team(
        self,
        role: str,
        require_two_players: bool = False,
        exclude: str | None = None,
        open_picker: bool = True,
    ) -> str:
        """Open a team picker, select an available team, and confirm it."""
        print(f"Selecting available {role} team...")
        if open_picker:
            self._click(self.SELECT_TEAM_SECTION)
            time.sleep(1)

        if role == "self" and not exclude:
            for locator in self.SELF_TEAM_LOCATORS:
                try:
                    team_element = WebDriverWait(self.driver, 4).until(
                        EC.element_to_be_clickable(locator)
                    )
                    break
                except TimeoutException:
                    continue
            else:
                team_element = None
        else:
            team_element = None

        if team_element is None:
            try:
                team_element = WebDriverWait(self.driver, 8).until(
                    lambda _driver: self._first_team(require_two_players, exclude) or False
                )
            except TimeoutException as exc:
                raise TimeoutException(f"No available {role} team found") from exc

        team_name = self._label(team_element) or f"{role} team"
        team_element.click()
        time.sleep(1)
        for locator in self.SELECT_TEAM_BUTTON_LOCATORS:
            try:
                WebDriverWait(self.driver, 4).until(
                    EC.element_to_be_clickable(locator)
                ).click()
                break
            except TimeoutException:
                continue
        else:
            raise TimeoutException("Select Team confirmation button not found")
        self.click_back_button()
        print(f"Selected {role} team: {team_name}")
        return team_name

    def _opponent_team_requires_change(self) -> bool:
        """Return whether the selected opponent team exceeds two players."""
        return self._element_exists(self.OPPONENT_TEAM_TOO_LARGE_WARNING, timeout=2)

    def replace_invalid_opponent_team(self) -> None:
        """Replace the opponent team only when its size warning is shown."""
        if not self._opponent_team_requires_change():
            return

        print("Opponent team has more than two players; changing it...")
        self._click(self.CHANGE_SECOND_BUTTON)
        time.sleep(1)
        self.selected_opponent_team = self.select_available_team(
            "opponent",
            require_two_players=True,
            exclude=self.selected_opponent_team,
            open_picker=False,
        )
        if self._opponent_team_requires_change():
            raise AssertionError("No two-player opponent team is available")

    def verify_doubles_match_ui(self) -> bool:
        """Check the generic resulting match UI after the doubles flow."""
        return self.verify_match_created()

    def _select_current_team(self, role: str) -> str:
        """Select a team from the Play Now team picker."""
        team_card = (
            self.CURRENT_SELF_TEAM_CARD
            if role == "self"
            else self.CURRENT_OPPONENT_TEAM_CARD
        )
        card = next(
            (
                element
                for element in self.driver.find_elements(*team_card)
                if element.is_displayed()
                and element.is_enabled()
                and "SELECT" in self._label(element).upper()
            ),
            None,
        )
        if card is None:
            raise TimeoutException(f"No unselected {role} team card was visible")
        bounds = card.rect
        self.driver.execute_script(
            "mobile: clickGesture",
            {
                "x": bounds["x"] + round(
                    bounds["width"] * (0.25 if role == "self" else 0.75)
                ),
                "y": bounds["y"] + bounds["height"] // 2,
            },
        )

        def find_team(_driver):
            for element in self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().clickable(true)',
            ):
                if not element.is_displayed() or not element.is_enabled():
                    continue
                label = self._label(element)
                if re.search(r"\b\d+\s+members?\b", label, re.IGNORECASE):
                    return element, label
            return False

        try:
            team, team_label = self.wait.until(find_team)
        except TimeoutException as exc:
            raise TimeoutException(f"No available {role} team was visible in the picker") from exc

        team.click()
        self._click(self.CURRENT_SELECT_TEAM)
        self.click_back_button()
        return team_label.splitlines()[1].strip() if len(team_label.splitlines()) > 1 else team_label

    def _has_unselected_current_team(self, role: str) -> bool:
        locator = (
            self.CURRENT_SELF_TEAM_CARD
            if role == "self"
            else self.CURRENT_OPPONENT_TEAM_CARD
        )
        return any(
            element.is_displayed()
            and element.is_enabled()
            and "SELECT" in self._label(element).upper()
            for element in self.driver.find_elements(*locator)
        )

    def _complete_current_doubles_flow(self, sets: str) -> None:
        """Run doubles match creation on the current Play Now setup screens."""
        self.close_ad_loading()
        source = self.driver.page_source

        if "PLAYER STATS" in source and self._has_visible_element(self.CURRENT_SELECT_TEAM):
            self._click(self.CURRENT_SELECT_TEAM)
            self.click_back_button()
            source = self.driver.page_source

        if not self._is_current_match_setup():
            if not any(self._has_visible_element(locator) for locator in self.CURRENT_START_MATCH):
                if self._has_visible_element(self.HOME_TAB):
                    self._click(self.HOME_TAB)
                if not self._has_visible_element(self.PLAY_ICON):
                    self.driver.back()
                self._click(self.PLAY_ICON)
                self.select_badminton_sport()
            self._click_first_visible(self.CURRENT_START_MATCH, "Start a match")

        if not self._is_current_match_setup():
            self._click(self.CURRENT_PLAY_NOW_OPTION)
            self._click(self.CURRENT_CONTINUE_PLAY_NOW)
            self.wait.until(lambda _driver: self._is_current_match_setup())

        if self._has_visible_element(self.DOUBLES_OPTION):
            self._click(self.DOUBLES_OPTION)
        if self._has_visible_element(self.CURRENT_MALE_OPTION):
            self._click(self.CURRENT_MALE_OPTION)

        source = self.driver.page_source
        if self._has_unselected_current_team("self"):
            self.selected_self_team = self._select_current_team("self")
            source = self.driver.page_source
        elif "Tap opponent to pick your team." not in source:
            selected = re.search(r"Your side\s+(.+?)\s+Change", source, re.DOTALL)
            if selected:
                self.selected_self_team = selected.group(1).strip()

        source = self.driver.page_source
        if self._has_unselected_current_team("opponent"):
            self.selected_opponent_team = self._select_current_team("opponent")
            source = self.driver.page_source
        elif not self.selected_opponent_team:
            selected = re.search(r"Opponent\s+(.+?)\s+Change", source, re.DOTALL)
            if selected:
                self.selected_opponent_team = selected.group(1).strip()

        if self._has_visible_element(self.OPPONENT_TEAM_TOO_LARGE_WARNING):
            raise TimeoutException("Selected opponent team has more than two players")

        set_locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().description("{sets} sets")',
        )
        window = self.driver.get_window_size()
        for _ in range(6):
            if self._has_visible_element(set_locator):
                break
            self.driver.swipe(
                window["width"] // 2,
                round(window["height"] * 0.8),
                window["width"] // 2,
                round(window["height"] * 0.35),
                450,
            )
        self._click(set_locator)
        self.selected_ground = self._select_current_ground(None)
        self._create_screen_source = self.driver.page_source
        self._click(self.CURRENT_CREATE_BUTTON)
        self.wait.until(
            lambda _driver: not self._has_visible_element(self.CURRENT_CREATE_BUTTON)
        )
        if not self.verify_doubles_match_ui():
            raise TimeoutException("Doubles match creation could not be verified")

    def complete_match_creation_flow(
        self,
        category: str = "Doubles",
        sets: str = "3",
        ground: str | None = None,
    ) -> None:
        """Execute the complete doubles match-creation workflow."""
        print("\n" + "=" * 70)
        print("STARTING DOUBLES SET MATCH CREATION FLOW")
        print("=" * 70 + "\n")

        try:
            if (
                self._is_current_match_setup()
                or "Pick your side" in self.driver.page_source
                or "PLAYER STATS" in self.driver.page_source
                or "Play - Badminton" in self.driver.page_source
            ):
                self._complete_current_doubles_flow(sets)
                return

            # Same navigation as the singles flow, through Create Match.
            self.close_ad_loading()
            self.click_play_icon()
            self.select_badminton_sport()
            self.click_play_button_after_card_flip()
            self.select_play_myself()
            self.click_play_now()
            self.proceed_to_create_match_page()

            self.select_category(category)
            self.select_male_type()
            self.selected_self_team = self.select_available_team("self")
            self.selected_opponent_team = self.select_available_team("opponent")
            self.replace_invalid_opponent_team()
            self.select_sets(sets)
            self.select_ground(ground)
            self.create_match()

            if not self.verify_doubles_match_ui():
                raise AssertionError("Doubles match was not verified after creation")
        except Exception as exc:
            print(f"Doubles match creation failed: {exc}")
            raise


# Allows the same import style as the singles module.
SetMatchCreation = SetMatchCreationDoubles
