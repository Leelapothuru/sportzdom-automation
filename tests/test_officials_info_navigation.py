import os

import pytest
from selenium.common.exceptions import InvalidSessionIdException

from drivers.driver_manager import get_driver
from pages.officials_page import OfficialsPage


OFFICIAL_SEARCH = "user2026.09"
OFFICIAL_FEE = "2500"


@pytest.fixture
def driver():
    try:
        session = get_driver()
    except RuntimeError as error:
        if "No Android device/emulator" not in str(error):
            raise
        pytest.skip(
            "No Android device/emulator is connected through ADB. "
            "Connect a device or start an emulator before running this test."
        )

    try:
        yield session
    finally:
        try:
            session.quit()
        except InvalidSessionIdException:
            pass


@pytest.mark.skipif(
    os.getenv("SPORTZDOM_RUN_OFFICIALS_FEE_MUTATION", "").lower() != "true",
    reason=(
        "Set SPORTZDOM_RUN_OFFICIALS_FEE_MUTATION=true to run the fee-changing "
        "flow with a dedicated test account."
    ),
)
def test_officials_info_navigation_and_fee_management(driver):
    officials = OfficialsPage(driver)

    officials.open_from_menu()
    officials.go_back()
    officials.open_from_menu()
    officials.select_filters("Archery", "Andhra Pradesh", "Male")
    officials.clear_filters()

    official_description = officials.open_official(OFFICIAL_SEARCH)
    assert OFFICIAL_SEARCH in official_description, (
        "The selected result did not match the configured official"
    )
    assert officials.is_add_fee_available(), "The official details did not load"

    officials.open_add_fee_form()
    assert officials.is_fee_form_displayed(), "Add-fee form was not displayed"
    officials.cancel_add_fee()
    assert officials.is_add_fee_available(), "Cancel did not return to official details"

    officials.open_add_fee_form()
    assert officials.enter_fee(OFFICIAL_FEE) == OFFICIAL_FEE, (
        "The fee value was not entered"
    )
    officials.save_fee()
    assert not officials.is_fee_form_displayed(), "Fee form remained open after saving"

    officials.scroll_to_bottom()
    officials.open_tab("Reviews")
    officials.open_tab("Gallery")
    officials.open_edit_fee_form()
    assert officials.is_fee_form_displayed(), "Edit-fee form was not displayed"
    assert officials.enter_fee(OFFICIAL_FEE) == OFFICIAL_FEE, (
        "The updated fee value was not entered"
    )
    officials.save_fee()
    assert not officials.is_fee_form_displayed(), "Edit-fee form remained open after saving"
    assert officials.is_edit_fee_available(), (
        "The saved fee was not available to edit"
    )
