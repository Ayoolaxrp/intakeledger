# Remediation plan — 2026-10-24

Source inspected: public main at 9fd7a196090f0fd634770ee56138cedb5ed176ca,
restored by a fresh clone after the previous workspace disappeared. Previous
unpublished remediation commits are not available in this clone. They are not
represented as recovered work.

The supplied DataFactor scores and estimated uplift are owner-reported. No
proprietary rubric or financial outcome is independently verified.

| Priority | Verified gap | Files and intended change | Behaviour evidence |
| --- | --- | --- | --- |
| 1 | Only single-batch replay exists; no persisted stage engine | pipeline.py, migration_2.sql, cli.py; bounded DAG, atomic checkpoints, explicit recovery, ordered backfill | DAG rejection, retries, failures, interruption, concurrency |
| 2 | Parent pointer represents replay only; no derived/reference graph | ledger.py, migration_2.sql; typed origins and acyclic ancestor query | multi-hop replay, derived outputs, cycle rejection, migration |
| 3 | Contracts validate rows separately; duplicate, foreign-key and cross-record rules absent | quality.py; declarative bounded rules, persist issues in existing quarantine | rule failures, schema-invalid exclusion, rejection gate |
| 4 | Development pins lack hashes; scanners resolve separately; CI bundles checks | dependency inputs/lock, CI, scripts; one universal hash lock, separate checks, coverage floor, updates | clean environment install, full verifier, package smoke, audits |
| 5 | README/HANDOFF/audit still say private and no pushed commits | docs and reports; describe actual public source and executed evidence | documentation and diff review |

No runtime dependencies, distributed infrastructure, external sinks, dashboards,
licence grant or evaluator-specific code volume will be added. Preserve existing
intake/replay APIs and all 103 original test cases. Recovery will be explicit,
generation-fenced and transactional; it will not claim external exactly-once effects.

Baseline: run the original suite and original static/build commands before editing
runtime source. Record current tool versions rather than pretending the surviving
tool environment matches the obsolete lock. Final results belong in
REMEDIATION_REPORT.md and machine-readable verification evidence.
