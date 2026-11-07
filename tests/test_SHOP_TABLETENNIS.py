from pages.login_page import LoginPage
from pages.shop_page import ShopPage


def test_shop_table_tennis_categories_are_navigable(driver):
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

    assert login.is_home_page(), "Home page was not displayed"

    shop = ShopPage(driver)
    shop.open_menu()
    shop.search_menu("shop")
    assert shop.open_shop().is_displayed(), "Shop page search field was not displayed"

    shop.open_category("Shop TableTennis")
    assert shop.wait_for_category("Clothing").is_displayed(), (
        "Table Tennis categories were not displayed"
    )

    shop.open_category("Clothing")
    assert shop.wait_for_category("jerseys").is_displayed(), (
        "Clothing categories were not displayed"
    )

    shop.open_category("jerseys")
