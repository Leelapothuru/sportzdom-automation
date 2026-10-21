import time
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

driver.tap([(676, 2122)])
time.sleep(1)

dump_state(driver, "tried_next_anyway")

driver.quit()
