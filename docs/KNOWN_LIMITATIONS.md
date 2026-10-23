# Known limitations
Implemented: bounded JSONL intake, flat versioned contracts, whole-batch quality gates, row quarantine, source and row hashes, immutable application history, batch replay, ordered export, local process concurrency, schema checks, and CLI.

Not implemented: nested-field contracts, external sink delivery, secret or personal-data anonymization, multi-tenant access, automatic retention, distributed coordination, streaming feeds beyond configured limits, UI, or remote service.

The engine buffers bounded input and row results in memory. Multiple processes share one SQLite writer. Only local filesystems with working locking are supported. Source bytes are hashed before parsing. Rows preserve their text excluding line terminators, but the complete original byte stream is not stored as a separate blob.

Replay does not repair values. It reinterprets all original rows under another contract. Duplicate business event IDs within a feed are not deduplicated. Retry identity is a request guarantee, not a claim of exactly-once delivery.

No production deployments, performance benchmarks, user studies, power-loss tests, or external security audit exist. Python 3.11 on Windows is the local validation environment. Linux and other Python versions require CI execution. Hosted CI and DataFactor eligibility remain unverified.

See reports/FINAL_AUDIT.md for executed checks and remaining release blockers. Project licensing and legal ownership require the owner's decision. No deployment or commercial readiness is implied by passing local tests.
