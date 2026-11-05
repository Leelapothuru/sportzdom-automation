"""Shared pytest fixtures, step evidence (screenshots) and run timing.

Files are named after the feature under test: a test module's FEATURE
(e.g. "tournament_creation"), or its file name without "test_".

Each run gets its own folder, screenshots/runs/<feature>_<start time>/:
  passed/  a screenshot at the end of every passed step
  failed/  a screenshot and widget dump of every failed step
  <feature>_junit.xml  a copy of that run's JUnit report
  <feature>_terminal.txt  a copy of the terminal output
Screenshots are numbered in run order, so they sort in flow order.

Each run's terminal output and JUnit report are also filed by result:
  reports/automation/success/  runs where every test passed
  reports/automation/failure/  runs with any failure or error, or that stopped early
as <feature>_terminal_<start time>.txt and <feature>_junit_<start time>.xml.
reports/automation/latest_junit.xml always holds the latest run (for pipelines).
"""

import logging
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pytest
from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException

# Importing config.settings loads the local .env (if any) before test modules
# read their environment variables; see config/settings.py.
from config import settings  # noqa: F401
from utils.driver_setup import get_driver

log = logging.getLogger(__name__)

TIME_FORMAT = "%d %b %Y %H:%M:%S"


def _duration(seconds):
    minutes, seconds = divmod(round(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}"


# Colour codes, and the progress-bar codes some terminals (e.g. Windows Terminal) receive.
ANSI_COLOURS = re.compile(r"\x1b\[[0-9;]*m|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")


class _TerminalCopy:
    """Write terminal output to the console and, without colour codes, to a text file."""

    def __init__(self, console, path):
        self._console = console
        self._file = open(path, "w", encoding="utf-8")

    def write(self, text):
        self._file.write(ANSI_COLOURS.sub("", text))
        return self._console.write(text)

    def flush(self):
        self._file.flush()
        self._console.flush()

    def close_copy(self):
        self._file.close()

    def __getattr__(self, name):
        return getattr(self._console, name)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    # trylast: the terminal reporter must exist before its output is copied.
    config._run_started = datetime.now()
    config._run_stamp = config._run_started.strftime("%Y-%m-%d_%H-%M-%S")
    config._step_number = 0
    config._terminal_copy = None
    # Until the session finishes successfully, a run counts as a failure.
    config._outcome = "failure"
    _name_run_files(config, "run")
    reporter = config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None and not config.option.collectonly:
        # The feature and result are only known later, so write to a temporary
        # name and move the file when the run ends.
        config._terminal_partial = Path(config.rootpath) / "reports" / "automation" / f"~running_{config._run_stamp}.txt"
        config._terminal_partial.parent.mkdir(parents=True, exist_ok=True)
        # pytest has no public option for this, so wrap the reporter's output stream.
        writer = reporter._tw
        config._terminal_copy = _TerminalCopy(writer._file, config._terminal_partial)
        writer._file = config._terminal_copy


def _name_run_files(config, feature):
    config._feature = feature
    config._run_dir = Path(config.rootpath) / "screenshots" / "runs" / f"{feature}_{config._run_stamp}"


def _report_path(config, kind, suffix):
    """reports/automation/<success|failure>/<feature>_<kind>_<start time><suffix>"""
    return (
        Path(config.rootpath) / "reports" / "automation" / config._outcome
        / f"{config._feature}_{kind}_{config._run_stamp}{suffix}"
    )


def pytest_sessionfinish(session, exitstatus):
    # Runs before the terminal summary, so the summary can print the final paths.
    session.config._outcome = "success" if exitstatus == 0 else "failure"


def pytest_collection_modifyitems(config, items):
    """Name the run's files after the feature(s) whose tests were selected."""
    features = sorted({
        getattr(item.module, "FEATURE", item.module.__name__.rsplit(".", 1)[-1].removeprefix("test_"))
        for item in items if item.module is not None
    })
    if features:
        _name_run_files(config, "__".join(features))


def pytest_unconfigure(config):
    terminal_log = _report_path(config, "terminal", ".txt")
    if config._terminal_copy is not None:
        config._terminal_copy.close_copy()
        terminal_log.parent.mkdir(parents=True, exist_ok=True)
        config._terminal_partial.replace(terminal_log)
    # The JUnit report is written over on every run; keep a copy of each run's report.
    xml_path = getattr(config.option, "xmlpath", None)
    xml_written = bool(xml_path) and Path(xml_path).exists() and config._terminal_copy is not None
    if xml_written:
        junit_copy = _report_path(config, "junit", ".xml")
        junit_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(xml_path, junit_copy)
    if not config._run_dir.exists():
        return
    feature = config._feature
    if xml_written:
        shutil.copy(xml_path, config._run_dir / f"{feature}_junit.xml")
    if config._terminal_copy is not None:
        shutil.copy(terminal_log, config._run_dir / f"{feature}_terminal.txt")


def pytest_report_header(config):
    return f"Run started: {config._run_started.strftime(TIME_FORMAT)}"


def pytest_terminal_summary(terminalreporter, config):
    """Print when the run started and ended, and how long each flow took."""
    ended = datetime.now()
    started = config._run_started
    per_flow = defaultdict(float)
    for reports in terminalreporter.stats.values():
        for report in reports:
            if getattr(report, "when", None) in ("setup", "call", "teardown"):
                # Group by test class ("file::Class::test"), or by file for tests outside a class.
                parts = report.nodeid.split("::")
                per_flow[parts[1] if len(parts) > 2 else parts[0]] += report.duration
    terminalreporter.write_sep("=", "run timing")
    terminalreporter.write_line(f"Started : {started.strftime(TIME_FORMAT)}")
    terminalreporter.write_line(f"Ended   : {ended.strftime(TIME_FORMAT)}")
    terminalreporter.write_line(f"Total   : {_duration((ended - started).total_seconds())} (h:mm:ss)")
    for flow, seconds in per_flow.items():
        terminalreporter.write_line(f"  {flow}: {_duration(seconds)}")
    if config._run_dir.exists():
        terminalreporter.write_line(f"Screenshots: {config._run_dir}")
    if config._terminal_copy is not None:
        terminalreporter.write_line(f"Result     : {config._outcome.upper()}")
        terminalreporter.write_line(f"Report     : {_report_path(config, 'junit', '.xml')}")
        terminalreporter.write_line(f"Terminal   : {_report_path(config, 'terminal', '.txt')}")


@pytest.fixture
def driver():
    session = get_driver()
    yield session
    try:
        session.quit()
    except InvalidSessionIdException:
        # Preserve the original test outcome when Appium has already closed a session.
        pass


def pytest_runtest_setup(item):
    """In an 'incremental' class, skip the remaining steps once one has failed."""
    if "incremental" in item.keywords:
        failed = getattr(item.parent, "_failed_step", None)
        if failed is not None:
            pytest.skip(f"previous step failed: {failed}")


def _appium_session(item):
    """The Appium driver a test used, or None."""
    session = item.funcargs.get("driver")
    if session is None:
        # Step-by-step flows share a page object (e.g. `tournaments`,
        # `demo_login`) instead of a driver fixture.
        for value in item.funcargs.values():
            if isinstance(getattr(value, "driver", None), WebDriver):
                session = value.driver
                break
    if session is None and "driver" in item.fixturenames:
        # When a fixture built on `driver` fails during setup, `driver` is not
        # in funcargs yet, but its already-created value can still be fetched.
        try:
            session = item._request.getfixturevalue("driver")
        except Exception:  # driver itself failed to start; nothing to capture
            session = None
    return session


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Save a screenshot after each passed step; add the widget hierarchy for a failed one.

    Failures during fixture setup (e.g. a page not opening) are captured too.
    """
    outcome = yield
    report = outcome.get_result()
    if report.skipped:
        return
    if report.when == "setup" and not report.failed:
        return
    if report.when not in ("setup", "call"):
        return
    if report.failed and "incremental" in item.keywords:
        item.parent._failed_step = item.name
    session = _appium_session(item)
    if session is None:
        return
    config = item.config
    config._step_number += 1
    folder = config._run_dir / ("failed" if report.failed else "passed")
    folder.mkdir(parents=True, exist_ok=True)
    # Knockout and League flows share step names, so include the class name.
    name = f"{item.cls.__name__}_{item.name}" if item.cls else item.name
    if report.when == "setup":
        name += "_setup"
    evidence = folder / f"{config._step_number:02d}_{name}"
    try:
        session.save_screenshot(f"{evidence}.png")
        if report.failed:
            Path(f"{evidence}.xml").write_text(session.page_source, encoding="utf-8")
            log.error("Failure evidence saved to %s.png / .xml", evidence)
    except WebDriverException as error:
        log.warning("Could not capture step screenshot: %s", error)
