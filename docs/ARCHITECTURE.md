# Architecture
The system keeps intake decisions and the evidence behind them in a single local database.

## Components and data flow
```mermaid
flowchart TD
    CLI["CLI and bounded file input"] --> Contract["Contract validation"]
    CLI --> Ledger["Ledger operations"]
    Contract --> Ledger
    Ledger --> DB["SQLite transaction"]
    DB --> Export["Ordered export and row lineage"]
```

- contracts.py parses strict JSON and validates a small flat-field contract language.
- ledger.py owns persistence, retry identity, replay, and batch quality decisions.
- cli.py maps command arguments, local files, results, and domain failures.
- schema.sql is the initial migration. application_id identifies IntakeLedger and user_version identifies migration 1.

## Transaction boundaries
Ingest first snapshots at most 8 MiB of source bytes. It checks transport limits and UTF-8 before preparing all row results. Only then does BEGIN IMMEDIATE acquire the writer lock. A source/key lookup, batch insert, and every row insert commit together. Equivalent retries return the existing batch. Changed retry identity raises a conflict before insertion.

The request digest includes original source hash, canonical contract hash, exact rational threshold, and replay parent. The source is part of the unique database key. There is no global deduplication across distinct sources or keys.

SQLite rolls back failures and interrupted transactions. The context manager catches BaseException so KeyboardInterrupt also rolls back. Abrupt process death relies on SQLite journal recovery. No network sink participates in the transaction.

Reads return bounded batches. Multiple method calls are separate database snapshots. Application code never updates recorded contracts, batches, or rows. Direct database access remains capable of changing them.

## Lineage and replay
A row hash covers UTF-8 row bytes excluding LF or CRLF line endings. The source hash covers all original bytes, including line endings. Physical blank lines are invalid rows, not skipped rows. U+2028 inside JSON strings is data, not a row separator. BOM is not stripped.

Replay reads every original row and validates against a registered contract. The new batch points to its parent and shares original source identity and row hashes. Replaying every row is necessary because a new contract can tighten as well as relax validation. A parent is never edited.

## Gates and errors
The fraction of invalid rows is compared to the permitted threshold using Fraction, including equality. Rejection persists all validation results but blocks the entire batch from export. A committed batch may have zero exportable rows if the operator explicitly permits a threshold of 1.

IntakeError carries a stable code and a payload-free message. Database busy errors are retryable. Invalid transport input creates no batch. Schema mismatches fail before migration. Health checks SQLite structural integrity and foreign keys, not cryptographic authenticity.

## Security and tradeoffs
Parameterized SQL handles labels. Contract fields never become SQL identifiers. No eval, subprocess, plugin execution, or external connections exist in the runtime package. Source text stays in the database unless an operator requests payload rows or accepted export. File permissions, disk encryption, backups, and retention belong to the operator.

This is a bounded batch engine, not a distributed ingestion service. One writer and brief read operations fit its local use case. See the decision record and threat model for residual risks.
