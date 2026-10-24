# 0002. Transactional local stages and explicit recovery

Accepted 2026-10-24.

The original replay API cannot express dependent transformations, cross-record
validation or resumable historical processing. Keep it and add a bounded declarative
DAG interpreted by one SQLite engine. Replay and field projection are the two useful
operations; contracts and opt-in quality rules apply uniformly to their outputs.

Reuse the ledger's internal batch writer with an existing connection. Each stage
output, issues, lineage and completion checkpoint must share the transaction. A
separate durable stage-start record exposes abandoned executions. Catch interruption
without allowing partial batches. Persist quality rejections rather than hiding them.

Use explicit generation-incrementing recovery rather than guessing worker death
from a clock-based lease. Check generation in every writer transaction. This supports
crash recovery without a daemon, time synchronization, a broker or a service database.
Operators must investigate before recovery; taking over a live worker is possible.

Backfill uses an ordered immutable manifest and stable child identities. Completed
partitions survive later failure. Origins and typed lineage edges distinguish original,
replay, derived and reference relationships. Enforce acyclicity in the database as
well as the pipeline parser. Migrate recognized v1 databases transactionally.

Alternatives: executing independent scripts leaves no atomic checkpoint contract;
distributed orchestration adds operational dependencies without a current need;
arbitrary callable stages would make retries and security guarantees unbounded.
This decision accepts sequential execution and no external side effects. Do not
generalize to remote sinks without a separate delivery/idempotency design.
