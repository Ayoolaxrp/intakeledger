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

## Version 0.2 reproducible tooling
Supported package management is pip-compatible requirements, not npm/Poetry. Create an isolated
venv (without --system-site-packages). Install with
`python -m pip install --require-hashes -r requirements-dev.lock`, then
`python -m pip install --no-build-isolation --no-deps -e .`.
requirements-dev.in declares direct tools; the universal generated lock includes complete
transitive pins, platform markers and distribution hashes. requirements-security.txt delegates
to this same lock. There are no third-party runtime dependencies. Build setuptools must match
the exact pyproject build-system pin.

Run `python scripts/verify.py --security` for full local verification. It includes the real
pipeline demo, pip check and CI-configuration validation. Coverage enforces 90% combined
statement/branch measurement, below the original 93% with room for platform/error paths.
Run `python -m coverage xml` for the XML report. See reports/REMEDIATION_REPORT.md for actual
execution evidence; the old audit is historical, not the current release gate.

To refresh locks, install uv from its official distribution, run `python scripts/lock.py`,
review the input/lock diff, hash-install in a clean environment and run the full verifier.
Keep the build pin consistent. Monthly Dependabot configuration proposes pip/action updates;
regenerate this custom-named hash lock when input versions change. Automatic merging is not
configured. Universal resolution is not proof of execution on every platform.
Tooling references: https://docs.astral.sh/uv/pip/compile/ and
https://pip.pypa.io/en/stable/cli/pip_install/ (--require-hashes).

## Windows temporary paths
On hosts whose default temporary directory contains braces, setuptools/distutils
can fail editable builds with `ValueError: invalid variable`. The verifier redirects
only its child processes' TEMP/TMP to the repository parent when this occurs. The
clean-source helper uses a disposable directory beside the checkout. For a manual
install on such a host, set TEMP and TMP to an existing writable path without braces
in that terminal. No system-wide configuration change is required.
