import time
from tools.helpers import by_id
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

by_id(driver, "PARTICIPATION").click()
time.sleep(1)

dump_state(driver, "tab2_blurred")

driver.quit()
