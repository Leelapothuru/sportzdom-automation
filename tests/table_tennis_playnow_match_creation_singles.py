"""Create a Table Tennis singles match through Sportzdom Play Now."""

from __future__ import annotations

import re

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException

from drivers.driver_manager import get_driver
from pages.badminton_playnow_match_creation_singles import (
    SetMatchCreation as BadmintonSetMatchCreation,
)


class TableTennisMatchCreation(BadmintonSetMatchCreation):
    """Reuse the Play Now singles flow with Table Tennis sport selection."""

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

    def select_table_tennis_sport(self) -> None:
        """Select Table Tennis from the sport picker."""
        if not any(self._has_visible_element(locator) for locator in self.TABLE_TENNIS_LOCATORS):
            self._click_first_visible(self.RACKET_CATEGORY_LOCATORS, "Racket sports category")
        self._click_first_visible(self.TABLE_TENNIS_LOCATORS, "Table Tennis sport")

    def select_badminton_sport(self) -> None:
        """Override the reference workflow's sport step without changing its flow."""
        self.select_table_tennis_sport()

    def _is_current_flow_screen(self) -> bool:
        return "Play - Table Tennis" in self.driver.page_source or super()._is_current_flow_screen()

    def complete_match_creation_flow(
        self,
        category: str = "Singles",
        opponent: str | None = None,
        sets: str = "3",
        ground: str | None = None,
        match_type: str = "Male",
    ) -> None:
        """Run the reference workflow while reporting Table Tennis accurately."""
        if (
            self._is_current_flow_screen()
            or self._has_visible_element(self.PLAY_ICON)
            or self._has_visible_element(self.HOME_TAB)
        ):
            self._complete_current_match_creation_flow(
                category,
                sets,
                match_type,
                ground,
            )
            return

        self.close_ad_loading()
        self.click_play_icon()
        self.select_table_tennis_sport()
        self.click_play_button_after_card_flip()
        self.select_play_myself()
        self.click_play_now()
        self.proceed_to_create_match_page()
        self.select_category(category)
        self.select_opponent(opponent)
        self.click_select_player_button()
        self.click_back_button()
        self.select_sets(sets)
        self.select_ground(ground)
        self.create_match()
        if not self.verify_table_tennis_match_created():
            raise TimeoutException("Table Tennis match creation was not verified")
        print(
            "Table Tennis Play Now match created: "
            f"category={category}, sets={sets}, "
            f"opponent={self.selected_opponent}, ground={self.selected_ground}"
        )

    def _complete_current_match_creation_flow(
        self,
        category: str,
        sets: str,
        match_type: str = "Male",
        ground: str | None = None,
    ) -> None:
        """Use the current Play Now screens to create a Table Tennis match."""
        self.close_ad_loading()
        source = self.driver.page_source
        if "PLAYER STATS" in source or "1 PLAYER" in source:
            self._select_current_opponent()
            source = self.driver.page_source

        if not self._is_current_match_setup() and "Select Whom To Play" not in source:
            if "1 PLAYER" not in source:
                if any(
                    self._has_visible_element(locator)
                    for locator in self.CURRENT_START_MATCH
                ):
                    self._click_first_visible(self.CURRENT_START_MATCH, "Start a match")
                else:
                    if self._has_visible_element(self.HOME_TAB):
                        self._click(self.HOME_TAB)
                    if not self._has_visible_element(self.PLAY_ICON):
                        self.driver.back()
                    self._click(self.PLAY_ICON)
                    self.select_table_tennis_sport()
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
        if not self.verify_table_tennis_match_created():
            raise TimeoutException(
                "Table Tennis match creation completed without a verifiable success screen"
            )
        print(
            "Table Tennis Play Now match created: "
            f"category={category}, type={match_type}, "
            f"opponent={self.selected_opponent}, sets={sets}, "
            f"ground={self.selected_ground}"
        )

    def verify_table_tennis_match_created(self) -> bool:
        """Verify the confirmation page identifies a created Table Tennis match."""
        if not self.verify_match_created():
            return False
        source = self.driver.page_source
        normalized = re.sub(r"\s+", "", source.casefold())
        if "match confirmation" not in source.casefold() or "tabletennis" not in normalized:
            return False
        return not self.selected_opponent or self.selected_opponent.casefold() in source.casefold()


def main() -> None:
    """Run and verify the Table Tennis Play Now singles match creation."""
    driver = get_driver()
    try:
        match_creation = TableTennisMatchCreation(driver)
        match_creation.complete_match_creation_flow(
            category="Singles",
            sets="3",
        )
        if not match_creation.verify_table_tennis_match_created():
            raise AssertionError("Table Tennis Play Now match creation was not verified")
        print("Table Tennis Play Now match creation completed successfully.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
