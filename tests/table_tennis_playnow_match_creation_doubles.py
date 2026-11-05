"""Create a Table Tennis doubles match through Sportzdom Play Now."""

from __future__ import annotations

import re

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException

from drivers.driver_manager import get_driver
from pages.badminton_playnow_match_creation_doubles import (
    SetMatchCreationDoubles as BadmintonDoublesMatchCreation,
)


class TableTennisDoublesMatchCreation(BadmintonDoublesMatchCreation):
    """Reuse doubles team-selection workflow with Table Tennis sport selection."""

    RACKET_CATEGORY_LOCATORS = (
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Racket")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Racket")'),
    )
    TABLE_TENNIS_LOCATORS = (
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Table Tennis")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Table Tennis")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Table Tennis")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Table Tennis")'),
    )

    def _is_current_match_setup(self) -> bool:
        """Recognize the Table Tennis match form exposed by the current app UI."""
        source = self.driver.page_source
        return "Create match" in source and (
            "Match setup" in source
            or "Pick an opponent" in source
            or "Play - TableTennis" in source
            or "Play - Table Tennis" in source
        )

    def select_table_tennis_sport(self) -> None:
        """Select Table Tennis from the Racket sports picker."""
        if not any(self._has_visible_element(locator) for locator in self.TABLE_TENNIS_LOCATORS):
            self._click_first_visible(self.RACKET_CATEGORY_LOCATORS, "Racket sports category")
        self._click_first_visible(self.TABLE_TENNIS_LOCATORS, "Table Tennis sport")

    def select_badminton_sport(self) -> None:
        """Override the reference doubles workflow's sport-selection step."""
        self.select_table_tennis_sport()

    def complete_match_creation_flow(
        self,
        category: str = "Doubles",
        sets: str = "3",
        ground: str | None = None,
    ) -> None:
        """Run the same Play Now doubles flow, targeting Table Tennis."""
        if category.casefold() != "doubles":
            raise ValueError("TableTennisDoublesMatchCreation requires category='Doubles'")

        source = self.driver.page_source
        if (
            self._is_current_match_setup()
            or "Pick your side" in source
            or "PLAYER STATS" in source
            or "Play - Table Tennis" in source
            or "Play - TableTennis" in source
            or self._has_visible_element(self.PLAY_ICON)
            or self._has_visible_element(self.HOME_TAB)
            or any(
                self._has_visible_element(locator)
                for locator in self.CURRENT_START_MATCH
            )
        ):
            self._complete_current_doubles_flow(sets)
            if not self.verify_table_tennis_doubles_match_ui():
                raise TimeoutException("Table Tennis doubles match was not verified")
            return

        self.close_ad_loading()
        self.click_play_icon()
        self.select_table_tennis_sport()
        if any(
            self._has_visible_element(locator)
            for locator in self.CURRENT_START_MATCH
        ):
            self._complete_current_doubles_flow(sets)
            if not self.verify_table_tennis_doubles_match_ui():
                raise TimeoutException("Table Tennis doubles match was not verified")
            return
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
        if not self.verify_table_tennis_doubles_match_ui():
            raise TimeoutException("Table Tennis doubles match was not verified after creation")
        print(
            "Table Tennis Play Now doubles match created: "
            f"self team={self.selected_self_team}, "
            f"opponent team={self.selected_opponent_team}, "
            f"sets={sets}, ground={self.selected_ground}"
        )

    def verify_table_tennis_doubles_match_ui(self) -> bool:
        """Require match confirmation to identify Table Tennis and both teams."""
        if not self.verify_doubles_match_ui():
            return False
        source = self.driver.page_source
        normalized = re.sub(r"\s+", "", source.casefold())
        if "match confirmation" not in source.casefold() or "tabletennis" not in normalized:
            return False
        for team in (self.selected_self_team, self.selected_opponent_team):
            if team and team.casefold() not in source.casefold():
                return False
        return True


def main() -> None:
    """Run and verify Table Tennis Play Now doubles match creation."""
    driver = get_driver()
    try:
        match_creation = TableTennisDoublesMatchCreation(driver)
        match_creation.complete_match_creation_flow(category="Doubles", sets="3")
        if not match_creation.verify_table_tennis_doubles_match_ui():
            raise AssertionError("Table Tennis doubles match creation was not verified")
        print("Table Tennis Play Now doubles match creation completed successfully.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
