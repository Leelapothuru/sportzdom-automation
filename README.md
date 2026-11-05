# Sportzdom Mobile Automation Framework

Python + Appium + Pytest automation for the Sportzdom Android app, organised with
the Page Object Model and ready to run from Azure DevOps on a self-hosted agent.

## Project structure

```
Sportzdom-Automation/
├── tests/
│   ├── test_login.py                 # sign-in screen checks + demo-account login
│   ├── test_logout.py                # profile drawer and logout
│   └── test_tournament_creation.py   # Knockout and League tournament wizard
├── pages/
│   ├── login_page.py
│   ├── logout_page.py
│   └── tournament_page.py
├── config/
│   ├── capabilities.py               # Appium UiAutomator2 options
│   └── settings.py                   # env-driven settings, loads local .env
├── test_data/
│   ├── tournament_data.json          # tournament form values
│   └── tournament_data.py            # loader (relative dates, officials safety rule)
├── utils/
│   ├── driver_setup.py               # get_driver(): starts the Appium session
│   └── helpers.py                    # shared locator and format helpers
├── reports/                          # manual test cases; automation run reports (git-ignored)
├── conftest.py                       # fixtures, screenshots, report filing, run timing
├── requirements.txt
├── pytest.ini
└── README.md
```

- **Page objects** (`pages/`) hold locators verified with Appium Inspector and reusable interactions.
- **Tests** (`tests/`) hold scenarios and assertions only.
- **Config** (`config/`) holds everything environment-specific, read from environment variables.

## Prerequisites (local machine or pipeline agent)

| Component | Notes |
|---|---|
| Python 3.12+ | `python -m venv venv` then `pip install -r requirements.txt` |
| Java JDK 17+ | `JAVA_HOME` set |
| Android SDK platform-tools | `ANDROID_HOME` / `ANDROID_SDK_ROOT` set, `adb` on `PATH` |
| Node.js 20+ and Appium 2+ | `npm install -g appium` |
| UiAutomator2 driver | `appium driver install uiautomator2` (installed on the machine, not in this repo) |
| Device or emulator | USB debugging on, visible in `adb devices`, Sportzdom app (`com.sportzdom.app`) installed |

Start the Appium server before running tests:

```bash
appium --address 127.0.0.1 --port 4723
```

## Configuration

All settings come from environment variables (see [config/settings.py](config/settings.py)).
For local runs, copy [.env.example](.env.example) to `.env` (git-ignored) and fill it in.
Variables already set in the environment (e.g. pipeline variables) take priority over `.env`.

| Variable | Purpose | Default |
|---|---|---|
| `SPORTZDOM_DEVICE_NAME` | Appium device name | `Android` |
| `SPORTZDOM_DEVICE_UDID` | Device serial from `adb devices` | empty: the only connected device |
| `SPORTZDOM_APPIUM_URL` | Appium server URL | `http://127.0.0.1:4723` |
| `SPORTZDOM_APP_PACKAGE` / `SPORTZDOM_APP_ACTIVITY` | App under test | `com.sportzdom.app` / `.MainActivity` |
| `SPORTZDOM_DEMO_EMAIL` / `SPORTZDOM_DEMO_PASSWORD` | Demo-account login (test skipped if unset) | none |
| `SPORTZDOM_RUN_VALID_MOBILE_CHECK` | Enable the valid-mobile-number check | off |
| `SPORTZDOM_RUN_INTERACTIVE_OTP_LOGIN` | Enable the interactive OTP login (needs a human) | off |

Credentials are never written in code. In Azure DevOps, define them as **secret** pipeline
variables and map them into the test step explicitly (secrets are not passed to scripts automatically):

```yaml
- script: python -m pytest -v
  env:
    SPORTZDOM_DEMO_EMAIL: $(SPORTZDOM_DEMO_EMAIL)
    SPORTZDOM_DEMO_PASSWORD: $(SPORTZDOM_DEMO_PASSWORD)
    SPORTZDOM_DEVICE_UDID: $(SPORTZDOM_DEVICE_UDID)
```

## Running tests

```bash
# All tests (order: logout -> login -> tournament creation needs the right app state)
python -m pytest tests/test_logout.py tests/test_login.py tests/test_tournament_creation.py -v

# One feature
python -m pytest tests/test_login.py -v
python -m pytest tests/test_tournament_creation.py -v

# By marker (see pytest.ini)
python -m pytest -m smoke -v
```

`test_login.py` needs the app signed out and `test_tournament_creation.py` needs it signed in;
each skips with a reason when the app is in the wrong state.
`test_tournament_creation.py` creates four tournaments per run on the test account
(FootBall Knockout and League, Badminton Singles Knockout and League) and **publishes**
each one from My drafts, then checks it appears in Upcoming. Run it only against the
test environment. Referees and scorers are picked only from test accounts (`user<number>`).

## Reports and evidence

- `reports/automation/latest_junit.xml`: JUnit XML of the latest run (for pipeline test publishing).
- `reports/automation/success|failure/`: each run's JUnit report and terminal log, filed by result.
- `screenshots/runs/<feature>_<time>/passed|failed/`: a screenshot per step, plus the widget XML for failures.
- `reports/manual/`: manual test cases and retest results.

Run outputs (`reports/automation/`, `screenshots/`) are git-ignored; publish them as pipeline artifacts.
Pytest returns a non-zero exit code when any test fails.

## Azure DevOps notes

No pipeline definition has been added yet. When one is added:

- Use a **self-hosted agent** with the prerequisites above and the device attached.
  Microsoft-hosted agents cannot reach a physical device.
- Install dependencies with `pip install -r requirements.txt`, start Appium, run pytest,
  then publish `reports/automation/latest_junit.xml` with `PublishTestResults@2`.
- Keep interactive OTP tests disabled (the default). They wait for a human to type an SMS code.
- Use a dedicated test environment and test accounts, not production data.
