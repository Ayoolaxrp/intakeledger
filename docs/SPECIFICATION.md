# IntakeLedger specification
IntakeLedger validates local JSONL feeds and records what happened to every row. Intended users are data engineers with periodic partner exports who need repeatable acceptance, quarantine, and replay without a hosted platform.

## Essential requirements
| ID | Behaviour |
| --- | --- |
| R1 | Register immutable named contract versions. Reject conflicting definitions and unknown keys. |
| R2 | Validate UTF-8 JSON objects against required and nullable fields, primitive types, numeric bounds, string lengths, and allowed values. Reject duplicate JSON keys and non-finite numbers. |
| R3 | Import one bounded JSONL batch atomically into a SQLite ledger. Preserve physical line numbers, raw row hashes, source digest, and contract identity. |
| R4 | Scope idempotency to source plus caller key. An identical retry returns the original batch; changed bytes, contract, quality threshold, or replay parent produce a conflict. |
| R5 | Quarantine invalid rows with stable issue codes and no payload in diagnostic logs. A batch above its permitted invalid fraction blocks all accepted-row export. |
| R6 | Replay all original rows under another contract with a parent link. Preserve source line numbers and row hashes without altering the parent. This rechecks the whole batch gate. |
| R7 | Export accepted rows as JSONL in source order. Support batch summaries, row lineage, and health/integrity checks. |
| R8 | Serialize competing writers with a bounded busy timeout. Roll back on failure or interruption. Refuse unknown schema versions and unrelated nonempty databases. |
| R9 | Provide machine-readable CLI output and errors, bounded input, and documented exit codes. |
| R10 | Build an installable wheel and source archive, with reproducible tests and static checks. |

A rejected batch retains validation results but exports no rows. A committed batch exports only valid rows. Invalid rows remain quarantined. Replay is batch-wide so a changed contract can revalidate previously accepted rows as well as invalid ones.

## Architecture and data
One process per operation. CLI parses commands; contracts own validation; ledger owns transactions and lineage; SQLite owns locking and durability. No plugins or user-provided code execution.

Tables: contracts keyed by name and positive version, batches keyed by generated identifier with unique source/key, and rows keyed by batch/physical line. Foreign keys link contracts and replay parents. Rows store raw text, SHA-256, canonical valid JSON, and issues. Schema migration 1 creates the ledger and sets application_id and user_version. Future incompatible versions fail closed.

Library API: Contract.from_dict, Ledger.register, Ledger.ingest, Ledger.replay, Ledger.batch, Ledger.rows, Ledger.export, Ledger.health. CLI: init, register, ingest, replay, show, rows, export, health. No network API.

## Non-functional requirements
Bound feeds to 8 MiB, each row to 256 KiB, 10,000 rows, 64 fields, 64 enum choices, and JSON nesting depth 32. Bound contract files to 128 KiB. Reject unpaired Unicode surrogates. Fraction comparisons use exact rational arithmetic. Execution is deterministic for row validation; batch IDs and timestamps are audit metadata, not deterministic identifiers.

Use SQLite FULL synchronous transactions on a local filesystem. Timeouts surface retryable busy errors. File permissions are the authorization boundary. The database contains raw data and is not encrypted or an immutable compliance archive.

## Errors and testing
Domain errors carry stable codes. Validation issues omit field values. CLI writes errors to stderr, results to stdout, and never prints tracebacks for expected failures. Exit 0 means successful command, 2 means input or policy error, 3 means idempotency conflict, 4 means database busy, and 5 means rejected quality gate. Broken pipes end quietly.

Tests cover contract boundaries, quality arithmetic, replay, source lineage, retry conflicts, interrupted transactions, concurrent processes, hostile input, database compatibility, installed CLI, and package contents. Seeded generated cases test row conservation without extra runtime dependencies.

## Dependencies and delivery
Python 3.11+ standard library only at runtime. Development tools are exact-version pins using installed tools where possible. setuptools builds a wheel with SQL package data. CI runs on Windows and Linux with read-only permissions. No deployment is needed. Optional enhancements are streaming very large feeds and external sink delivery. Neither belongs in this core.

## Non-goals
No general JSON Schema engine, nested-field contracts, fuzzy repair, personal-data anonymization, multi-tenant authentication, daemon, dashboard, cloud connector, or distributed database. No claim of exactly-once delivery to external systems.
