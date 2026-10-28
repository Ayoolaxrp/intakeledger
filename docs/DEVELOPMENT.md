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

## Extended audit verification (0.2.1)
`python scripts/check_lock.py` checks active exact pins, hash declarations, direct
input constraints and build-system consistency without network access. It is a CI
and full-verifier gate. It does not replace the resolver, hash installation or
advisory audit. Regenerate the lock when changing inputs/build pins; do not edit
hashes to make a failing install pass. CI validation rejects altered/no-op checks,
skipped/allowed-failure gates and writable permissions even under `python -O`.
Verifier subprocess launch/timeout failures now replace prior green evidence with
failed JSON. Clean-checkout setup failures do not reuse an old bundled verification.
See reports/EXTENDED_SCORE_AUDIT.md for the pre-change analysis and the dated
extension in REMEDIATION_REPORT.md for results. Full verification remains
`python scripts/verify.py --security`.

CI jobs now create a private `.venv` and put its executable directory on GITHUB_PATH
before hash installation. The lock is intended for an isolated environment; hosted
runner packages must not be treated as part of its dependency contract. The observed
Windows 3.12 failure is historical: hosted main run 40201420345 passed all jobs;
the old exact cause is unknown. New changes still require hosted checks.

## Release bundles and event logs
Source package smoke verifies exact bytes of requirements-dev.in,
requirements-dev.lock and requirements-security.txt before rebuilding. Missing or
changed files fail even if a wheel happened to build. The tool prints their hashes.
See OBSERVABILITY.md for structured fields and CLI logging configuration boundaries,
VALIDATION.md for request guards, and root CHANGELOG.md for release changes.


## Tests-only and offline development (0.2.3)

The full development lock remains authoritative. `requirements-test.in` declares
pytest, PyYAML (workflow tests), and packaging (lock tests). The generated test lock
includes their complete dependency closure, constrained by the development lock.
`scripts/lock.py` regenerates both; `scripts/check_lock.py` rejects changed pins,
hashes, missing roots and drift. No runtime dependencies were added. Test wheels
are ignored and are not distributed with source archives. Source smoke verifies
all five dependency input/lock/security files byte for byte.

First, with connectivity on the intended platform and Python version:

```powershell
python -m pip download --require-hashes --only-binary=:all: -r requirements-test.lock --dest .test-wheels
```

Then offline, to test the current working tree (including uncommitted edits):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip --isolated --no-cache-dir --disable-pip-version-check install --no-index --find-links .test-wheels --only-binary=:all: --require-hashes -r requirements-test.lock
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
.\.venv\Scripts\python.exe -m pytest -q
```

Use `.venv/bin/python` on Linux and `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` before its
pytest command. The tests import `src` directly; no build backend, linter, scanner,
editable installation or external service is needed for this path. It does not run
coverage, builds or advisory queries. Use a fresh venv for this recipe; use the
full development lock for `scripts/verify.py --security` and all release checks.

For a machine-readable clean-source proof, commit intended changes and run
`python scripts/offline_tests.py --wheelhouse .test-wheels`. It exports tracked HEAD
rather than trusting the working tree, creates a disposable empty venv and records
revision, setup/test exit codes and failures in reports/OFFLINE_TESTS.json. A missing
or incomplete wheelhouse fails; it does not fetch missing packages or reuse a prior
success report. CI prepares wheels in a separate connected step, then runs this
check for each Windows/Linux and Python 3.11/3.12 matrix entry.

The autouse test guard denies Python DNS/connect/send operations and propagates to
normal child Python processes via test-only sitecustomize. It is a regression guard,
not an OS firewall or malicious-code sandbox: native programs or Python launched
with -S/-I could bypass it. No container network isolation was tested. Pytest
plugins are disabled during verification; unrelated plugins are not in scope.
Wheelhouses can depend on OS/architecture/Python version. See pip's official
[repeatable installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/).

Dependency automation already exists in .github/dependabot.yml (pip and Actions).
The pip job failed on 2026-10-28; public annotations require repository write access
to view its detailed diagnostic. Do not claim that config validation fixes this
hosted failure. The owner can inspect the failed job and regenerate both locks
when inputs change. Local CLI authentication was invalid during this audit.
