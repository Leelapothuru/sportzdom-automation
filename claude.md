# Sportzdom Python Automation Framework — Project Instructions

## 1. Project objective

Build and maintain a Python-based mobile application automation framework for Sportzdom.

Technology stack:
- Python
- Appium
- Pytest
- Appium Inspector for mobile widget inspection
- Azure Repos for source code version control
- Azure DevOps Pipelines for automated test execution

The framework must support local test execution and be designed for future execution through Azure DevOps pipelines.

## 2. Mandatory workflow for every feature

Whenever I say "Test [page name] — [feature flow]", follow this workflow:

1. Inspect the existing automation repository and application structure.
2. Inspect the requested screen's widget hierarchy using Appium Inspector or the available Appium session.
3. Identify and verify widget locators.
4. Prepare manual test cases with steps and expected results.
5. Perform manual testing only if the required application and device access are available. Otherwise, provide executable manual test steps and ask me to confirm actual results.
6. Prepare Python automation scripts for the same feature flow.
7. Review the scripts for correctness and compatibility with the existing framework.
8. After approval, execute the tests when the environment permits.
9. Report passed tests, failed tests, defects, and remaining work.

Never claim that manual testing or automation has been completed unless it was actually performed.

## 3. Python coding requirements

- Write all mobile automation test scripts in Python.
- Use Appium with the existing compatible Python client and Pytest.
- Follow Python conventions, use meaningful function and variable names, and keep code modular.
- Use assertions to verify application behavior.
- Use explicit waits instead of arbitrary sleep statements wherever practical.
- Handle expected errors and timeouts appropriately without hiding failures.
- Reuse fixtures, helper functions, and common utilities.
- Avoid duplicate code and hardcoded machine-specific paths.
- Use configuration or environment variables for environment-specific settings.
- Keep credentials, OTPs, access tokens, and other secrets out of source code.
- Include clear test names and useful failure messages.
- Use type hints where helpful and maintain readable documentation.

## 4. Appium widget inspection and locators

- Inspect widgets before writing page-specific interactions.
- Prefer stable accessibility IDs and resource IDs when available.
- Use other locator strategies only when necessary.
- Do not invent widget identifiers or selectors.
- Reuse verified locators and existing page objects.
- If widget information cannot be accessed, ask me to open Appium Inspector or provide the relevant widget hierarchy.

## 5. Page-wise script organization

Organize the framework by application page and feature flow.

Use the existing repository structure if one already exists. Otherwise, propose a structure such as:

sportzdom-automation/
- tests/
  - test_login_page.py
  - test_signup_page.py
  - test_home_page.py
  - test_create_tournament_page.py
  - test_tournament_details_page.py
  - test_live_match_page.py
- pages/
  - login_page.py
  - signup_page.py
  - create_tournament_page.py
  - tournament_details_page.py
  - live_match_page.py
- utils/
  - waits.py
  - configuration.py
- conftest.py
- pytest.ini
- requirements.txt
- README.md
- .gitignore
- azure-pipelines.yml (when requested and approved)

Use Page Object Model where appropriate:
- Page objects contain page-specific locators and reusable interactions.
- Test files contain test scenarios and assertions.
- Shared fixtures and utilities contain reusable setup and helper logic.
- Keep individual feature flows as separate test functions.

Do not create every suggested file automatically. Inspect the repository and propose the necessary files first.

## 6. Azure DevOps readiness

The code will eventually be pushed to Azure Repos and executed through Azure DevOps Pipelines.

Therefore:
- Make tests runnable through standard Pytest commands.
- Provide dependency declarations in requirements.txt with compatible versions.
- Support configuration through environment variables or pipeline variables.
- Do not rely on personal machine paths, local IDE state, or interactive prompts during pipeline execution.
- Generate useful test reports, preferably JUnit XML using Pytest's supported reporting options.
- Make test failures return an appropriate nonzero exit code.
- Keep secrets in approved secure pipeline variables or a secret store.
- Document the required Python, Java, Android SDK, Appium server, driver, device, and environment setup.
- Design for execution on a properly configured self-hosted agent or another compatible agent with access to the required mobile device or emulator.
- Do not assume a Microsoft-hosted agent can access a physical mobile device or has the required Android and Appium setup.
- Keep production application data safe. Prefer a dedicated test environment and test accounts.
- Do not create, modify, or run a pipeline until I explicitly request and approve that work.

## 7. Test coverage

For each feature, cover applicable scenarios:
- Successful flow.
- Invalid and missing inputs.
- Boundary conditions.
- Validation messages.
- Navigation and state persistence.
- Network and API failures where testable.
- Authentication and authorization.
- Duplicate actions.
- Relevant regression cases.

For discovered application defects, write a test that asserts the correct expected behavior. Report whether it fails because of the defect, a locator issue, a configuration problem, or another cause.

## 8. Execution and reporting

For each feature, provide:
- Manual test case list.
- Expected and actual results, distinguishing unexecuted tests.
- Automation file paths.
- Test execution command.
- Execution results and failure details.
- Bugs and evidence where available.
- Any setup requirements or blockers.

## 9. Approval and repository safety

- Read-only inspection and planning are allowed.
- Before creating or modifying files, explain the approach and list the proposed file paths.
- Wait for my explicit approval before implementing file changes.
- Ask for approval before installing dependencies, changing configuration, or executing actions that could alter application or external-system data.
- Never modify application code to make a test pass without approval.
- Keep changes local until I explicitly authorize a specific Git or remote operation.
- Never commit, push to Azure Repos, publish, upload, or deploy without my explicit instruction and approval.

## 10. Default trigger

When I say "Test [page name] — [feature flow]", use this complete workflow automatically.

Do not ask me to repeat these instructions. Ask only for essential missing details, and do not invent requirements or results.

### Automatic Appium Widget Inspection

When I request testing for a Sportzdom page:

1. Check whether an existing Appium session is available.
2. If available, retrieve the current screen's page source using the existing Appium session and Python Appium client.
3. Save the hierarchy to an appropriate local artifact file, excluding credentials and sensitive data.
4. Analyze widget attributes and identify candidate locators.
5. Verify locators against the active session when possible.
6. Prepare manual test cases and Python + Appium + Pytest automation scripts for the requested flow.
7. Organize scripts by page and reuse existing page objects.
8. If no session is available, explain how to start or expose one. Do not invent widget details.
9. Explain the proposed files and actions and wait for my approval before creating or modifying files.
10. Keep all work local unless I explicitly authorize a specific remote operation.

Do not automatically terminate an existing Appium session, create a competing session, or perform destructive actions without approval.