# IntakeLedger
IntakeLedger turns a local JSONL feed into an inspectable intake ledger. It validates rows against an immutable contract, records invalid rows in quarantine, enforces a batch quality threshold, and replays recorded batches without replacing their history.

Use it for periodic partner exports and offline data checks. It is a Python library and CLI with SQLite persistence and no third-party runtime packages.

The published 0.2.2 revision passed [hosted CI](https://github.com/ycent/intakeledger/actions/runs/40560106454)
on Windows and Linux with Python 3.11 and 3.12, including security checks. See
[the remediation report](reports/REMEDIATION_REPORT.md) for revision-specific evidence,
test results and remaining limitations. Engineering checks do not predict a licensing offer.

To try the source offline without installing packages, set PYTHONPATH to the src directory and run python scripts/demo.py. In PowerShell, use $env:PYTHONPATH = (Resolve-Path src).Path. The full install workflow follows below.

## Run the primary workflow
Requires Python 3.11+ with sqlite3. From this directory, create an environment and install the package:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m intakeledger --db intake.db init
.\.venv\Scripts\python.exe -m intakeledger --db intake.db register examples/shipments-v1.json
.\.venv\Scripts\python.exe -m intakeledger --db intake.db register examples/shipments-v2.json
.\.venv\Scripts\python.exe -m intakeledger --db intake.db ingest examples/shipments.jsonl --source synthetic --key first --contract shipments --version 1 --max-invalid 0
```

The final command returns a rejected batch and exit code 5. Its negative return quantity violates contract version 1. Copy the returned batch ID into the replay command:

```powershell
.\.venv\Scripts\python.exe -m intakeledger --db intake.db rows BATCH_ID
.\.venv\Scripts\python.exe -m intakeledger --db intake.db replay BATCH_ID --key replay-v2 --contract shipments --version 2
.\.venv\Scripts\python.exe -m intakeledger --db intake.db export REPLAY_BATCH_ID
.\.venv\Scripts\python.exe -m intakeledger --db intake.db health
```

Version 2 deliberately permits negative quantities for returns. Replay commits all three synthetic records, keeps the parent link, and retains the original source digest. The original rejected batch remains unchanged. On Linux, use `.venv/bin/python`. To run the same scenario without copying IDs, run `python scripts/demo.py` after installation. It uses a temporary database and prints its assertions and results.

## Contracts and retries
See [the contract reference](docs/CONTRACTS.md). Required and nullable have separate meanings. Integers exclude booleans and floating-point values. Unexpected properties are rejected by default.

Retry identity is source plus key. Identical source bytes, normalized contract definition, threshold, and replay parent return the original result. A changed request under that key exits 3. Equivalent thresholds such as 0.5 and 1/2 share an identity. Changes to whitespace or newline bytes change the source digest.

Rejected batches export nothing. Committed batches export their valid rows in input order. Replay revalidates every row, so a stricter replacement contract can reject a previously accepted row.

## Scope and non-goals
This is a self-contained transactional intake ledger and in-process, declarative
pipeline engine for bounded local batches. It does not schedule remote jobs,
connect warehouses or track lineage across external systems. External orchestration
and connectors need an actual integration requirement; SQLite remains the local
coordination boundary. See [pipeline semantics](docs/PIPELINES.md).

## Input validation
[The validation map](docs/VALIDATION.md) identifies CLI/library guards, limits and
caller responsibilities. [Event logging](docs/OBSERVABILITY.md) explains native
metadata fields and JSON stderr output. [Release notes](CHANGELOG.md) record changes.

## Architecture
The CLI handles bounded files and machine-readable results. Contract validation has no persistence dependencies. The ledger records a batch and its rows in one SQLite transaction. SQLite coordinates concurrent writers. Read [architecture](docs/ARCHITECTURE.md) and [decisions](docs/DECISIONS/0001-local-transactional-ledger.md) for the tradeoffs.

## Durable pipelines and historical backfill
Version 0.2 adds a persisted dependency-ordered pipeline engine, replay and projection stages,
opt-in duplicate/reference/consistency/business rules, explicit ancestry graphs, and ordered
backfill with safe retries and manual crash recovery. Existing intake commands still work.
Run `python scripts/pipeline_demo.py` after installation for a complete synthetic example.
See [pipelines](docs/PIPELINES.md) for definitions, CLI commands, states and guarantees, and
[the remediation report](reports/REMEDIATION_REPORT.md) for verified quality evidence.

## Development and verification
From a clean checkout, use an isolated environment and the committed hash lock:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/verify.py --security
```

On Linux replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.
The supported manager is pip. requirements-dev.in declares direct development
constraints; requirements-dev.lock holds transitive versions and hashes;
requirements-security.txt delegates to that same lock. No runtime packages are
required. Package smoke rejects missing/changed lock material in source archives
and prints SHA-256 digests for inspection.

The verifier runs tests with branch coverage, Ruff, strict mypy, repository checks,
build, installed-package smoke, the real pipeline demo, Bandit and pip-audit.
Installation and advisory queries need network access. See
[development](docs/DEVELOPMENT.md) for commands and evidence files.
Build with `python -m build --no-isolation` after hash installation; output is in
ignored dist/. Packages include migration SQL and the type marker.

## Operation and limits
No environment variables, credentials, ports, or daemon are required. The database path is explicit on every command. `--verbose` logs batch metadata to stderr. The local operating-system account controls database access. The raw database is not encrypted. Run only with synthetic data in this evaluation project.

Use a local filesystem with reliable SQLite locking. Back up through SQLite's backup API or copy the database after all writers exit. Do not deploy on an ephemeral filesystem. FULL synchronous mode depends on the filesystem and storage device honoring flushes.

Feeds are bounded to 8 MiB, 10,000 rows, and 256 KiB per row. Read [known limitations](docs/KNOWN_LIMITATIONS.md) and [the threat model](docs/THREAT_MODEL.md) before extending the system. There is no UI or network API.

## Provenance and commercial status
This repository was created with AI assistance for Project Atlas. It has no production users, field performance claims, or fabricated development history. [Provenance](PROVENANCE.md) records ownership assumptions and third-party notices.

The owner has not chosen a project licence. No licence grant is included. The owner authorized public visibility. Publication does not grant a project licence; ownership and buyer requirements still need verification. Research and the [final audit](reports/FINAL_AUDIT.md) distinguish observed checks from unresolved commercial claims. No DataFactor score or payment is promised.

## Quality inspection and release evidence
Use `python -m intakeledger --db intake.db quality BATCH_ID` for safe row/issue
aggregates, and `--verbose` for timestamped stage and terminal execution logs.
The [extended audit](reports/EXTENDED_SCORE_AUDIT.md) checks the latest evaluator
findings against repository evidence. Release checks now enforce direct-input/build
lock consistency and reject ineffective CI gates; failed tool launches/timeouts
produce fresh failed evidence rather than leaving an older green report.


## Enforce a consumer quality policy

```text
python -m intakeledger --db intake.db quality BATCH_ID --fail-on-threshold --max-invalid 1/100 --min-exportable 1
python scripts/quality_gate_demo.py
```

The gate exits 5 with JSON reasons when the policy fails. It cannot release a
previously rejected batch or change stored validation. Equality at the threshold
passes, using exact arithmetic. Plain `quality BATCH_ID` remains report-only.
See [pipeline semantics and a lineage example](docs/PIPELINES.md).

## Tests without network access

`requirements-dev.lock` is the authoritative pip hash lock for development, build
and security tools. `requirements-test.lock` is a generated smaller subset using
the same versions/hashes, for the entire pytest suite only. Both are tracked at
repository root and checked in source releases; this project uses no other package
manager and needs no Poetry or uv project lock. uv is only the regeneration tool.

Prepare wheels while connected, using the Python/OS intended for the offline run:

```text
python -m pip download --require-hashes --only-binary=:all: -r requirements-test.lock --dest .test-wheels
python scripts/offline_tests.py --wheelhouse .test-wheels
```

The second command exports committed HEAD, creates an empty venv, installs with
`--no-index --no-cache-dir --require-hashes`, and runs all tests with Python network
calls blocked. It records actual results in `reports/OFFLINE_TESTS.json`. Wheel
preparation needs network/cache access; offline installation requires those wheels
already present. No claim of an internet-free first download is made. For uncommitted
source and manual offline commands, see [development](docs/DEVELOPMENT.md).
