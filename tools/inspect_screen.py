"""
Quick one-off inspection of whatever screen the app launches to
(MainActivity, since driver_manager uses no_reset=True / app_package+app_activity).

For inspecting a screen deeper in the app, write a small script that performs
the navigation steps (reusing Page Object methods) and calls dump_state()
at the point you want to inspect, instead of using this file directly.
"""

from drivers.driver_manager import get_driver
from tools.inspector import dump_state

driver = get_driver()
dump_state(driver, "current_screen")
driver.quit()
