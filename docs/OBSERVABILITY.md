# Event logging

Library loggers emit standard LogRecords with native event and at attributes plus
applicable batch_id, execution_id, generation, stage, status, error and row_count.
Messages retain canonical JSON for existing text handlers. Applications can attach
their own collectors without parsing the message string.

CLI --verbose installs a temporary handler on the intakeledger namespace.
JsonFormatter emits one JSON object per event to stderr, adding level and logger.
stdout remains the command result/export stream. The handler is removed and the
namespace level/propagation restored on success or failure; root logging is not
reconfigured. Existing application-owned namespace handlers remain. CLI errors
retain their documented error object and exit codes.

| Event | Context |
| --- | --- |
| batch_recorded | Batch ID, status and row count after ordinary ingest/replay |
| stage_started | Execution ID, generation and stage after start checkpoint |
| stage_finished | Execution ID, generation, stage, batch ID, status and safe error code |
| execution_finished | Execution ID, generation, terminal status, optional failing stage/code |

The formatter emits an explicit metadata allowlist. Arbitrary message/exception
text, raw rows, field values, source labels and retry keys are omitted. Unknown
unstructured records receive event unclassified; their text is omitted. Times are
UTC ISO 8601. Stage names and IDs are operator-visible metadata; never put
confidential material in configuration.

Logs are diagnostics, not a transaction journal. A process can die between a SQLite
commit and logging; retries may repeat observations. Stored batches, executions and
events remain authoritative. There is no external telemetry service or dashboard.
Concurrent embedded CLI main calls are unsupported because logging configuration
is process-global; use host-configured library logging or separate CLI processes.
SQLite still coordinates ledger writers.

Tests cover real CLI stderr/stdout separation, native attributes, failure redaction
and recovery, JSON parsing and restoration of host logging settings.
