import json
import sqlite3
import subprocess
import sys

import pytest

from intakeledger import IntakeError, Ledger, Pipeline, PipelineEngine, QualityRules
from intakeledger.cli import main
from intakeledger.ledger import APPLICATION_ID


def plan(**changes):
    stage = {
        "name": "validate",
        "operation": "replay",
        "contract": {"name": "shipments", "version": 1},
    }
    stage.update(changes)
    return Pipeline.from_dict({"name": "daily", "version": 1, "stages": [stage]})


def ingest(ledger, key="day1", records=None):
    records = records if records is not None else [{"event_id": "a", "units": 2}]
    return ledger.ingest(
        "\n".join(json.dumps(row) for row in records).encode(),
        source="synthetic",
        key=key,
        contract_name="shipments",
        contract_version=1,
        max_invalid="1",
    )


def two_stages():
    data = plan().as_dict()
    data["stages"].append(
        {
            "name": "project",
            "operation": "project",
            "contract": {"name": "shipments", "version": 1},
            "input": "validate",
            "depends_on": ["validate"],
            "fields": ["event_id", "units"],
            "references": {"original": "$input"},
            "rules": {
                "unique": [["event_id"]],
                "references": [
                    {"dataset": "original", "fields": ["event_id"], "target_fields": ["event_id"]}
                ],
            },
        }
    )
    return Pipeline.from_dict(data)


def test_pipeline_retry_lineage_and_deterministic_export(ledger, caplog):
    parent = ingest(ledger)
    engine = PipelineEngine(ledger)
    caplog.set_level("INFO", logger="intakeledger.pipeline")
    pipeline = two_stages()
    shuffled = pipeline.as_dict()
    shuffled["stages"].reverse()
    assert Pipeline.from_dict(shuffled) == pipeline
    result = engine.run(pipeline, parent["id"], "daily")
    assert result["status"] == "completed", result
    assert [row["name"] for row in result["stages"]] == ["validate", "project"]
    assert all(
        row["attempts"] == 1 and row["started_at"] <= row["finished_at"] for row in result["stages"]
    )
    final = result["stages"][-1]["batch_id"]
    assert ledger.export(final) == ledger.export(parent["id"])
    graph = ledger.lineage(final)
    assert [node["id"] for node in graph["nodes"]] == sorted(node["id"] for node in graph["nodes"])
    assert {node["kind"] for node in graph["nodes"]} == {"ingest", "replay", "derived"}
    assert {edge["kind"] for edge in graph["edges"]} == {"replay", "derived", "reference"}
    assert all(
        node["execution_id"] == result["id"] for node in graph["nodes"] if node["kind"] != "ingest"
    )
    assert engine.run(pipeline, parent["id"], "daily") == result
    assert engine.resume(result["id"]) == result
    assert ledger.batch(parent["id"]) == parent
    assert ledger.health()["batches"] == 3
    assert "stage_finished" in caplog.text and '"batch_id"' in caplog.text
    assert "event_id" not in caplog.text


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate",
        "missing",
        "self",
        "cycle",
        "undeclared",
        "badoperation",
        "badprojection",
        "replayfields",
        "badreference",
        "missingdataset",
        "duplicate_dep",
        "unknownkey",
        "badversion",
        "empty",
    ],
)
def test_invalid_graphs(mutation):
    data = two_stages().as_dict()
    first, second = data["stages"]
    if mutation == "duplicate":
        second["name"] = first["name"]
    elif mutation == "missing":
        second["depends_on"] = ["absent"]
    elif mutation == "self":
        first["depends_on"] = [first["name"]]
    elif mutation == "cycle":
        first["depends_on"] = [second["name"]]
    elif mutation == "undeclared":
        second["depends_on"] = []
    elif mutation == "badoperation":
        first["operation"] = "shell"
    elif mutation == "badprojection":
        second["fields"] = []
    elif mutation == "replayfields":
        first["fields"] = ["units"]
    elif mutation == "badreference":
        second["references"] = []
    elif mutation == "missingdataset":
        second["references"] = {}
    elif mutation == "duplicate_dep":
        second["depends_on"] *= 2
    elif mutation == "unknownkey":
        first["typo"] = True
    elif mutation == "badversion":
        data["version"] = True
    else:
        data["stages"] = []
    with pytest.raises(IntakeError):
        Pipeline.from_dict(data)


def test_conflicting_execution_request(ledger):
    parent = ingest(ledger)
    engine = PipelineEngine(ledger)
    engine.run(plan(), parent["id"], "one")
    with pytest.raises(IntakeError) as error:
        engine.run(plan(max_invalid="1"), parent["id"], "one")
    assert error.value.code == "idempotency_conflict"
    with pytest.raises(IntakeError):
        engine.execution("missing")


def test_stage_checkpoint_rollback_and_recovery(ledger):
    parent = ingest(ledger)
    with sqlite3.connect(ledger.path) as connection:
        connection.execute("""CREATE TRIGGER fail_checkpoint BEFORE UPDATE ON stages
            WHEN NEW.name='project' AND NEW.status='completed'
            BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END""")
    engine = PipelineEngine(ledger)
    result = engine.run(two_stages(), parent["id"], "failure")
    assert result["status"] == "failed" and result["error"] == "database_error"
    assert ledger.health()["batches"] == 2
    assert result["stages"][1]["batch_id"] is None
    assert engine.run(two_stages(), parent["id"], "failure") == result
    with sqlite3.connect(ledger.path) as connection:
        connection.execute("DROP TRIGGER fail_checkpoint")
    recovered = engine.resume(result["id"])
    assert recovered["status"] == "completed"
    assert [row["attempts"] for row in recovered["stages"]] == [1, 2]
    assert ledger.health()["batches"] == 3
    assert any(event["error"] == "database_error" for event in recovered["events"])


def test_interruption_and_generation_fence(ledger, monkeypatch):
    parent = ingest(ledger)
    engine = PipelineEngine(ledger)
    original = engine._process

    def interrupt(*args):
        original(*args)
        raise KeyboardInterrupt

    monkeypatch.setattr(engine, "_process", interrupt)
    with pytest.raises(KeyboardInterrupt):
        engine.run(plan(), parent["id"], "interrupt")
    with sqlite3.connect(ledger.path) as connection:
        execution_id = connection.execute("SELECT id FROM executions").fetchone()[0]
    assert engine.execution(execution_id)["status"] == "interrupted"
    assert ledger.health()["batches"] == 1
    monkeypatch.setattr(engine, "_process", original)
    assert engine.resume(execution_id)["status"] == "completed"
    with ledger._connect() as connection, pytest.raises(IntakeError) as error:
        engine._owned(connection, execution_id, 1)
    assert error.value.code == "execution_superseded"


def test_quality_rejection_is_persisted_and_not_duplicated(ledger):
    parent = ingest(ledger, records=[{"event_id": "a", "units": 1}, {"event_id": "a", "units": 2}])
    engine = PipelineEngine(ledger)
    result = engine.run(plan(rules={"unique": [["event_id"]]}), parent["id"], "reject")
    assert result["status"] == "failed" and result["error"] == "quality_rejected"
    output = result["stages"][0]["batch_id"]
    assert ledger.batch(output)["valid_count"] == 0
    assert all(row["issues"][0]["code"] == "unique" for row in ledger.rows(output))
    with pytest.raises(IntakeError):
        ledger.export(output)
    recovered = engine.resume(result["id"])
    assert recovered["status"] == "failed"
    assert recovered["stages"][0]["error"] == "quality_rejected"
    assert ledger.health()["batches"] == 2


def test_multi_hop_replay_preserves_lines_and_hashes(ledger):
    parent = ingest(ledger)
    second = ledger.replay(
        parent["id"], key="second", contract_name="shipments", contract_version=1
    )
    third = ledger.replay(second["id"], key="third", contract_name="shipments", contract_version=1)
    assert third["parent_id"] == second["id"]
    assert ledger.rows(third["id"])[0]["row_digest"] == ledger.rows(parent["id"])[0]["row_digest"]
    assert len(ledger.lineage(third["id"])["nodes"]) == 3
    with sqlite3.connect(ledger.path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO batch_edges VALUES (?,?,'replay')", (third["id"], parent["id"])
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE batch_edges SET kind='reference'")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO batch_edges VALUES ('absent',?,'reference')", (parent["id"],)
            )


def test_backfill_order_retry_and_recovery(ledger, monkeypatch):
    ids = [ingest(ledger, key=f"day{i}")["id"] for i in range(12)]
    engine = PipelineEngine(ledger)
    original = engine._process

    def fail(connection, stage, parent, references, execution):
        if parent == ids[2]:
            raise RuntimeError("do not disclose synthetic private values")
        return original(connection, stage, parent, references, execution)

    monkeypatch.setattr(engine, "_process", fail)
    result = engine.backfill(plan(), ids, "history")
    assert result["status"] == "failed" and len(result["children"]) == 3
    assert "private" not in json.dumps(result)
    completed = [child["id"] for child in result["children"][:2]]
    monkeypatch.setattr(engine, "_process", original)
    result = engine.resume(result["id"])
    assert result["status"] == "completed"
    assert [json.loads(child["inputs"])[0] for child in result["children"]] == ids
    assert [child["id"] for child in result["children"][:2]] == completed
    assert all(
        engine.execution(child["id"])["parent_id"] == result["id"] for child in result["children"]
    )
    assert engine.backfill(plan(), ids, "history") == result
    assert ledger.health()["batches"] == 24
    with pytest.raises(IntakeError):
        engine.backfill(plan(), list(reversed(ids)), "history")
    with pytest.raises(IntakeError):
        engine.backfill(plan(), [ids[0], ids[0]], "duplicate")


def test_schema_and_quality_rejections_coexist(ledger):
    parent = ingest(
        ledger, records=[{"event_id": "a", "units": 2}, {"event_id": "a", "units": "bad"}]
    )
    result = PipelineEngine(ledger).run(
        plan(max_invalid="1/2", rules={"unique": [["event_id"]]}), parent["id"], "schema"
    )
    assert result["status"] == "completed"
    rows = ledger.rows(result["stages"][0]["batch_id"])
    assert rows[0]["issues"] == [] and rows[1]["issues"] == [{"field": "units", "code": "type"}]


def test_quality_cross_record_rules():
    rules = QualityRules.from_dict(
        {
            "consistent": [{"by": ["group"], "fields": ["currency"]}],
            "references": [{"dataset": "accounts", "fields": ["account"], "target_fields": ["id"]}],
            "compare": [{"left": "min", "op": "le", "right": "max"}],
        }
    )
    records = [
        {"group": "a", "currency": "USD", "account": 1, "min": 1, "max": 2},
        {"group": "a", "currency": "EUR", "account": 2, "min": 3, "max": 2},
        None,
    ]
    issues = rules.validate(records, {"accounts": [{"id": 1}]})
    assert {issue["code"] for issue in issues[0]} == {"consistent"}
    assert {issue["code"] for issue in issues[1]} == {"consistent", "foreign_key", "compare"}
    assert issues[2] == []
    assert "USD" not in json.dumps(issues)
    with pytest.raises(IntakeError):
        rules.validate(records)
    assert (
        QualityRules.from_dict({"unique": [["id"]]}).validate([{}, {"id": None}])[0][0]["code"]
        == "rule_missing"
    )
    assert QualityRules.from_dict({"compare": [{"left": "x", "op": "ge", "right": "y"}]}).validate(
        [{"x": 2, "y": 1}, {"x": True, "y": 1}]
    ) == [[], [{"field": "x,y", "code": "compare", "rule": "compare:0"}]]
    eq = QualityRules.from_dict({"compare": [{"left": "x", "op": "eq", "right": "y"}]})
    assert eq.validate([{"x": 1, "y": 1}, {"x": 1, "y": 1.0}, {}])[0] == []
    assert all(eq.validate([{"x": 1, "y": 1.0}, {}]))


@pytest.mark.parametrize(
    "rules",
    [
        [],
        {"unknown": []},
        {"unique": "id"},
        {"unique": [[]]},
        {"references": [{}]},
        {"references": [{"fields": ["x"], "target_fields": ["x", "y"], "dataset": "a"}]},
        {"consistent": [{"by": [], "fields": ["x"]}]},
        {"compare": [{"left": "x", "op": "eval", "right": "y"}]},
        {"compare": [{"left": "bad field", "op": "eq", "right": "y"}]},
    ],
)
def test_invalid_rules(rules):
    with pytest.raises(IntakeError):
        QualityRules.from_dict(rules)


def test_v1_upgrade_preserves_existing_replay_and_retry(tmp_path, contract):
    path = tmp_path / "old.db"
    from importlib.resources import files

    with sqlite3.connect(path) as connection:
        connection.executescript(files("intakeledger").joinpath("schema.sql").read_text())
        connection.execute(f"PRAGMA application_id={APPLICATION_ID}")
        connection.execute("PRAGMA user_version=1")
        connection.execute(
            "INSERT INTO contracts VALUES (?,?,?,?)",
            (contract.name, contract.version, contract.digest, contract.to_json()),
        )
        args = (
            "a",
            "source",
            "key",
            "request",
            "sourcehash",
            "shipments",
            1,
            None,
            "0",
            "committed",
            1,
            1,
            "2026-10-23",
        )
        connection.execute("INSERT INTO batches VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", args)
        connection.execute("INSERT INTO rows VALUES ('a',1,'{}','hash','{}','[]')")
        child = list(args)
        child[0], child[2], child[7] = "b", "child-key", "a"
        connection.execute("INSERT INTO batches VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", child)
        connection.execute("INSERT INTO rows VALUES ('b',1,'{}','hash','{}','[]')")
    ledger = Ledger(path)
    assert ledger.health()["schema_version"] == 2
    assert ledger.batch("a")["request_digest"] == "request"
    assert ledger.export("a") == [{}]
    assert ledger.lineage("a")["nodes"][0]["kind"] == "ingest"
    assert ledger.lineage("b")["edges"] == [{"parent_id": "a", "child_id": "b", "kind": "replay"}]
    assert Ledger(path).health() == ledger.health()


def test_migration_failure_rolls_back(tmp_path):
    from importlib.resources import files

    path = tmp_path / "collision.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(files("intakeledger").joinpath("schema.sql").read_text())
        connection.execute(f"PRAGMA application_id={APPLICATION_ID}")
        connection.execute("PRAGMA user_version=1")
        connection.execute("CREATE TABLE stages (value TEXT)")
    with pytest.raises(IntakeError):
        Ledger(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert not connection.execute(
            "SELECT name FROM sqlite_master WHERE name='executions'"
        ).fetchall()


def test_cli_pipeline_commands(ledger, tmp_path, capsys):
    parent = ingest(ledger)
    definition = tmp_path / "pipeline.json"
    definition.write_text(two_stages().definition, encoding="utf-8")
    args = ["--db", str(ledger.path)]
    assert main(args + ["pipeline", str(definition), parent["id"], "--key", "cli"]) == 0
    execution = json.loads(capsys.readouterr().out)
    for command in ("execution", "resume"):
        assert main(args + [command, execution["id"]]) == 0
        assert json.loads(capsys.readouterr().out)["id"] == execution["id"]
    assert main(args + ["lineage", execution["stages"][-1]["batch_id"]]) == 0
    assert len(json.loads(capsys.readouterr().out)["nodes"]) == 3
    assert main(args + ["backfill", str(definition), parent["id"], "--key", "backfill"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "completed"
    definition.write_bytes(b"\xff")
    assert main(args + ["pipeline", str(definition), parent["id"], "--key", "bad"]) == 2
    assert "invalid_encoding" in capsys.readouterr().err


def test_process_death_and_explicit_recovery(ledger, cli_env):
    parent = ingest(ledger)
    script = """
import os, sys
from intakeledger import Ledger, Pipeline, PipelineEngine
class Crash(PipelineEngine):
    def _process(self, *args):
        super()._process(*args)
        os._exit(87)
pipeline = Pipeline.from_dict({"name":"daily","version":1,"stages":[
    {"name":"validate","operation":"replay","contract":{"name":"shipments","version":1}}]})
Crash(Ledger(sys.argv[1])).run(pipeline, sys.argv[2], "crash")
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(ledger.path), parent["id"]],
        env=cli_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 87, result.stderr
    engine = PipelineEngine(ledger)
    with sqlite3.connect(ledger.path) as connection:
        execution_id = connection.execute("SELECT id FROM executions").fetchone()[0]
    assert engine.execution(execution_id)["status"] == "running"
    assert ledger.health()["batches"] == 1
    with pytest.raises(IntakeError) as error:
        engine.run(plan(), parent["id"], "crash")
    assert error.value.code == "execution_busy"
    assert engine.resume(execution_id)["status"] == "completed"
    assert ledger.health()["batches"] == 2


def test_concurrent_pipeline_retries(ledger, cli_env):
    parent = ingest(ledger)
    script = """
import json,sys
from intakeledger import Ledger, Pipeline, PipelineEngine, IntakeError
pipeline=Pipeline.from_dict(json.loads(sys.argv[3]))
try:
    result=PipelineEngine(Ledger(sys.argv[1])).run(pipeline,sys.argv[2],"concurrent")
    print(result["id"])
except IntakeError as exc:
    if exc.code != "execution_busy": raise
    print("busy")
"""
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(ledger.path), parent["id"], plan().definition],
            env=cli_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(3)
    ]
    results = [process.communicate(timeout=30) for process in processes]
    assert all(process.returncode == 0 for process in processes), results
    assert len({stdout.strip() for stdout, _ in results} - {"busy"}) == 1
    assert ledger.health()["batches"] == 2


def test_recovery_prevents_stale_worker_commit(ledger, monkeypatch):
    parent = ingest(ledger)
    engine = PipelineEngine(ledger)
    original = engine._stage
    recovered = []

    def takeover(execution_id, generation, stage, input_id):
        if not recovered:
            recovered.append(execution_id)
            assert engine.resume(execution_id)["status"] == "completed"
        return original(execution_id, generation, stage, input_id)

    monkeypatch.setattr(engine, "_stage", takeover)
    result = engine.run(plan(), parent["id"], "takeover")
    assert result["status"] == "completed" and result["generation"] == 2
    assert result["stages"][0]["attempts"] == 1
    assert ledger.health()["batches"] == 2


def test_reference_failure_is_persisted_and_lineage_remains_queryable(ledger):
    parent = ingest(ledger)
    from intakeledger import Contract

    ledger.register(
        Contract.from_dict(
            {"name": "units", "version": 1, "fields": {"units": {"type": "integer"}}}
        )
    )
    definition = plan().as_dict()
    definition["stages"][0].update(
        {
            "depends_on": ["reference"],
            "references": {"accounts": "reference"},
            "rules": {
                "references": [
                    {"fields": ["event_id"], "dataset": "accounts", "target_fields": ["units"]}
                ]
            },
        }
    )
    definition["stages"].append(
        {
            "name": "reference",
            "operation": "project",
            "fields": ["units"],
            "contract": {"name": "units", "version": 1},
        }
    )
    result = PipelineEngine(ledger).run(Pipeline.from_dict(definition), parent["id"], "reference")
    assert result["status"] == "failed" and result["error"] == "quality_rejected"
    batch_id = result["stages"][1]["batch_id"]
    assert ledger.rows(batch_id)[0]["issues"][0]["code"] == "foreign_key"
    assert len(ledger.lineage(batch_id)["nodes"]) == 3
    with pytest.raises(IntakeError):
        ledger.export(batch_id)


def test_empty_projection_has_no_partial_output(ledger):
    parent = ingest(ledger, records=[{"event_id": "bad", "units": -1}])
    result = PipelineEngine(ledger).run(
        plan(operation="project", fields=["event_id", "units"]), parent["id"], "empty"
    )
    assert result["status"] == "failed" and result["error"] == "empty_projection"
    assert ledger.health()["batches"] == 1
