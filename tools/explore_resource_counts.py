import time
from tools.helpers import edit_text, dismiss_keyboard
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()


def fill(instance, value):
    field = edit_text(driver, instance)
    field.click()
    field = edit_text(driver, instance)
    field.send_keys(value)


fill(0, "2")   # Grounds Count
dismiss_keyboard(driver, "TOURNAMENT RESOURCES")
time.sleep(1)

dump_state(driver, "after_grounds_count")

driver.quit()
