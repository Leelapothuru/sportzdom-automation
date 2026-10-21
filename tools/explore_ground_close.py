import time
from tools.helpers import by_id, edit_text
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

by_id(driver, "Select Time").click()
time.sleep(1)
by_id(driver, "Switch to text input mode").click()
time.sleep(1)

hour_field = edit_text(driver, 0)
hour_field.click()
hour_field = edit_text(driver, 0)
hour_field.clear()
hour_field.send_keys("08")

minute_field = edit_text(driver, 1)
minute_field.click()
minute_field = edit_text(driver, 1)
minute_field.clear()
minute_field.send_keys("00")

by_id(driver, "PM").click()
time.sleep(1)
by_id(driver, "OK").click()
time.sleep(1)

dump_state(driver, "ground_close_set")

driver.quit()
