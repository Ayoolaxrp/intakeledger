import json
import subprocess
import sys

import pytest

from intakeledger.cli import _read, main
from intakeledger.errors import IntakeError


def call(environment, db, *args):
    return subprocess.run(
        [sys.executable, "-m", "intakeledger", "--db", str(db), *args],
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )


def test_cli_workflow(tmp_path, cli_env, contract):
    db = tmp_path / "cli.db"
    spec = tmp_path / "contract.json"
    spec.write_text(contract.to_json(), encoding="utf-8")
    feed = tmp_path / "feed.jsonl"
    feed.write_text(
        '{"event_id":"test","units":1}\n{"event_id":"bad","units":-1}', encoding="utf-8"
    )
    assert call(cli_env, db, "init").returncode == 0
    assert call(cli_env, db, "register", str(spec)).returncode == 0
    result = call(
        cli_env,
        db,
        "ingest",
        str(feed),
        "--source",
        "synthetic",
        "--key",
        "first",
        "--contract",
        "shipments",
        "--version",
        "1",
    )
    assert result.returncode == 5, result.stderr
    batch = json.loads(result.stdout)
    rejected = call(cli_env, db, "export", batch["id"])
    assert rejected.returncode == 5
    assert json.loads(rejected.stderr)["error"]["code"] == "batch_rejected"
    assert call(cli_env, db, "show", batch["id"]).returncode == 0
    rows = call(cli_env, db, "rows", batch["id"])
    assert all("raw" not in row for row in json.loads(rows.stdout))
    replay = call(
        cli_env,
        db,
        "replay",
        batch["id"],
        "--key",
        "second",
        "--contract",
        "shipments",
        "--version",
        "1",
        "--max-invalid",
        "0.5",
    )
    assert replay.returncode == 0, replay.stderr
    child = json.loads(replay.stdout)
    exported = call(cli_env, db, "export", child["id"])
    assert json.loads(exported.stdout) == {"event_id": "test", "units": 1}
    conflict = call(
        cli_env,
        db,
        "replay",
        batch["id"],
        "--key",
        "second",
        "--contract",
        "shipments",
        "--version",
        "1",
        "--max-invalid",
        "0.6",
    )
    assert conflict.returncode == 3
    health = call(cli_env, db, "health")
    assert json.loads(health.stdout)["batches"] == 2
    raw = call(cli_env, db, "rows", child["id"], "--include-payload")
    assert json.loads(raw.stdout)[0]["raw"] == '{"event_id":"test","units":1}'


def test_cli_expected_errors_hide_private_input(tmp_path, cli_env):
    db = tmp_path / "db"
    result = call(cli_env, db, "health")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert json.loads(result.stderr)["error"]["code"] == "not_initialized"
    call(cli_env, db, "init")
    missing = call(cli_env, db, "register", str(tmp_path / "private-secret-name"))
    assert json.loads(missing.stderr)["error"]["code"] == "io_error"
    assert "private-secret-name" not in missing.stderr
    bad = tmp_path / "bad"
    bad.write_bytes(b"\xff")
    assert json.loads(call(cli_env, db, "register", str(bad)).stderr)["error"]["code"] == (
        "invalid_encoding"
    )


def test_cli_read_is_bounded(tmp_path):
    file = tmp_path / "large"
    file.write_bytes(b"12345")
    with pytest.raises(IntakeError) as error:
        _read(str(file), 4)
    assert error.value.code == "input_limit"


def test_metadata_logging_omits_payload(ledger, caplog):
    caplog.set_level("INFO", logger="intakeledger.ledger")
    ledger.ingest(
        b'{"event_id":"private-test-payload","units":1}',
        source="local",
        key="k",
        contract_name="shipments",
        contract_version=1,
    )
    assert "private-test-payload" not in caplog.text
    assert "batch_recorded" in caplog.text


def test_main_keyboard_interrupt(monkeypatch, tmp_path):
    def interrupted(_):
        raise KeyboardInterrupt

    monkeypatch.setattr("intakeledger.cli._run", interrupted)
    assert main(["--db", str(tmp_path / "db"), "health"]) == 130
