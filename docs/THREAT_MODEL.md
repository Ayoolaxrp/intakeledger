# Threat model
Assets are source rows, contract definitions, batch decisions, and lineage. The operator is trusted. Incoming files and contract definitions are untrusted. SQLite is trusted persistence on a local disk. The CLI has no network listener or authentication system.

| Threat | Mitigation | Residual risk |
| --- | --- | --- |
| SQL injection through source, key, or record content | Bound SQL parameters, static schema | A user with database write access bypasses all application rules. |
| Malicious JSON and resource exhaustion | Byte, row, field, enum, length, and nesting limits | Multiple processes can still exhaust machine resources. No host-level quotas. |
| Ambiguous parsing | Duplicate-key rejection, strict UTF-8, no non-finite numbers | Floating-point numbers are not exact decimals. |
| Retry corrupts prior results | Request fingerprint and unique source/key in one transaction | Distinct keys intentionally allow the same data again. |
| Partial batch after failure | SQLite FULL synchronous transaction, rollback, process-crash tests | Device flush failures and power-loss durability are not tested. |
| Race between competing writers | BEGIN IMMEDIATE, uniqueness, bounded busy timeout | Long readers can delay commit. Network filesystems are unsupported. |
| Private values leak through diagnostics | No values in validation issues, metadata-only logging | Explicit raw-row reads and export contain data. Source labels are operator supplied. |
| Database tampering | Foreign keys, schema identity checks, health checks | SHA-256 is provenance identification, not a signed tamper-evidence scheme. |
| Dependency compromise | No runtime packages, pinned development tools, optional scanners | Python, SQLite, build tools, and CI actions still require supply-chain trust. |
| Database theft or over-retention | Operator-controlled permissions and encrypted disk recommended | No application encryption, retention scheduler, or deletion workflow. |

All bundled examples and tests are synthetic. This build has never connected to customer systems. Use a restricted working directory. Do not execute against hostile SQLite files or allow untrusted parties to choose database paths.

## Pipeline extension boundaries
Pipeline definitions and rules are untrusted declarative input, bounded by bytes, stages and
rule counts. No plugin, expression evaluator or shell command is available. Contracts remain
immutable. References use committed batch snapshots. Execution generations fence stale writers;
SQLite protects stage output/checkpoint atomicity. Failed exceptions persist safe codes rather
than exception text or payload. Raw rows and explicit exports remain operator-visible.
Schema migration 2 is transactional and only upgrades a recognized v1 ledger; back up first.
Local database owners can remove triggers or forge records. Histories are not signed and query
results are not paginated. There is no application-level access control or hostile-file sandbox.
