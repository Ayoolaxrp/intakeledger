import json
import subprocess
import sys

import pytest

from intakeledger import IntakeError, Pipeline, PipelineEngine
from intakeledger.cli import main


def mixed(ledger, threshold="1/3"):
    return ledger.ingest(
        b'{"event_id":"private-fixture","units":1}\n'
        b'{"event_id":"b","units":2}\n{"event_id":"","units":-1}',
        source="synthetic",
        key="mixed",
        contract_name="shipments",
        contract_version=1,
        max_invalid=threshold,
    )


def test_gate_exact_boundary_and_deterministic_non_mutating_policy(ledger):
    batch = mixed(ledger)
    before = ledger.health(), ledger.rows(batch["id"]), ledger.lineage(batch["id"])
    result = ledger.quality_gate(batch["id"], max_invalid="1/3", min_exportable=2)
    assert result["gate"] == {
        "passed": True,
        "max_invalid": "1/3",
        "min_exportable": 2,
        "invalid_fraction": "1/3",
        "reasons": [],
    }
    assert result["issue_counts"] == {"min_length": 1, "minimum": 1}
    assert ledger.quality_gate(batch["id"], max_invalid="2/6", min_exportable=2) == result
    failed = ledger.quality_gate(batch["id"], max_invalid="0.3333333333333333")
    assert failed["gate"]["reasons"] == ["invalid_fraction_exceeded"]
    assert "private-fixture" not in json.dumps(result)
    assert ledger.batch(batch["id"]) == batch
    assert (ledger.health(), ledger.rows(batch["id"]), ledger.lineage(batch["id"])) == before


def test_gate_cannot_release_previously_rejected_batch(ledger):
    batch = mixed(ledger, "0")
    gate = ledger.quality_gate(batch["id"], max_invalid="1", min_exportable=0)["gate"]
    assert not gate["passed"] and gate["reasons"] == ["batch_rejected"]
    with pytest.raises(IntakeError) as error:
        ledger.export(batch["id"])
    assert error.value.code == "batch_rejected"


def test_gate_blocks_empty_export_unless_explicitly_allowed(ledger):
    batch = ledger.ingest(
        b'{"event_id":"bad","units":-1}',
        source="synthetic",
        key="empty",
        contract_name="shipments",
        contract_version=1,
        max_invalid="1",
    )
    assert batch["status"] == "committed" and ledger.export(batch["id"]) == []
    assert ledger.quality_gate(batch["id"], max_invalid="1")["gate"]["reasons"] == [
        "insufficient_exportable_rows"
    ]
    assert ledger.quality_gate(batch["id"], max_invalid="1", min_exportable=0)["gate"]["passed"]


@pytest.mark.parametrize("minimum", [-1, 10001, True, "1", 1.5])
def test_gate_rejects_invalid_minimum(ledger, minimum):
    batch = mixed(ledger)
    with pytest.raises(IntakeError) as error:
        ledger.quality_gate(batch["id"], min_exportable=minimum)
    assert error.value.code == "invalid_min_exportable"


@pytest.mark.parametrize("threshold", ["1e-1001", "NaN", "-0.1", "1.1", "1/0"])
def test_gate_rejects_invalid_threshold(ledger, threshold):
    batch = mixed(ledger)
    with pytest.raises(IntakeError) as error:
        ledger.quality_gate(batch["id"], max_invalid=threshold)
    assert error.value.code == "invalid_threshold"


def test_gate_missing_batch(ledger):
    with pytest.raises(IntakeError) as error:
        ledger.quality_gate("missing")
    assert error.value.code == "batch_not_found"


def test_gate_records_pipeline_rule_failures_and_reuses_retry_output(ledger):
    parent = ledger.ingest(
        b'{"event_id":"a","units":1}\n{"event_id":"a","units":2}',
        source="synthetic",
        key="duplicate",
        contract_name="shipments",
        contract_version=1,
    )
    pipeline = Pipeline.from_dict(
        {
            "name": "quality",
            "version": 1,
            "stages": [
                {
                    "name": "validate",
                    "operation": "replay",
                    "contract": {"name": "shipments", "version": 1},
                    "rules": {"unique": [["event_id"]]},
                }
            ],
        }
    )
    engine = PipelineEngine(ledger)
    execution = engine.run(pipeline, parent["id"], "once")
    output = execution["stages"][0]["batch_id"]
    result = ledger.quality_gate(output)
    assert result["issue_counts"] == {"unique": 2}
    assert result["gate"]["reasons"] == [
        "batch_rejected",
        "invalid_fraction_exceeded",
        "insufficient_exportable_rows",
    ]
    assert engine.resume(execution["id"])["stages"][0]["batch_id"] == output
    assert ledger.quality_gate(output) == result
    assert ledger.health()["batches"] == 2


def test_cli_gate_exit_codes_json_and_safe_native_event(ledger, cli_env):
    batch = mixed(ledger)
    command = [
        sys.executable,
        "-m",
        "intakeledger",
        "--db",
        str(ledger.path),
        "--verbose",
        "quality",
        batch["id"],
        "--fail-on-threshold",
    ]
    failed = subprocess.run(command, env=cli_env, capture_output=True, text=True, timeout=20)
    assert failed.returncode == 5
    assert json.loads(failed.stdout)["gate"]["reasons"] == ["invalid_fraction_exceeded"]
    event = json.loads(failed.stderr)
    assert event["event"] == "quality_gate_checked" and event["status"] == "failed"
    assert event["batch_id"] == batch["id"]
    assert "private-fixture" not in failed.stdout + failed.stderr
    passed = subprocess.run(
        command + ["--max-invalid", "1/3"], env=cli_env, capture_output=True, text=True, timeout=20
    )
    assert passed.returncode == 0 and json.loads(passed.stdout)["gate"]["passed"]


def test_cli_report_compatibility_and_policy_requires_opt_in(ledger, capsys):
    batch = mixed(ledger, "0")
    command = ["--db", str(ledger.path), "quality", batch["id"]]
    assert main(command) == 0
    assert json.loads(capsys.readouterr().out) == ledger.quality_summary(batch["id"])
    assert main(command + ["--max-invalid", "1"]) == 2
    assert json.loads(capsys.readouterr().err)["error"]["code"] == "usage_error"
    assert main(command + ["--fail-on-threshold", "--min-exportable", "-1"]) == 2
    assert json.loads(capsys.readouterr().err)["error"]["code"] == "invalid_min_exportable"


def test_ci_requires_quality_gate_demonstration():
    import importlib.util
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("check_ci_gate", root / "scripts/check_ci.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    workflow = yaml.load((root / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    step = next(
        s for s in workflow["jobs"]["quality"]["steps"] if s.get("name") == "Quality gate demo"
    )
    step["run"] = "echo skipped"
    with pytest.raises(ValueError, match="Quality gate demo"):
        module.validate(workflow)
