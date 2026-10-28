import importlib.util
import io
import sqlite3
import sys
from pathlib import Path

import pytest

from intakeledger import Contract, IntakeError, Ledger
from intakeledger.cli import main


def test_nonempty_database_with_sqlite_like_name_is_not_modified(tmp_path):
    path = tmp_path / "unrelated.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE sqliteXprivate (value TEXT)")
        connection.execute("INSERT INTO sqliteXprivate VALUES ('synthetic-preserve')")
    before = path.read_bytes()
    with pytest.raises(IntakeError) as error:
        Ledger.initialize(path)
    assert error.value.code == "incompatible_database"
    assert path.read_bytes() == before


def test_numeric_enum_choices_must_be_distinct():
    with pytest.raises(IntakeError):
        Contract.from_dict(
            {
                "name": "a",
                "version": 1,
                "fields": {"a": {"type": "number", "enum": [1, 1.0]}},
            }
        )


@pytest.mark.parametrize("version", [True, 0, -1, 2**80])
def test_library_version_boundaries(ledger, version):
    with pytest.raises(IntakeError) as error:
        ledger.ingest(
            b'{"event_id":"one","units":1}',
            source="test",
            key="a",
            contract_name="shipments",
            contract_version=version,
        )
    assert error.value.code == "invalid_contract"


def test_usage_errors_are_machine_readable_and_hide_values(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--db", "synthetic.db", "not-a-command"])
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert '"usage_error"' in captured.err
    assert "not-a-command" not in captured.err


def test_broken_output_pipe_returns_without_traceback(monkeypatch, ledger):
    class ClosedConsumer(io.StringIO):
        def write(self, _):
            raise BrokenPipeError

    monkeypatch.setattr(sys, "stdout", ClosedConsumer())
    assert main(["--db", str(ledger.path), "health"]) == 0


def test_keyboard_interrupt_rolls_back_transaction(ledger, contract):
    with ledger._connect() as connection:
        with pytest.raises(KeyboardInterrupt), ledger._transaction(connection):
            connection.execute(
                "INSERT INTO contracts VALUES (?, ?, ?, ?)",
                ("interrupt", 1, contract.digest, contract.to_json()),
            )
            raise KeyboardInterrupt
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM contracts WHERE name='interrupt'",
            ).fetchone()[0]
            == 0
        )


def test_contract_definition_size_is_bounded():
    with pytest.raises(IntakeError) as error:
        Contract.from_dict(
            {
                "name": "a",
                "version": 1,
                "fields": {"a": {"type": "string", "enum": ["x" * (128 * 1024)]}},
            }
        )
    assert error.value.code == "invalid_contract"


def test_untrusted_property_names_are_not_echoed(contract):
    issues = contract.validate({"event_id": "a", "units": 2, "private-field-value": "secret"})
    assert issues == [{"field": "$", "code": "extra_fields"}]


def test_secret_check_detects_patterns_without_live_credentials():
    script = Path(__file__).resolve().parents[1] / "scripts" / "check_repository.py"
    spec = importlib.util.spec_from_file_location("repo_check", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.inspect_text("gh" + "p_" + "x" * 35)
    assert module.inspect_text("-----BEGIN " + "PRIVATE KEY-----")
    assert not module.inspect_text("ordinary synthetic text")


@pytest.mark.parametrize("value", ["1e-999999999", "0e999999999", "1E+1001", "1e-1_001"])
def test_threshold_exponent_is_bounded_before_fraction_conversion(value, monkeypatch):
    from intakeledger.ledger import _threshold

    def forbidden_conversion(_):
        raise AssertionError("Unbounded exponent reached Fraction")

    monkeypatch.setattr("intakeledger.ledger.Fraction", forbidden_conversion)
    with pytest.raises(IntakeError) as error:
        _threshold(value)
    assert error.value.code == "invalid_threshold"


def test_bounded_scientific_thresholds_keep_exact_retry_identity(ledger):
    from fractions import Fraction

    from intakeledger.ledger import _threshold

    assert _threshold("1e-61") == Fraction(1, 10**61)
    assert _threshold("0e1000") == 0
    options = dict(
        source="synthetic", key="exponent", contract_name="shipments", contract_version=1
    )
    data = b'{"event_id":"bounded","units":1}'
    batch = ledger.ingest(data, max_invalid="1e-4", **options)
    assert ledger.ingest(data, max_invalid="1/10000", **options) == batch
    with pytest.raises(IntakeError) as error:
        ledger.replay(
            batch["id"],
            key="unsafe",
            contract_name="shipments",
            contract_version=1,
            max_invalid="1e-1001",
        )
    assert error.value.code == "invalid_threshold"
    assert ledger.health()["batches"] == 1


@pytest.mark.parametrize("threshold", ["1e-62", "1e-1000"])
def test_threshold_rejects_non_roundtrippable_normalized_fraction(threshold):
    from intakeledger import Pipeline

    with pytest.raises(IntakeError) as error:
        Pipeline.from_dict(
            {
                "name": "small",
                "version": 1,
                "stages": [
                    {
                        "name": "check",
                        "operation": "replay",
                        "contract": {"name": "shipments", "version": 1},
                        "max_invalid": threshold,
                    }
                ],
            }
        )
    assert error.value.code == "invalid_threshold"


def test_scientific_threshold_roundtrips_through_pipeline_normalization(ledger):
    from intakeledger import Pipeline, PipelineEngine

    pipeline = Pipeline.from_dict(
        {
            "name": "small",
            "version": 1,
            "stages": [
                {
                    "name": "check",
                    "operation": "replay",
                    "contract": {"name": "shipments", "version": 1},
                    "max_invalid": "1e-61",
                }
            ],
        }
    )
    assert Pipeline.from_dict(pipeline.as_dict()) == pipeline
    batch = ledger.ingest(
        b'{"event_id":"small","units":1}',
        source="synthetic",
        key="small",
        contract_name="shipments",
        contract_version=1,
    )
    assert PipelineEngine(ledger).run(pipeline, batch["id"], "once")["status"] == "completed"
