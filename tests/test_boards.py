from pages.boards_page import BoardsPage
from pages.login_page import LoginPage


def test_boards_filter_can_be_applied_and_cleared(driver):
    login = LoginPage(driver)
    if not login.is_home_page() and not login.is_signin_page():
        for _ in range(8):
            driver.back()
            if login.is_home_page():
                break

    if login.is_logged_in():
        if not login.is_home_page():
            login.click_home()
    else:
        login.login()

    assert login.is_home_page(), "Home page was not displayed after login"

    boards = BoardsPage(driver)
    boards.open()
    boards.scroll_page("down")
    sport_filter = boards.scroll_until_visible(boards.SPORT_DROPDOWN)
    assert sport_filter.is_displayed(), "Boards sport filter was not displayed"

    boards.open_sport_filter()
    clear_button = boards.select_sport("Football")
    assert clear_button.is_displayed(), "Football filter was not applied"

    boards.scroll_for("down", 5)
    boards.scroll_for("up", 5)

    assert boards.clear_filter(), "Clear button remained visible after clearing the filter"
    assert not any(
        button.is_displayed() for button in driver.find_elements(*boards.CLEAR_BUTTON)
    )