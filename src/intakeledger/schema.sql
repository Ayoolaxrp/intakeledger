CREATE TABLE contracts (
    name TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version > 0),
    digest TEXT NOT NULL,
    definition TEXT NOT NULL,
    PRIMARY KEY (name, version)
);
CREATE TABLE batches (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    contract_name TEXT NOT NULL,
    contract_version INTEGER NOT NULL,
    parent_id TEXT REFERENCES batches(id),
    threshold TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('committed', 'rejected')),
    row_count INTEGER NOT NULL CHECK (row_count > 0),
    valid_count INTEGER NOT NULL CHECK (valid_count >= 0 AND valid_count <= row_count),
    created_at TEXT NOT NULL,
    UNIQUE (source, idempotency_key),
    FOREIGN KEY (contract_name, contract_version) REFERENCES contracts(name, version)
);
CREATE TABLE rows (
    batch_id TEXT NOT NULL REFERENCES batches(id),
    line INTEGER NOT NULL CHECK (line > 0),
    raw TEXT NOT NULL,
    digest TEXT NOT NULL,
    value TEXT,
    issues TEXT NOT NULL,
    PRIMARY KEY (batch_id, line)
);
CREATE INDEX batches_parent ON batches(parent_id);
