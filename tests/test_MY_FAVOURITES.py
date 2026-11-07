import os

import pytest

from pages.favourites_page import FavouritesPage
from pages.login_page import LoginPage
from utils.favourites_texts import FavouritesTexts


@pytest.mark.destructive
@pytest.mark.skipif(
    os.environ.get("SPORTZDOM_RUN_FAVOURITES_TEST") != "1",
    reason=FavouritesTexts.RUN_TEST_REASON,
)
def test_selected_sports_are_shown_in_favourites_tab(driver):
    login = LoginPage(driver)
    if not login.is_home_page():
        if login.is_logged_in():
            login.click_home()
        elif login.is_signin_page():
            login.login()
        else:
            try:
                login.return_to_home()
            except RuntimeError:
                login.login()

    assert login.is_home_page(), FavouritesTexts.HOME_PAGE_NOT_DISPLAYED

    login.click_profile()
    favourites = FavouritesPage(driver)
    favourites.open()
    assert favourites.is_my_favourites_page(), (
        FavouritesTexts.FAVOURITES_PAGE_NOT_DISPLAYED
    )

    original_count = favourites.get_favourite_count()
    assert original_count == 0, FavouritesTexts.EMPTY_ACCOUNT_REQUIRED

    favourites.click_all_sports()
    assert favourites.is_all_sports_tab(), (
        FavouritesTexts.ALL_SPORTS_TAB_NOT_SELECTED
    )

    added_sports = []
    try:
        for sport in FavouritesTexts.SPORTS_TO_FAVOURITE:
            favourites.scroll_to_sport(sport)
            count_before = favourites.get_favourite_count()
            try:
                favourites.click_favourite_for_sport(sport)
            finally:
                if favourites.get_favourite_count() > count_before:
                    added_sports.append(sport)

        assert favourites.get_favourite_count() == len(
            FavouritesTexts.SPORTS_TO_FAVOURITE
        ), (
            FavouritesTexts.EXPECTED_FAVOURITE_COUNT_NOT_REACHED
        )

        favourites.click_favourite_sports()
        assert favourites.is_favourite_sports_tab(), (
            FavouritesTexts.FAVOURITE_SPORTS_TAB_NOT_SELECTED
        )
        for sport in FavouritesTexts.SPORTS_TO_FAVOURITE:
            assert favourites.is_sport_card_displayed(sport), (
                FavouritesTexts.SPORT_NOT_DISPLAYED.format(sport)
            )
    finally:
        if added_sports:
            if not favourites.is_favourite_sports_tab():
                favourites.click_favourite_sports()
            for sport in reversed(added_sports):
                assert favourites.is_sport_card_displayed(sport), (
                    FavouritesTexts.SPORT_NOT_DISPLAYED_FOR_REMOVAL.format(sport)
                )
                favourites.remove_favourite_for_sport(sport)

        assert favourites.get_favourite_count() == original_count, (
            FavouritesTexts.FAVOURITES_NOT_RESTORED
        )
        if added_sports:
            favourites.click_browse_all_sports()
            assert favourites.is_all_sports_tab(), (
                FavouritesTexts.ALL_SPORTS_TAB_NOT_DISPLAYED
            )
