import pytest
from selenium.common.exceptions import InvalidSessionIdException

from drivers.driver_manager import get_driver
from pages.role_registration_page import RoleRegistrationPage


APPLICATION_DESCRIPTION = (
    "I am interested in contributing to the sport as an Archery referee."
)
ROLE_SPORT = "FootBall"
ROLE = "Referee"
PLAYING_LEVEL = "South Zone"
EDUCATION = "Post Graduate"
STATE = "Andhra Pradesh"


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


def test_archery_referee_role_registration_flow(driver):
    registration = RoleRegistrationPage(driver)
    registration.open_registration()
    registration.select_sport(ROLE_SPORT)
    registration.select_role(ROLE)
    registration.select_playing_level(PLAYING_LEVEL)
    registration.add_one_year_experience()
    registration.select_education(EDUCATION)
    registration.select_state(STATE)
    registration.enter_application_description(APPLICATION_DESCRIPTION)
    registration.accept_declaration()
    registration.submit_application()

    assert registration.is_submission_confirmation_displayed(), (
        "Role application confirmation was not displayed"
    )
    registration.confirm_submission()
