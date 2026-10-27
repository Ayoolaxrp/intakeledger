import io
import json
import logging
import subprocess
import sys
from datetime import datetime

import pytest

from intakeledger import Ledger, Pipeline, PipelineEngine
from intakeledger.cli import main
from intakeledger.observability import JsonFormatter, cli_logging, emit_event


def test_batch_events_have_native_fields_and_safe_json(ledger, caplog):
    caplog.set_level(logging.INFO, logger="intakeledger.ledger")
    batch = ledger.ingest(
        b'{"event_id":"synthetic-private-value","units":2}',
        source="synthetic-private-source",
        key="synthetic-private-key",
        contract_name="shipments",
        contract_version=1,
    )
    record = next(r for r in caplog.records if getattr(r, "event", None) == "batch_recorded")
    assert record.batch_id == batch["id"]
    assert record.status == "committed" and record.row_count == 1
    assert datetime.fromisoformat(record.at).utcoffset().total_seconds() == 0
    event = json.loads(JsonFormatter().format(record))
    assert event == {**json.loads(record.getMessage()), "level": "INFO", "logger": record.name}
    assert "synthetic-private" not in JsonFormatter().format(record)
    assert "synthetic-private" not in record.getMessage()


def test_pipeline_events_are_correlated_and_failures_redacted(ledger, caplog, monkeypatch):
    batch = ledger.ingest(
        b'{"event_id":"synthetic","units":1}',
        source="test",
        key="one",
        contract_name="shipments",
        contract_version=1,
    )
    pipeline = Pipeline.from_dict(
        {
            "name": "observe",
            "version": 1,
            "stages": [
                {
                    "name": "validate",
                    "operation": "replay",
                    "contract": {"name": "shipments", "version": 1},
                }
            ],
        }
    )
    engine = PipelineEngine(ledger)
    caplog.set_level(logging.INFO, logger="intakeledger.pipeline")
    result = engine.run(pipeline, batch["id"], "success")
    records = [r for r in caplog.records if r.name == "intakeledger.pipeline"]
    assert [r.event for r in records] == ["stage_started", "stage_finished", "execution_finished"]
    events = [json.loads(JsonFormatter().format(r)) for r in records]
    assert all(e["execution_id"] == result["id"] and e["generation"] == 1 for e in events)
    assert events[1]["batch_id"] == result["stages"][0]["batch_id"]
    assert events[-1]["status"] == "completed"
    original = engine._process

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic-private-exception")

    monkeypatch.setattr(engine, "_process", fail)
    failed = engine.run(pipeline, batch["id"], "failure")
    record = caplog.records[-1]
    event = json.loads(JsonFormatter().format(record))
    assert event["event"] == "execution_finished" and event["status"] == "failed"
    assert event["execution_id"] == failed["id"] and event["error"] == "stage_error"
    assert "synthetic-private-exception" not in caplog.text
    monkeypatch.setattr(engine, "_process", original)
    assert engine.resume(failed["id"])["status"] == "completed"
    assert json.loads(JsonFormatter().format(caplog.records[-1]))["status"] == "completed"


def test_verbose_cli_json_stays_on_stderr(tmp_path, contract, cli_env):
    db = tmp_path / "cli.db"
    Ledger.initialize(db).register(contract)
    source = tmp_path / "synthetic.jsonl"
    source.write_text('{"event_id":"synthetic-private-record","units":3}', encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "intakeledger",
            "--db",
            str(db),
            "--verbose",
            "ingest",
            str(source),
            "--source",
            "synthetic-private-label",
            "--key",
            "synthetic-private-key",
            "--contract",
            "shipments",
            "--version",
            "1",
        ],
        env=cli_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    batch = json.loads(result.stdout)
    events = [json.loads(line) for line in result.stderr.splitlines()]
    assert len(events) == 1
    assert events[0]["event"] == "batch_recorded" and events[0]["batch_id"] == batch["id"]
    assert events[0]["level"] == "INFO" and events[0]["logger"] == "intakeledger.ledger"
    assert "synthetic-private" not in result.stderr


def test_scoped_logging_preserves_host_handlers_and_restores_on_failure(monkeypatch):
    namespace = logging.getLogger("intakeledger")
    root = logging.getLogger()
    handlers, level, propagate = list(namespace.handlers), namespace.level, namespace.propagate
    root_handlers, root_level = list(root.handlers), root.level
    output = io.StringIO()
    monkeypatch.setattr("sys.stderr", output)
    with pytest.raises(RuntimeError), cli_logging(True):
        emit_event(logging.getLogger("intakeledger.ledger"), "batch_recorded", batch_id="synthetic")
        raise RuntimeError("synthetic-failure")
    assert namespace.handlers == handlers and namespace.level == level
    assert namespace.propagate == propagate
    assert root.handlers == root_handlers and root.level == root_level
    assert json.loads(output.getvalue())["batch_id"] == "synthetic"
    with cli_logging(False):
        assert namespace.handlers == handlers and namespace.level == level


def test_formatter_ignores_unstructured_message_and_unknown_fields():
    record = logging.LogRecord(
        "intakeledger.synthetic",
        logging.ERROR,
        "synthetic",
        1,
        "synthetic-private-message",
        (),
        None,
    )
    record.private_payload = "synthetic-private-field"
    record.exc_text = "synthetic-private-traceback"
    event = json.loads(JsonFormatter().format(record))
    assert event["event"] == "unclassified" and event["level"] == "ERROR"
    assert "synthetic-private" not in json.dumps(event)


def test_repeated_embedded_cli_calls_leave_no_logging_handlers(ledger, capsys):
    namespace = logging.getLogger("intakeledger")
    before = list(namespace.handlers)
    for _ in range(2):
        assert main(["--db", str(ledger.path), "--verbose", "health"]) == 0
    assert namespace.handlers == before
    assert all(json.loads(line)["ok"] for line in capsys.readouterr().out.splitlines())
