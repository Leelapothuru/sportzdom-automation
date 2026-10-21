import time
from tools.helpers import edit_text, by_id
from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()

scorer = edit_text(driver, 2)
scorer.click()
scorer = edit_text(driver, 2)
scorer.send_keys("2")

by_id(driver, "Grounds Count").click()
time.sleep(1)

dump_state(driver, "after_scorer_count")

driver.quit()
