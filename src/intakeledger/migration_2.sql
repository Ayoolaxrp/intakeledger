CREATE TABLE executions (
    id TEXT PRIMARY KEY,
    pipeline TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    definition TEXT NOT NULL,
    inputs TEXT NOT NULL,
    parent_id TEXT REFERENCES executions(id),
    kind TEXT NOT NULL CHECK (kind IN ('pipeline', 'backfill')),
    status TEXT NOT NULL CHECK (status IN ('pending','running','completed','failed','interrupted')),
    generation INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    error TEXT,
    UNIQUE (pipeline, idempotency_key)
);
CREATE TABLE stages (
    execution_id TEXT NOT NULL REFERENCES executions(id),
    name TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending','running','completed','failed','blocked')),
    attempts INTEGER NOT NULL DEFAULT 0,
    batch_id TEXT REFERENCES batches(id),
    started_at TEXT,
    finished_at TEXT,
    error TEXT,
    PRIMARY KEY (execution_id, name)
);
CREATE TABLE execution_events (
    sequence INTEGER PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES executions(id),
    generation INTEGER NOT NULL,
    stage TEXT,
    status TEXT NOT NULL,
    at TEXT NOT NULL,
    error TEXT
);
CREATE TABLE batch_origins (
    batch_id TEXT PRIMARY KEY REFERENCES batches(id),
    kind TEXT NOT NULL CHECK (kind IN ('ingest','replay','derived')),
    execution_id TEXT REFERENCES executions(id),
    stage TEXT,
    FOREIGN KEY (execution_id, stage) REFERENCES stages(execution_id, name)
);
CREATE TABLE batch_edges (
    parent_id TEXT NOT NULL REFERENCES batches(id),
    child_id TEXT NOT NULL REFERENCES batches(id),
    kind TEXT NOT NULL CHECK (kind IN ('replay','derived','reference')),
    PRIMARY KEY (parent_id, child_id, kind),
    CHECK (parent_id != child_id)
);
CREATE INDEX edges_child ON batch_edges(child_id);
CREATE INDEX executions_parent ON executions(parent_id);
CREATE TRIGGER edges_acyclic BEFORE INSERT ON batch_edges
BEGIN
    SELECT RAISE(ABORT, 'lineage cycle') WHERE EXISTS (
        WITH RECURSIVE descendants(id) AS (
            SELECT NEW.child_id UNION
            SELECT child_id FROM batch_edges JOIN descendants ON parent_id=descendants.id
        ) SELECT 1 FROM descendants WHERE id=NEW.parent_id
    );
END;
CREATE TRIGGER edges_no_update BEFORE UPDATE ON batch_edges
BEGIN
    SELECT RAISE(ABORT, 'lineage edges are append only');
END;
INSERT INTO batch_origins (batch_id, kind)
SELECT id, CASE WHEN parent_id IS NULL THEN 'ingest' ELSE 'replay' END FROM batches;
INSERT INTO batch_edges SELECT parent_id, id, 'replay' FROM batches WHERE parent_id IS NOT NULL;
