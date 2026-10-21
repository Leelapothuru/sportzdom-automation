import time
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

driver.swipe(540, 1800, 540, 500, 600)
time.sleep(1)

dump_state(driver, "tab2_scrolled_more")

driver.quit()
