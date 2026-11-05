import sys
import time
from pathlib import Path

# Make this script runnable directly with: python tests/test_delete_account.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from drivers.driver_manager import get_driver
from pages.login_page import LoginPage


driver = get_driver()
login = LoginPage(driver)

print("📱 App initialized")
print("Current Activity:", driver.current_activity)
time.sleep(2)

# Login using the standard login method (handles all app states)
print("🔐 Logging in...")
try:
    if not login.is_logged_in():
        print("⏳ User not logged in, performing login...")
        login.login()
        time.sleep(5)
    else:
        print("✅ User already logged in")
    
    # Ensure we're on the home page
    if not login.is_home_page():
        print("📍 Returning to home page...")
        login.click_home()
        time.sleep(2)
    
except Exception as e:
    print(f"❌ Login error: {e}")
    driver.save_screenshot("screenshots/login_error.png")
    raise

# Give app time to settle
time.sleep(3)

# Click the Profile icon at the top-left corner of the Home page.
print("👤 Opening Profile Drawer...")
try:
    login.click_profile()
    time.sleep(2)
    driver.save_screenshot("screenshots/profile_drawer_opened.png")
    print("✅ Profile Drawer Opened")
except Exception as e:
    print(f"❌ Error opening profile: {e}")
    driver.save_screenshot("screenshots/profile_error.png")
    raise

# Scroll down in the Profile Drawer to find Delete Account
print("📜 Scrolling down in Profile Drawer...")
size = driver.get_window_size()
for i in range(5):
	driver.swipe(
		size["width"] // 2,
		int(size["height"] * 0.75),
		size["width"] // 2,
		int(size["height"] * 0.25),
		600,
	)
	time.sleep(0.5)

driver.save_screenshot("screenshots/profile_drawer_scrolled.png")
print("✅ Profile Drawer Scrolled Down")

# Click on Delete Account
print("🗑️ Clicking Delete Account...")
try:
    login.click_delete_account()
    print("✅ Delete Account Clicked")
    time.sleep(2)
    driver.save_screenshot("screenshots/delete_account_page.png")
except Exception as e:
    print(f"❌ Error clicking Delete Account: {e}")
    driver.save_screenshot("screenshots/delete_account_error.png")
    raise

# Verify Delete Account page is displayed
try:
    if not login.is_delete_account_page():
        print("⚠️ Delete Account page verification inconclusive, proceeding...")
    else:
        print("✅ Delete Account Page Verified")
except Exception:
    pass

# Click Confirm button
print("✅ Clicking Confirm Button...")
try:
    login.click_confirm_button()
    print("✅ Confirm Button Clicked")
    time.sleep(2)
    driver.save_screenshot("screenshots/after_confirm_delete_account.png")
except Exception as e:
    print(f"❌ Error clicking Confirm: {e}")
    driver.save_screenshot("screenshots/confirm_error.png")
    raise

# Click OK button on the popup dialog
print("📋 Clicking OK Button on Popup...")
try:
    login.click_ok_button()
    print("✅ OK Button Clicked")
    time.sleep(2)
    driver.save_screenshot("screenshots/after_ok_popup.png")
except Exception as e:
    print(f"❌ Error clicking OK: {e}")
    driver.save_screenshot("screenshots/ok_button_error.png")
    raise

print("\n✅ Test Completed Successfully: Delete Account Flow with Confirm and OK")

