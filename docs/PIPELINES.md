# Pipelines, quality and historical reprocessing

The library exposes `Pipeline.from_dict`, `PipelineEngine(ledger).run(pipeline,
input_id, key)`, `backfill(pipeline, input_ids, key)`, `execution(id)`, `resume(id)`,
`QualityRules.from_dict(...).validate(records, references)` and `Ledger.lineage(id)`.
Existing ingestion and replay APIs retain their meanings.

## Reproduce the workflow

Install the development lock as described in DEVELOPMENT.md. From the repository:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python scripts/pipeline_demo.py
```

On Linux use `PYTHONPATH=src python scripts/pipeline_demo.py`. The script uses real
SQLite storage and synthetic shipment files. Contract v1 rejects a return; a replay
under v2 accepts it, projection creates a derived batch, reference validation links
the accepted input, retry returns the same execution, and backfill processes two
recorded daily inputs. The original rejection is unchanged. No services are needed.

For individual CLI operations, initialize and register contracts using the README,
then use an ingestion batch identifier:

```text
python -m intakeledger --db intake.db pipeline examples/pipeline.json BATCH_ID --key daily-v1
python -m intakeledger --db intake.db execution EXECUTION_ID
python -m intakeledger --db intake.db lineage OUTPUT_BATCH_ID
python -m intakeledger --db intake.db rows OUTPUT_BATCH_ID
python -m intakeledger --db intake.db export OUTPUT_BATCH_ID
python -m intakeledger --db intake.db backfill examples/pipeline.json DAY1_BATCH_ID DAY2_BATCH_ID --key history-v1
python -m intakeledger --db intake.db resume EXECUTION_ID
```

Pipeline/execution/resume/backfill return JSON; non-completed results exit 5.
An active execution retry exits 4 (`execution_busy`); changed retry input exits 3.
Lineage and row diagnostics are deterministic JSON exports, without raw payload by
default. Accepted export deliberately includes values.

## Definitions and dependencies

See examples/pipeline.json for the complete supported format. A pipeline has a
name, positive immutable-in-request version, and 1–32 uniquely named stages.
Its normalized JSON is at most 128 KiB. Stages select a registered contract by
name/version, an operation, input, explicit `depends_on`, optional quality rules,
named reference inputs and an exact-fraction `max_invalid` threshold (default 0).

`$input` selects the execution's original batch. Other selectors identify a stage
listed in `depends_on`. Reference selectors follow the same rule. Unknown keys,
missing dependencies, self edges, cycles, duplicate dependencies and missing rule
datasets are rejected before execution. Every dependency must have completed.
Among ready stages the lexically first name runs next. Normalized plans and data
outputs are deterministic; UUIDs, event sequences and UTC timestamps are metadata.

`replay` revalidates every raw input row, including quarantine. Original line
numbers, row hashes and source digest are preserved. `project` selects named fields
from accepted rows of a committed batch, in their original order. It writes
canonical JSON with sequential line numbers and a new source digest. Missing fields
remain missing and are checked by the output contract. Empty projections fail.
There are no joins, implicit repairs, user expressions or arbitrary code stages.

## Execution, failure and recovery

Execution states are pending, running, completed, failed and interrupted. Stage
states are pending, running, completed, failed and blocked. The engine runs
sequentially and stops at the first failure. Remaining pending stages become blocked.
Records contain execution/batch IDs, definition, ordered input manifest, parent
execution, generation, per-stage attempts, start/finish times and safe error codes.
Append-only application events retain earlier attempts. Timings can be calculated
from UTC timestamps. Verbose structured logs report stage IDs/statuses and output
IDs without values; health includes execution state counts and SQLite checks.

The stage-start record commits first. Processing, output batch and quarantine,
origin/edges, completion event and checkpoint share one `BEGIN IMMEDIATE`
transaction. An insert or checkpoint failure rolls back all that stage's effects.
Earlier completed stages remain durable. A rejected quality decision commits its
evidence and failed-stage output ID, blocks export and stops downstream stages.
Retrying that deterministic rejection reuses the output; change the rules/contract
with a new execution key to reprocess it.

An execution key is scoped by pipeline name. Its identity includes the complete
canonical plan, ordered inputs, execution kind and parent execution. An identical
completed retry returns its existing result. Failed/interrupted ordinary retries
return the recorded failure. They do not silently rerun processing. Distinct keys
intentionally create distinct effects; this is not global business-event deduplication.

After investigating a failed or abandoned worker, explicitly `resume` it. Resume
increments the execution generation and reuses completed checkpoints. Old workers
must prove generation ownership at each writer transaction; an old worker cannot
commit a later stage after takeover. A caught KeyboardInterrupt rolls back the
current stage and records interruption. Hard process death may leave status running
until explicit recovery. Do not infer worker death solely from an old timestamp.
Recovery can supersede a live worker between stages. There are no automatic leases
or external side effects, and no external exactly-once delivery guarantee.

## Quality semantics

Contracts first check object shape, required/nullable fields, primitive types,
bounds and enums. Schema-invalid rows are excluded from cross-record comparisons.
Quality rules then add inspectable `{field, code, rule}` issues to existing quarantine.
Rules are bounded to 32 entries per category and 32 KiB per stage:

| Category | Example | Behaviour |
| --- | --- | --- |
| unique | `[["event_id"]]` | Composite key uniqueness; all duplicate occurrences fail |
| references | `[{"fields":["account"],"dataset":"accounts","target_fields":["id"]}]` | Every key must occur in a committed reference input's accepted rows |
| consistent | `[{"by":["order_id"],"fields":["currency"]}]` | All members of a group must have the same non-null values |
| compare | `[{"left":"minimum","op":"le","right":"maximum"}]` | Numeric `le`/`ge` or canonical JSON `eq`; booleans are not numbers |

Missing/null keys fail rather than silently passing. Canonical JSON key comparison
distinguishes integer 1 from floating 1.0. References are immutable recorded batch
snapshots, not live database queries. `records` entries of None in the standalone
rule API denote schema-invalid rows; other entries must be contract-valid objects.
No rule reports input values. The exact invalid fraction controls the entire batch:
rejected batches export nothing, committed batches export only rows without issues.

## Lineage and backfill

Each batch has one origin: ingest, replay or derived, with optional execution/stage
links. Typed parent-to-child edges record replay, derivation and reference inputs.
Foreign keys require existing batches; a recursive insertion trigger rejects cycles
and a trigger prevents edge updates. `lineage(id)` returns all ancestors sorted by
ID and edges sorted by parent/child/kind. Projection lineage is batch-level, not a
row-to-row mapping. Hashes identify content; they do not authenticate an operator.

Backfill accepts an explicit ordered manifest of 1–100 distinct batch IDs. It does
not guess date ranges from source labels. A coordinator creates one child execution
per input in that order, linked by `parent_id`, and fails fast. Child keys derive
from the coordinator ID and ordinal. Retry/resume reuses those identities and
completed child effects. Changing order or inputs under the same key conflicts.
Historical inputs remain unchanged. Retention, scheduling and parallel partitions
are outside this implementation.

## Schema and operating limits

Opening a recognized v1 ledger atomically applies bundled migration 2 and seeds
existing ingest/replay ancestry. Back up before upgrade; downgrade is unsupported.
Other application IDs and future versions fail closed. Both new and upgraded
databases use SQLite foreign keys and FULL synchronous writes. All processing is
bounded by the original 8 MiB/10,000-row/256 KiB-row limits and one local writer.
Use filesystem permissions and encrypted disks as appropriate; there is no network
authentication or database encryption. Direct database owners can bypass triggers.
Execution histories and ancestor graphs are not paginated or automatically retained.
