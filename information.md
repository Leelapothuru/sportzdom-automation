here i can run it but in the azure devops pipelines how can it run there with out failing







1:36 PM






Azure DevOps cannot wait for a person to type a mobile number or OTP. So the interactive test must stay skipped in the pipeline—which it already does.

Your normal pipeline command can remain:
.\venv\Scripts\python.exe -m pytest tests\test_login.py -v
With SPORTZDOM_RUN_INTERACTIVE_OTP_LOGIN unset, Azure will run the non-interactive checks and report the OTP test as skipped, not failed.

For a true OTP end-to-end pipeline test, you need one of these:
- A test-only OTP API/service that the pipeline can read.
- A dedicated test phone/SMS inbox with programmatic access, with its credentials stored as Azure DevOps secret variables.
- A backend-supported fixed test OTP or test authentication bypass enabled only in a non-production environment.
- The built-in demo-account test, run only on an isolated test device.
Do not set SPORTZDOM_RUN_INTERACTIVE_OTP_LOGIN=true in Azure DevOps; it would wait for terminal input and eventually fail.

  
1:36 PM







ok how will you suggest it now







1:37 PM






I suggest a two-tier approach:
- Local/manual testing: keep test_interactive_mobile_otp_login for a QA engineer to enter the phone number and OTP at runtime.
- Azure DevOps: run only non-interactive login checks by default. The OTP test remains skipped, so the pipeline stays reliable.
For full automated OTP verification in Azure, the best solution is a dedicated non-production test account plus a test-only OTP mechanism—ideally an API endpoint or controlled fixed OTP enabled only in QA/UAT. Store the test mobile number and any access credentials as Azure DevOps secret variables.

If the app team cannot provide that, use the existing demo-account route as the authenticated-login smoke test in the pipeline, on an isolated emulator/device.

This gives you reliable CI coverage without exposing real phone numbers or waiting for human input.