"""Environment-driven settings for the Sportzdom automation framework.

Values come from environment variables (Azure DevOps pipeline variables on an
agent). For local runs, a git-ignored .env file in the repository root is
loaded first; variables already set in the environment win over the file.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_local_env(path: Path = PROJECT_ROOT / ".env") -> None:
    """Load KEY=VALUE lines from a local .env file into the environment.

    For local runs only: the file is git-ignored, so test credentials never
    reach the repository.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# Load before any setting below (or any test module) reads the environment.
load_local_env()

# -- Application under test --------------------------------------------------
APP_PACKAGE = os.getenv("SPORTZDOM_APP_PACKAGE", "com.sportzdom.app")
APP_ACTIVITY = os.getenv("SPORTZDOM_APP_ACTIVITY", ".MainActivity")

# -- Appium server and device -------------------------------------------------
APPIUM_URL = os.getenv("SPORTZDOM_APPIUM_URL", "http://127.0.0.1:4723")
# No machine-specific defaults: set these per machine (.env) or pipeline agent.
DEVICE_NAME = os.getenv("SPORTZDOM_DEVICE_NAME", "Android")
DEVICE_UDID = os.getenv("SPORTZDOM_DEVICE_UDID", "")
# Interactive OTP tests pause while a tester receives and enters an SMS code.
NEW_COMMAND_TIMEOUT = int(os.getenv("SPORTZDOM_NEW_COMMAND_TIMEOUT", "300"))
