import time
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

# Tap a neutral label area (not an input) to blur the focused field and close the keyboard
driver.tap([(190, 754)])
time.sleep(1)

dump_state(driver, "after_tap_dismiss")

driver.quit()
