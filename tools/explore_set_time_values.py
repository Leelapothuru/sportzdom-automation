import time
from tools.helpers import by_id, edit_text
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

hour_field = edit_text(driver, 0)
hour_field.click()
hour_field = edit_text(driver, 0)
hour_field.clear()
hour_field.send_keys("06")

minute_field = edit_text(driver, 1)
minute_field.click()
minute_field = edit_text(driver, 1)
minute_field.clear()
minute_field.send_keys("00")

by_id(driver, "AM").click()
time.sleep(1)

dump_state(driver, "time_set_before_ok")

driver.quit()
