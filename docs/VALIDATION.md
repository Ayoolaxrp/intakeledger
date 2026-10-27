# Input validation map

The operator, local paths and SQLite files are trusted. Incoming JSON, contracts,
pipeline definitions and feed records are untrusted. Validation is explicit Python
code rather than a runtime validation framework. An empty scanner pattern list
does not establish that validation is absent.

| Boundary | Actual guard / behaviour |
| --- | --- |
| CLI syntax, all commands | cli.parser and ArgumentParser.error enforce required flags, choices and integer versions; usage errors omit user-supplied text |
| File reads | cli._read reads limit + 1 bytes; ingest uses MAX_INPUT_BYTES, register/pipeline/backfill use MAX_CONTRACT_BYTES; UTF-8 failures are safe errors |
| JSON definitions and rows | contracts.parse_json rejects duplicate keys, non-finite numbers, invalid Unicode and nesting deeper than 32 |
| Contracts | Contract.from_dict validates names, positive versions, field definitions, types and bounds; Contract.validate returns schema issues without values |
| Open/initialize ledger | Ledger.__init__ validates a 0-30 second timeout, explicit initialization, application ID and supported schema; only recognized v1 upgrades |
| Register contract | Ledger.register validates the serialized contract and enforces immutable name/version identity |
| Ingest | Ledger.ingest uses _label, _threshold and _contract; requires bytes and enforces 8 MiB input, 10,000 rows, 256 KiB per row, nonempty input and UTF-8 |
| Replay | Ledger.replay validates key, threshold, parent existence and selected contract, then revalidates every original row |
| Query batch/rows/export/lineage/quality | Ledger.batch or quality_summary checks existence using bound SQL; export blocks rejected batches; rows omits raw text unless explicitly requested |
| Health | Ledger.health accepts no data input; SQLite quick_check and foreign_key_check report integrity |
| Pipeline definitions | Pipeline.from_dict checks names, versions, 1-32 stages, 128 KiB normalized plan, supported operations, fields, explicit dependencies/references and acyclicity |
| Pipeline start | PipelineEngine._create validates key, rebuilds the normalized definition, verifies input batches/contracts and immutable execution request identity |
| Backfill | PipelineEngine.backfill requires 1-100 distinct ordered string batch IDs; _create checks their existence |
| Execution/resume | PipelineEngine.execution checks existence; _drive/_owned enforce recovery status and generation ownership at writer transactions |
| Quality rules | QualityRules.from_dict checks category shapes, field sets, reference datasets, operators, per-category counts and 32 KiB normalized size |
| Cross-record quality | QualityRules.validate implements uniqueness, reference membership, group consistency and comparisons; schema-invalid rows are excluded |

Callers should construct definitions through from_dict. QualityRules.validate
expects schema-validated dictionaries or None and appropriate reference snapshots;
it is not an arbitrary raw-JSON parser. Query IDs are bound SQL values, not a
UUID-format validation API; nonexistent string IDs yield not-found errors, and
unsupported argument types may yield a safe storage error. Python annotations are
not runtime type enforcement for every argument.

Local filesystem access is an operator responsibility. There is no user/tenant
authentication, external sink, expression evaluator or shell/plugin stage. Keep
private data out of labels and stage names. Limits bound each request, not total
process memory/CPU across simultaneous operators. See THREAT_MODEL.md.

Evidence: test_contracts.py, test_ledger.py, test_regressions.py, test_cli.py and
test_pipeline.py exercise invalid definitions, hostile JSON, limits, rejected
records, rollback, replay, graphs, references and recovery. test_processes.py
covers competing writers and abrupt termination. Logging privacy is covered by
test_observability.py; no real customer records are bundled.
