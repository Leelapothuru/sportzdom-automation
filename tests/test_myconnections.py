import os
import time

from drivers.driver_manager import get_driver
from pages.login_page import LoginPage
from pages.myprofile import MyProfilePage


start = time.perf_counter()
os.makedirs("screenshots/myconnections", exist_ok=True)

# App launcher
driver = get_driver()
print("App Opened")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/myconnections/signup_screen.png")
print("Screenshot Saved")

# Open login page
login = LoginPage(driver)
print("Login page Opened")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/myconnections/login_page.png")
print("Screenshot Saved")

# Open signin page
login.click_signin_text()
print("Sign In Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/myconnections/signin_screen.png")
print("Screenshot Saved")

# Check the checkbox
login.click_checkbox()
print("Checkbox Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/myconnections/checkbox_clicked_screen.png")
print("Screenshot Saved")

# Enter email
login.click_emailfield()
login.enter_email("user.1@yopmail.com")
print("Email Entered")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/myconnections/email_entered_screen.png")
print("Screenshot Saved")

# Enter password
login.click_passwordfield()
login.enter_password("User1@123")
print("Password Entered")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/myconnections/password_entered_screen.png")
print("Screenshot Saved")

# Login
login.click_signin_button()
print("Login Button Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/myconnections/homepage_screen.png")
print("Screenshot Saved")

# Wait for home page to load
time.sleep(10)

# Open My Connections from profile drawer
my_profile = MyProfilePage(driver)
my_profile.click_profile_icon()
print("Profile Icon Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/myconnections/profile_drawer_screen.png")
print("Screenshot Saved")

my_profile.click_my_connections()
print("My Connections Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/myconnections/my_connections_screen.png")
print("Screenshot Saved")

end = time.perf_counter()
print(f"Time taken: {end - start:.2f} seconds")
