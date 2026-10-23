# Develop and verify IntakeLedger
Create Python 3.11+ virtual environment, install requirements-dev.lock, and install this package with `python -m pip install --no-build-isolation -e .`. On Windows use `.venv/Scripts/python.exe`. On Linux use `.venv/bin/python`.

## Run checks
Run `python scripts/verify.py` from any directory. It runs commands from the repository root and writes command results to reports/VERIFICATION.json. Full logs go to ignored reports/checks. The JSON records actual return codes and tool output summaries. The verifier stops on a failed check.

Individual checks:
```powershell
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python -m mypy src
python -m coverage run -m pytest -q
python -m coverage report
python scripts/check_repository.py
python -m build --no-isolation
python scripts/package_smoke.py
```

The verifier sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 to isolate tests from unrelated globally installed plugins. Coverage uses its own runner and needs no pytest plugin.

Install requirements-security.txt and add `--security` to run Bandit and pip-audit. Advisory queries send package names and versions to the advisory service, not source code. An unavailable scanner or failed query is a failed check, never a clean security result.

## Tests and traceability
| Requirement | Main evidence |
| --- | --- |
| R1-R2 | test_contracts.py, immutable contract and hostile JSON tests |
| R3 | mixed-row intake, insertion failure, process-death recovery |
| R4 | equivalent retries, changed identity, concurrent process retries |
| R5 | exact threshold boundary and rejection export tests |
| R6 | replay with relaxed and stricter contracts, parent identity conflicts |
| R7 | ordered exports, source digests, row digests, CLI workflow |
| R8 | busy writer, unrelated database, future schema, interrupted writer |
| R9 | bounded reads, safe errors, metadata logging, CLI exit tests |
| R10 | build and package_smoke.py outside the source checkout |

## Debug
Inspect a batch with show and rows. Use --include-payload only when the raw synthetic record is needed. Use --verbose for batch metadata. database_busy means another writer exceeded the configured timeout. Retry with the same source and key. An idempotency conflict means the request changed and needs an intentionally new key.

Do not delete a database to hide an integrity error. Make an offline copy before investigation. Do not weaken schema checks to open an unknown database.

## Contributions
Add a behaviour test for each changed contract or transaction rule. Keep source formatting compatible with Ruff. Explain consequential changes in a decision record. Use real commits when author identity is configured. Do not backdate, fabricate review activity, or publish this repository without owner approval.
