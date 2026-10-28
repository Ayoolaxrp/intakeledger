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

## Operational summaries (0.2.1)
`Ledger.quality_summary(batch_id)` and `intakeledger --db intake.db quality BATCH_ID`
return total, valid, quarantined, exportable and gate-blocked valid row counts,
plus sorted issue-code counts. One row may have multiple issues. A rejected batch
has zero exportable rows, even when some rows validate. This query emits no raw
records or field values and does not change a batch. Stage and terminal execution
logs now include UTC timestamps; terminal failures include stable reason codes,
execution ID, stage and generation. Exception messages are excluded. Database
execution/event records remain authoritative; logs are operational diagnostics.


## Consumer quality gates

`quality BATCH_ID` keeps its existing report-only behavior and exit code 0.
Use the opt-in gate before downstream processing:

```text
python -m intakeledger --db intake.db quality BATCH_ID --fail-on-threshold --max-invalid 1/100 --min-exportable 1
```

The library equivalent is `Ledger.quality_gate(batch_id, max_invalid="1/100",
min_exportable=1)`. It returns the existing summary plus a `gate` object with
`passed`, normalized `max_invalid`, exact `invalid_fraction`, `min_exportable`
and ordered `reasons`. The CLI exits 0 on pass, 5 on policy failure, 2 on invalid
policy. Gate options require `--fail-on-threshold`. Defaults are zero invalid rows
and at least one exportable row. Fractions compare exactly; equality passes.
Minimum exportable rows is an integer from 0 through 10,000. Scientific exponents
are bounded to -1000 through 1000 before exact rational conversion.

A rejected batch always fails, even with a looser consumer threshold. An all-invalid
committed batch fails the default minimum; allowing an empty result requires
explicit `--min-exportable 0`. Reasons distinguish stored rejection, excessive
invalid fraction and insufficient exportable rows. Issue counts count individual
issues; the invalid fraction counts rows once, even if several rules fail.

This is an observation of immutable stored validation, not revalidation or a
mutation of the ingestion decision. It cannot release a rejected batch, repair
values, or prevent an independent process from calling export. Downstream callers
must honor its exit code. Use replay with a new key/contract to change validation.
Reports omit values and can be redirected to JSON files. Verbose logging emits a
metadata-only `quality_gate_checked` event. Reports are deterministic for the same
batch/policy; event timestamps are not. `python scripts/quality_gate_demo.py`
exercises real CLI failures/passes, pipeline replay, retry and ancestry using a
temporary synthetic database; the verifier and CI both run it.

## Concrete lineage example

For one input A, a replay stage produces B; a projection of B using A as a reference
produces C. `lineage C` exports three nodes with kinds ingest/replay/derived and
edges A->B (replay), B->C (derived), A->C (reference). B and C identify their parent
execution/stage. A subsequent replay of C adds C->D (replay), preserving all three
ancestors. Nodes sort by ID; edges sort by parent/child/kind. UUID lexical order is
not execution order. `scripts/pipeline_demo.py` and the multi-hop tests demonstrate
these relationships against SQLite. No edge asserts lineage outside this database.

The normalized numerator/denominator form must also fit 64 characters. This
ensures accepted thresholds survive pipeline normalization and retry validation;
values such as 1e-62 fail early with invalid_threshold rather than after planning.
