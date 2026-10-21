import time
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

# Close (X) button is top-right of the Upload Banner modal
driver.tap([(838, 1194)])
time.sleep(1)

dump_state(driver, "after_close_banner")

driver.quit()
