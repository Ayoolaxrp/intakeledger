# Baseline — 2026-10-24

Fresh clone at 9fd7a19; clean working tree and two authentic commits. No unpublished
remediation commits were recoverable. Read runtime code, tests, documents, scripts,
dependency pins, workflow and audit before implementation.

Executed using the surviving isolated `intakeledger-remediation-env` Python:

| Command | Actual result |
| --- | --- |
| `python -m coverage run -m pytest -q` (plugin autoload disabled) | 103 passed in 40.67s |
| `python -m ruff check src tests scripts` | Passed |
| `python -m ruff format --check src tests scripts` | 17 files formatted |
| `python -m mypy src` | Passed, 6 source files |
| `python -m build --no-isolation` | Failed: requires setuptools 79.0.1, environment has 84.1.0 |
| `gh auth status` | Failed: saved Ayoolaxrp token invalid |

The build failure is an environment/pin mismatch, not proof of an application bug.
The dependency inventory cannot pass against the old lock in this newer environment.
The prior 0.1 audit is historical: privacy/push/scanner statements are stale. The
new final report will supersede those statements without altering historical evidence.
