import time
from drivers.driver_manager import get_driver
from tools.helpers import edit_text, dismiss_keyboard
from tools.inspector import dump_state

driver = get_driver()

minutes = edit_text(driver, 0)
minutes.click()
minutes = edit_text(driver, 0)
minutes.send_keys("90")

# Blur by clicking a stable label (resolved live, not a hardcoded coordinate)
dismiss_keyboard(driver, "MATCH DETAILS")
time.sleep(1)

dump_state(driver, "after_match_minutes")

driver.quit()
