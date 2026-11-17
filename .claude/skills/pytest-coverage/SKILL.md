---
name: pytest-coverage
description: 'Run pytest with coverage on the framework''s pure-Python logic (utils/, e.g. the fixture planner), find uncovered lines, and add unit tests for them. Not for Appium page objects or device flows.'
---

The goal is to fully cover the framework's **device-free logic**, such as `utils/fixture_planner.py` and the helpers in `utils/`, with fast unit tests. Do not chase line coverage for `pages/` or device E2E tests. Those are proven by running flows on a device, not by coverage numbers.

## Setup

`pytest-cov` is not in `requirements.txt`. If it is missing, ask the user before installing it (`pip install pytest-cov` inside `venv`, then add it to `requirements.txt`).

## Generate a report

Run only the device-free tests (the `planner` marker needs no device):

```
pytest -m planner --cov=utils --cov-report=term-missing --cov-report=annotate:reports/cov_annotate
```

For one module:

```
pytest tests/test_fixture_planner.py --cov=utils.fixture_planner --cov-report=term-missing --cov-report=annotate:reports/cov_annotate
```

The output goes under `reports/`, which is gitignored. Never write it to the repo root.

## Read the report

`term-missing` lists the uncovered line numbers. In `reports/cov_annotate/`, there is one file per source file, and a line starting with `!` is not covered. Skip files already at 100%.

## Add tests

- Add tests for the uncovered lines and branches, following the existing style in `tests/test_fixture_planner.py`. Give each test a clear name and assert exact values.
- Mark new device-free tests with `@pytest.mark.planner`, or add a new marker in `pytest.ini`, so they run without Appium.
- Cover behaviour (edge cases, empty inputs, odd team counts and so on), not just lines. Never write tests that pass whatever the code does.
- Re-run until the logic modules are covered, then report coverage before and after.
