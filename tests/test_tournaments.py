import os
import time

from drivers.driver_manager import get_driver
from pages.tournaments_page import TournamentsPage


start = time.perf_counter()
os.makedirs("screenshots/tournaments", exist_ok=True)

# App launcher (assumes an already-logged-in session, e.g. from test_login.py)
driver = get_driver()
print("App Opened")

# Wait for app to fully load
time.sleep(2)

print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/tournaments/homepage_screen.png")
print("Screenshot Saved")

# Click Tournaments on the nav bar
tournaments = TournamentsPage(driver)
tournaments.click_tournaments_nav()
print("Tournaments Nav Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/tournaments/tournaments_page_screen.png")
print("Screenshot Saved")

# Click the "Click here" button
tournaments.click_here_button()
print("Click Here Button Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/tournaments/click_here_screen.png")
print("Screenshot Saved")

# Select "Single Tournament" and proceed
tournaments.select_single_tournament()
print("Single Tournament Selected")
tournaments.click_modal_next()
print("Modal NEXT Clicked")
driver.save_screenshot("screenshots/tournaments/tab1_basic_details_screen.png")
print("Screenshot Saved")

# --- Tab 1: Basic Details ---
tournaments.enter_tournament_name("Automation Test Tournament")
print("Tournament Name Entered")

tournaments.select_sport("FootBall")
print("Sport Selected: FootBall")

tournaments.select_tournament_type("KnockOut")
print("Tournament Type Selected: KnockOut")

tournaments.select_match_type("Team")
print("Match Type Selected: Team")

tournaments.select_age_group("Open")
print("Age Group Selected: Open")

tournaments.select_category("Mixed")
print("Category Selected: Mixed")

tournaments.select_area("District")
print("Area Selected: District")

tournaments.select_state("Andhra Pradesh")
print("State Selected: Andhra Pradesh")

tournaments.select_district("Anantapur")
print("District Selected: Anantapur")

tournaments.enter_city("Kurnool")
print("City Entered: Kurnool")

tournaments.enter_prizes(first="5000", second="3000", third="1000")
print("Prizes Entered")
driver.save_screenshot("screenshots/tournaments/tab1_filled_screen.png")
print("Screenshot Saved")

tournaments.click_basic_details_next()
print("Basic Details Next Clicked")

# Banner upload requires a real photo from the device gallery
tournaments.upload_banner_manually(wait_seconds=20)
print("Banner Uploaded and Saved")
driver.save_screenshot("screenshots/tournaments/tab2_scheduling_details_screen.png")
print("Screenshot Saved")

# --- Tab 2: Scheduling Details ---
tournaments.select_tournament_start_date_today()
print("Tournament Start Date Selected")

tournaments.select_tournament_end_date("7, Monday, September 7, 2026")
print("Tournament End Date Selected")

tournaments.select_tournament_schedule("Daily")
print("Tournament Schedule Selected: Daily")

tournaments.enter_match_minutes("90")
print("Match Minutes Entered: 90")

tournaments.select_team_size("11A - Side")
print("Team Size Selected: 11A - Side")

tournaments.select_teams_count("16")
print("Teams Count Selected: 16")

tournaments.select_ground_open_time("06", "00", "AM")
print("Ground Open Time Set: 06:00 AM")

tournaments.select_ground_close_time("08", "00", "PM")
print("Ground Close Time Set: 08:00 PM")

tournaments.enter_grounds_count("2")
print("Grounds Count Entered: 2")

tournaments.enter_referee_count("2")
print("Referee Count Entered: 2")

tournaments.enter_scorer_count("2")
tournaments.dismiss_keyboard("Grounds Count")
print("Scorer Count Entered: 2")
driver.save_screenshot("screenshots/tournaments/tab2_filled_screen.png")
print("Screenshot Saved")

tournaments.click_scheduling_details_next()
print("Scheduling Details Next Clicked")
driver.save_screenshot("screenshots/tournaments/tab3_registration_details_screen.png")
print("Screenshot Saved")

end = time.perf_counter()
print(f"Time taken: {end - start:.2f} seconds")
