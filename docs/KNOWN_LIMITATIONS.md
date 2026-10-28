# Known limitations
Implemented: bounded JSONL intake, flat versioned contracts, whole-batch quality gates, row quarantine, source and row hashes, immutable application history, batch replay, ordered export, local process concurrency, schema checks, and CLI.

Not implemented: nested-field contracts, external sink delivery, secret or personal-data anonymization, multi-tenant access, automatic retention, distributed coordination, streaming feeds beyond configured limits, UI, or remote service.

The engine buffers bounded input and row results in memory. Multiple processes share one SQLite writer. Only local filesystems with working locking are supported. Source bytes are hashed before parsing. Rows preserve their text excluding line terminators, but the complete original byte stream is not stored as a separate blob.

Replay does not repair values. It reinterprets all original rows under another contract. Duplicate business event IDs within a feed are not deduplicated. Retry identity is a request guarantee, not a claim of exactly-once delivery.

No production deployments, performance benchmarks, user studies, power-loss tests, or external security audit exist. Python 3.11 on Windows is the local validation environment. Hosted CI for revision ef4100e passed Windows and Linux on Python 3.11 and 3.12, plus the security job; see reports/HOSTED_CI_OBSERVATIONS.json. These matrix results do not establish support for every Python release or environment. DataFactor eligibility and a fresh evaluation remain unverified.

See reports/FINAL_AUDIT.md for executed checks and remaining release blockers. Project licensing and legal ownership require the owner's decision. No deployment or commercial readiness is implied by passing local tests.

## Version 0.2 superseding notes
Pipeline execution, explicit ancestry, backfill and the four rule categories now exist; the
earlier statement that business IDs cannot be checked for duplicates is superseded by opt-in
pipeline uniqueness rules. Ordinary ingestion still does not globally deduplicate events.
No joins, automatic scheduling, distributed infrastructure, row-mapping table for projections,
external delivery, retention or history pagination is implemented. Every stage buffers bounded
records and holds one SQLite writer while processing. Execution/history storage grows until
operators archive databases. Explicit resume can supersede a live worker between stages;
operators must investigate first. No automatic abandoned-run detector is present.
No public project licence has been chosen. The owner authorized public visibility and supplied
a DataFactor evaluation, but the scoring methodology and a fresh score remain unverified.
Current verified results and remaining environmental limits are in REMEDIATION_REPORT.md.

## Extended audit boundary
The owner reports 64.3 overall but elected to proceed without the latest category
breakdown/evaluated SHA. The audit cannot establish current category scores, latest
framework-specific comments or projected points. Local 94% coverage is a different
measurement from the evaluator's unknown method. The lock guard evaluates markers
on its current interpreter; the configured platform/Python CI matrix remains needed.
History secret scanning, independent security review and legal ownership/licensing
review are still outside the completed automated checks.

## 0.2.2 feedback and operational boundaries
The latest owner-supplied report gives 65.7 overall. Its missing-lock inference
conflicts with tracked files and successful clean installation. Source-package
checks now verify exact lock material; the evaluated SHA and scanner-bundle/parser
cause remain unknown. No score uplift has been measured. Logs are not transactional
or exactly-once delivery. Concurrent embedded CLI main calls are unsupported; use
host-configured library logging or separate CLI processes. See OBSERVABILITY.md.


## Current 0.2.3 work and 2026-10-28 report

The latest supplied evaluation is **68.6**, superseding the earlier dated values
above. Its category scores and current discrepancies are recorded at the top of
EXTENDED_SCORE_AUDIT.md. The evaluated SHA remains unspecified; a missing-lock
scanner result still conflicts with tracked files and executed clean installs.
No projected uplift is claimed. GitHub currently identifies ycent as repo owner.

Consumer gates now enforce an optional exact invalid fraction and minimum exported
row count. They observe stored results; callers must honor the CLI exit code.
There is still no external scheduler, cross-system lineage or warehouse connector.
Tiny thresholds whose normalized fraction exceeds 64 characters now fail early.
Offline pytest setup requires a matching pre-downloaded wheelhouse. Python socket
denial is not OS/container isolation. The actual Dependabot pip updater failure
needs its owner-only diagnostic log; configuration exists but health is unverified.
Project licensing/ownership rights and independent security/load/power-loss review
remain unresolved. GitHub ownership transfer alone does not establish IP rights.
