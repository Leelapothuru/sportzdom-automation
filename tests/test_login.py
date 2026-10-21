import time

start = time.perf_counter()

from drivers.driver_manager import get_driver
from pages.login_page import LoginPage

# App launcher
driver = get_driver()
print("✅ App Opened")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/loginpage/signup_screen.png")
print("Screenshot Saved")

# open SignUp page
login = LoginPage(driver)
print("✅ login page Opened")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/loginpage/signup_screen.png")
print("Screenshot Saved")

# open signin page
login.click_signin_text()
print("✅ Sign In Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/loginpage/signin_screen.png")
print("Screenshot Saved")

# check the checkbox
login.click_checkbox()
print("✅ Checkbox Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/loginpage/checkBoxclicked_screen.png")
print("Screenshot Saved")

# click on the Email text field to enter email
login.click_emailfield()
print("✅ emailField Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/loginpage/checkBoxclicked_screen.png")
print("Screenshot Saved")

# enter email
login.enter_email("user.1@yopmail.com")
print("✅ Email Entered")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/loginpage/emailEntered_screen.png")
print("Screenshot Saved")

# click on the password text field to enter password
login.click_passwordfield()
print("✅ passwordField Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/loginpage/checkBoxclicked_screen.png")
print("Screenshot Saved")

# enter password
login.enter_password("User1@123")
print("✅ Password Entered")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/loginpage/passwordEntered_screen.png")
print("Screenshot Saved")

# click signin button
login.click_signin_button()
print("✅ Login Button Clicked")
print("Current Activity:", driver.current_activity)
driver.save_screenshot("screenshots/loginpage/homepage_screen.png")
print("Screenshot Saved")

# wait for home page to load
time.sleep(10)  # basic wait; better if you can wait for a home-page element

# save screenshot of home page
driver.save_screenshot("screenshots/loginpage/homepage_screen.png")
print("Screenshot Saved")

end = time.perf_counter()
print(f"Time taken: {end - start:.2f} seconds")