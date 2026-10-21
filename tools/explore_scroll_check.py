import time
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

# Swipe up to scroll the form down and reveal Second/Third Prize fields
driver.swipe(540, 1800, 540, 900, 600)
time.sleep(1)

dump_state(driver, "after_scroll_down")

driver.quit()
