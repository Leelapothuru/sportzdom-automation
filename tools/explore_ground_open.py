import time
from tools.helpers import by_id
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

field = by_id(driver, "Select time")
field.click()
time.sleep(1)

dump_state(driver, "ground_open_picker")

driver.quit()
