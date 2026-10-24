# IntakeLedger
IntakeLedger turns a local JSONL feed into an inspectable intake ledger. It validates rows against an immutable contract, records invalid rows in quarantine, enforces a batch quality threshold, and replays recorded batches without replacing their history.

Use it for periodic partner exports and offline data checks. It is a Python library and CLI with SQLite persistence and no third-party runtime packages.

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
```powershell
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
.\.venv\Scripts\python.exe scripts/verify.py
```

The verifier runs tests with branch coverage, Ruff, strict mypy, repository checks, build, and an installed-package smoke test. To add Bandit and dependency scanning, install `requirements-security.txt` and run `scripts/verify.py --security`. Scanner installation and advisory queries need internet access. [Development](docs/DEVELOPMENT.md) describes individual commands and evidence files.

Build with `python -m build --no-isolation` after installing the development lock. Wheels and source archives go to ignored `dist/`. The package includes the migration SQL and type marker.

## Operation and limits
No environment variables, credentials, ports, or daemon are required. The database path is explicit on every command. `--verbose` logs batch metadata to stderr. The local operating-system account controls database access. The raw database is not encrypted. Run only with synthetic data in this evaluation project.

Use a local filesystem with reliable SQLite locking. Back up through SQLite's backup API or copy the database after all writers exit. Do not deploy on an ephemeral filesystem. FULL synchronous mode depends on the filesystem and storage device honoring flushes.

Feeds are bounded to 8 MiB, 10,000 rows, and 256 KiB per row. Read [known limitations](docs/KNOWN_LIMITATIONS.md) and [the threat model](docs/THREAT_MODEL.md) before extending the system. There is no UI or network API.

## Provenance and commercial status
This repository was created with AI assistance for Project Atlas. It has no production users, field performance claims, or fabricated development history. [Provenance](PROVENANCE.md) records ownership assumptions and third-party notices.

The owner has not chosen a project licence. No licence grant is included. The owner authorized public visibility. Publication does not grant a project licence; ownership and buyer requirements still need verification. Research and the [final audit](reports/FINAL_AUDIT.md) distinguish observed checks from unresolved commercial claims. No DataFactor score or payment is promised.
