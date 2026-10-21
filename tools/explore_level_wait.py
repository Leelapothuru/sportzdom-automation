import time
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

driver.tap([(773, 1401)])
time.sleep(6)

dump_state(driver, "level_after_long_wait")

driver.quit()
