import time
from tools.helpers import by_id
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

option = by_id(driver, "16")
option.click()
time.sleep(1)

dump_state(driver, "after_teams_count")

driver.quit()
