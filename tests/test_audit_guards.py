import copy
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from intakeledger import IntakeError, Pipeline, PipelineEngine
from intakeledger.cli import main

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verifier_replaces_stale_success_on_timeout(tmp_path, monkeypatch):
    module = script("verify")
    (tmp_path / "reports").mkdir()
    report = tmp_path / "reports/VERIFICATION.json"
    report.write_text('{"all_requested_passed":true}')
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["verify.py"])
    monkeypatch.setattr(module, "run_check", lambda *args: (124, "Check timed out"))
    assert module.main() == 1
    result = json.loads(report.read_text())
    assert not result["all_requested_passed"]
    assert result["checks"][0]["exit_code"] == 124


@pytest.mark.parametrize(
    "failure,code", [(subprocess.TimeoutExpired("x", 300), 124), (OSError(), 127)]
)
def test_launch_failures_are_recordable(failure, code, monkeypatch):
    module = script("verify")

    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(module.subprocess, "run", fail)
    assert module.run_check(["missing"], {})[0] == code


@pytest.mark.parametrize("change", ["hash", "input", "build", "duplicate"])
def test_lock_rejects_drift(tmp_path, change):
    module = script("check_lock")
    assert module.validate(ROOT) > 0
    for name in ("requirements-dev.lock", "requirements-dev.in", "pyproject.toml"):
        (tmp_path / name).write_bytes((ROOT / name).read_bytes())
    path = tmp_path / "requirements-dev.lock"
    if change == "hash":
        text = path.read_text().replace("\\\n", " ")
        path.write_text(re.sub(r"\s+--hash=sha256:[a-f0-9]+", "", text))
    elif change == "input":
        (tmp_path / "requirements-dev.in").write_text("pytest==0.0.0\n")
    elif change == "build":
        (tmp_path / "pyproject.toml").write_text('[build-system]\nrequires=["setuptools==0.0.0"]')
    else:
        text = path.read_text().replace("\\\n", " ")
        entry = next(line for line in text.splitlines() if line.startswith("pytest=="))
        path.write_text(text + "\n" + entry + "\n")
    with pytest.raises(ValueError):
        module.validate(tmp_path)


@pytest.mark.parametrize("change", ["noop", "skip", "continue", "write", "hashes"])
def test_ci_guard_rejects_disabled_gates(change):
    module = script("check_ci")
    workflow = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    module.validate(workflow)
    changed = copy.deepcopy(workflow)
    steps = changed["jobs"]["quality"]["steps"]
    coverage = next(step for step in steps if step.get("name") == "Coverage")
    if change == "noop":
        coverage["run"] = "echo skipped"
    elif change == "skip":
        coverage["if"] = "false"
    elif change == "continue":
        coverage["continue-on-error"] = "true"
    elif change == "write":
        changed["permissions"]["contents"] = "write"
    else:
        next(step for step in steps if step.get("name") == "Install")["run"] = "pip install ."
    with pytest.raises(ValueError):
        module.validate(changed)
    if change == "noop":
        result = subprocess.run(
            [
                sys.executable,
                "-O",
                "-c",
                "import runpy,json,sys;"
                "runpy.run_path(sys.argv[1])['validate'](json.loads(sys.argv[2]))",
                str(ROOT / "scripts/check_ci.py"),
                json.dumps(changed),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0 and "Missing or altered gate" in result.stderr


def test_quality_summary_distinguishes_issues_rows_and_gate(ledger, capsys):
    data = b'{"event_id":"","units":-1}\n{"event_id":"private-fixture","units":1}'
    batch = ledger.ingest(
        data, source="synthetic", key="quality", contract_name="shipments", contract_version=1
    )
    result = ledger.quality_summary(batch["id"])
    assert result["total_rows"] == 2 and result["quarantined_rows"] == 1
    assert result["valid_rows"] == result["blocked_valid_rows"] == 1
    assert result["exportable_rows"] == 0
    assert result["issue_counts"] == {"min_length": 1, "minimum": 1}
    assert "private-fixture" not in json.dumps(result)
    assert main(["--db", str(ledger.path), "quality", batch["id"]]) == 0
    assert json.loads(capsys.readouterr().out) == result
    accepted = ledger.ingest(
        data,
        source="synthetic",
        key="accepted",
        contract_name="shipments",
        contract_version=1,
        max_invalid="1/2",
    )
    assert ledger.quality_summary(accepted["id"])["exportable_rows"] == 1
    assert ledger.quality_summary(accepted["id"])["blocked_valid_rows"] == 0
    with pytest.raises(IntakeError):
        ledger.quality_summary("absent")


def test_execution_failure_logs_are_safe_and_correlated(ledger, monkeypatch, caplog):
    batch = ledger.ingest(
        b'{"event_id":"a","units":1}',
        source="synthetic",
        key="logging",
        contract_name="shipments",
        contract_version=1,
    )
    pipeline = Pipeline.from_dict(
        {
            "name": "logs",
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
    caplog.set_level("INFO", logger="intakeledger.pipeline")
    original = engine._process

    def fail(*args):
        raise RuntimeError("sensitive-fixture-value")

    monkeypatch.setattr(engine, "_process", fail)
    result = engine.run(pipeline, batch["id"], "logs")
    assert result["status"] == "failed"
    events = [json.loads(record.message) for record in caplog.records]
    terminal = [event for event in events if event["event"] == "execution_finished"][-1]
    assert terminal["execution_id"] == result["id"] and terminal["stage"] == "validate"
    assert terminal["error"] == "stage_error" and terminal["at"]
    assert "sensitive-fixture-value" not in caplog.text
    monkeypatch.setattr(engine, "_process", original)
    assert engine.resume(result["id"])["status"] == "completed"
    assert json.loads(caplog.records[-1].message)["status"] == "completed"


def test_clean_checkout_launch_failure_replaces_stale_report(tmp_path, monkeypatch):
    module = script("clean_checkout")
    (tmp_path / "reports").mkdir()
    report = tmp_path / "reports/CLEAN_CHECKOUT.json"
    report.write_text('{"all_passed":true}')

    def fail():
        raise OSError("sensitive-local-path")

    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "_execute", fail)
    assert module.main() == 1
    result = json.loads(report.read_text())
    assert result["all_passed"] is False and result["verification"] is None
    assert "sensitive-local-path" not in report.read_text()
