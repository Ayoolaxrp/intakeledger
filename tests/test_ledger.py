import hashlib
import json
import random
import sqlite3

import pytest

from intakeledger import Contract, IntakeError, Ledger
from intakeledger.contracts import MAX_INPUT_BYTES, MAX_ROW_BYTES, MAX_ROWS
from intakeledger.ledger import APPLICATION_ID

VALID = b'{"event_id":"synthetic-1","units":2}'
INVALID = b'{"event_id":"synthetic-2","units":-1}'


def ingest(ledger, data=VALID, **kwargs):
    options = {
        "source": "synthetic",
        "key": "batch-1",
        "contract_name": "shipments",
        "contract_version": 1,
    }
    options.update(kwargs)
    return ledger.ingest(data, **options)


def test_end_to_end_mixed_rows_and_lineage(ledger):
    data = VALID + b"\r\n" + INVALID + b"\r\nnot-json\r\n"
    result = ingest(ledger, data, max_invalid="2/3")
    assert result["status"] == "committed"
    assert result["valid_count"] == 1
    assert result["row_count"] == 3
    assert result["source_digest"] == hashlib.sha256(data).hexdigest()
    assert ledger.export(result["id"]) == [{"event_id": "synthetic-1", "units": 2}]
    rows = ledger.rows(result["id"])
    assert [row["line"] for row in rows] == [1, 2, 3]
    assert [row["exportable"] for row in rows] == [True, False, False]
    assert rows[0]["row_digest"] == hashlib.sha256(VALID).hexdigest()
    assert rows[1]["issues"] == [{"field": "units", "code": "minimum"}]
    assert rows[2]["issues"] == [{"field": "$", "code": "invalid_json"}]
    assert all("raw" not in row for row in rows)
    assert ledger.rows(result["id"], include_payload=True)[0]["raw"] == VALID.decode()
    assert Ledger(ledger.path).batch(result["id"]) == result


def test_gate_rejects_every_export_and_equal_fraction_passes(ledger):
    data = VALID + b"\n" + INVALID
    rejected = ingest(ledger, data, max_invalid="0.499999")
    assert rejected["status"] == "rejected"
    assert not any(row["exportable"] for row in ledger.rows(rejected["id"]))
    with pytest.raises(IntakeError) as error:
        ledger.export(rejected["id"])
    assert error.value.code == "batch_rejected"
    accepted = ingest(ledger, data, key="second", max_invalid="0.5")
    assert accepted["status"] == "committed"


def test_retry_returns_original_and_scopes_keys_by_source(ledger):
    first = ingest(ledger, max_invalid="0.0")
    assert ingest(ledger, max_invalid="0/10") == first
    second = ingest(ledger, source="other")
    assert second["id"] != first["id"]
    assert ledger.health()["batches"] == 2


@pytest.mark.parametrize(
    "options,data",
    [
        ({}, VALID + b"\n"),
        ({"max_invalid": "0.1"}, VALID),
        ({"contract_version": 2}, VALID),
    ],
)
def test_retry_conflicts_with_changed_identity(ledger, contract, options, data):
    definition = contract.as_dict()
    definition["version"] = 2
    ledger.register(Contract.from_dict(definition))
    ingest(ledger)
    with pytest.raises(IntakeError) as error:
        ingest(ledger, data, **options)
    assert error.value.code == "idempotency_conflict"
    assert ledger.health()["batches"] == 1


def test_contract_versions_are_immutable(ledger, contract):
    assert ledger.register(contract)["digest"] == contract.digest
    definition = contract.as_dict()
    definition["fields"]["units"]["min"] = -5
    with pytest.raises(IntakeError) as error:
        ledger.register(Contract.from_dict(definition))
    assert error.value.code == "contract_conflict"


def test_replay_preserves_original_and_revalidates_entire_gate(ledger, contract):
    parent = ingest(ledger, VALID + b"\n" + INVALID)
    definition = contract.as_dict()
    definition["version"] = 2
    definition["fields"]["units"]["min"] = -10
    ledger.register(Contract.from_dict(definition))
    child = ledger.replay(
        parent["id"], key="replay-1", contract_name="shipments", contract_version=2
    )
    assert child["status"] == "committed"
    assert child["parent_id"] == parent["id"]
    assert child["source_digest"] == parent["source_digest"]
    assert len(ledger.export(child["id"])) == 2
    assert ledger.batch(parent["id"]) == parent
    assert [r["row_digest"] for r in ledger.rows(parent["id"])] == [
        r["row_digest"] for r in ledger.rows(child["id"])
    ]
    assert (
        ledger.replay(parent["id"], key="replay-1", contract_name="shipments", contract_version=2)
        == child
    )
    stricter = contract.as_dict()
    stricter["version"] = 3
    stricter["fields"]["units"]["min"] = 3
    ledger.register(Contract.from_dict(stricter))
    grandchild = ledger.replay(
        child["id"],
        key="replay-2",
        contract_name="shipments",
        contract_version=3,
        max_invalid="0.5",
    )
    assert grandchild["valid_count"] == 0
    assert grandchild["status"] == "rejected"


def test_replay_parent_is_part_of_request_identity(ledger):
    parent = ingest(ledger)
    ingest(ledger, key="taken")
    with pytest.raises(IntakeError) as error:
        ledger.replay(parent["id"], key="taken", contract_name="shipments", contract_version=1)
    assert error.value.code == "idempotency_conflict"


@pytest.mark.parametrize(
    "data,code",
    [
        (b"", "empty_input"),
        (b"\xff", "invalid_encoding"),
        (b"x" * (MAX_INPUT_BYTES + 1), "input_limit"),
        (b"x" * (MAX_ROW_BYTES + 1), "row_size_limit"),
        (b"{}\n" * (MAX_ROWS + 1), "row_limit"),
    ],
    ids=["empty", "bad-utf8", "feed-bytes", "row-bytes", "row-count"],
)
def test_input_limits_leave_no_batches(ledger, data, code):
    with pytest.raises(IntakeError) as error:
        ingest(ledger, data)
    assert error.value.code == code
    assert ledger.health()["batches"] == 0


@pytest.mark.parametrize("value", ["-0.1", "1.1", "NaN", "1/0", "x" * 40, ""])
def test_bad_threshold(ledger, value):
    with pytest.raises(IntakeError) as error:
        ingest(ledger, max_invalid=value)
    assert error.value.code == "invalid_threshold"


@pytest.mark.parametrize("label", ["", "x" * 201, "a\nb", "\ud800"])
def test_bad_label(ledger, label):
    with pytest.raises(IntakeError) as error:
        ingest(ledger, source=label)
    assert error.value.code == "invalid_label"


def test_blank_lines_are_counted_and_unicode_line_separators_are_data(ledger):
    data = (
        b"\n"
        + json.dumps({"event_id": "a\u2028b", "units": 2}, ensure_ascii=False).encode()
        + b"\n"
    )
    result = ingest(ledger, data, max_invalid="0.5")
    assert result["row_count"] == 2
    assert ledger.export(result["id"])[0]["event_id"] == "a\u2028b"


def test_all_invalid_can_be_committed_without_exportable_rows(ledger):
    result = ingest(ledger, b"null", max_invalid="1")
    assert result["status"] == "committed"
    assert ledger.export(result["id"]) == []


def test_sql_injection_labels_do_not_change_database(ledger):
    result = ingest(ledger, source="'; DROP TABLE contracts; --")
    assert ledger.export(result["id"])[0]["units"] == 2
    assert ledger.health()["ok"]


def test_failure_mid_insert_rolls_back_batch_and_all_rows(ledger):
    with sqlite3.connect(ledger.path) as connection:
        connection.execute("""CREATE TRIGGER fail_second BEFORE INSERT ON rows
                            WHEN NEW.line=2 BEGIN SELECT RAISE(ABORT, 'test failure'); END""")
    with pytest.raises(IntakeError) as error:
        ingest(ledger, VALID + b"\n" + VALID)
    assert error.value.code == "database_error"
    assert ledger.health()["rows"] == 0
    assert ledger.health()["batches"] == 0


def test_busy_writer_is_retryable(ledger):
    reader = Ledger(ledger.path, timeout=0)
    connection = sqlite3.connect(ledger.path, isolation_level=None)
    try:
        connection.execute("BEGIN IMMEDIATE")
        with pytest.raises(IntakeError) as error:
            ingest(reader)
        assert error.value.code == "database_busy"
    finally:
        connection.close()
    assert ingest(reader)["status"] == "committed"


def test_initialization_and_database_compatibility(tmp_path):
    path = tmp_path / "data.db"
    with pytest.raises(IntakeError):
        Ledger(path)
    assert not path.exists()
    ledger = Ledger(path, create=True)
    assert Ledger.initialize(path).health() == ledger.health()
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=99")
    with pytest.raises(IntakeError) as error:
        Ledger.initialize(path)
    assert error.value.code == "incompatible_database"
    other = tmp_path / "other.db"
    with sqlite3.connect(other) as connection:
        connection.execute("CREATE TABLE important (value TEXT)")
        connection.execute("INSERT INTO important VALUES ('keep')")
    before = other.read_bytes()
    with pytest.raises(IntakeError):
        Ledger.initialize(other)
    assert other.read_bytes() == before


def test_corrupt_file_is_safe_error(tmp_path):
    path = tmp_path / "bad.db"
    path.write_bytes(b"not a database")
    with pytest.raises(IntakeError) as error:
        Ledger.initialize(path)
    assert error.value.code == "database_error"


@pytest.mark.parametrize("timeout", [-1, 31, float("nan"), True])
def test_bad_timeouts(tmp_path, timeout):
    with pytest.raises(IntakeError) as error:
        Ledger(tmp_path / "data.db", timeout=timeout)
    assert error.value.code == "invalid_timeout"


def test_unknown_entities(ledger):
    with pytest.raises(IntakeError) as error:
        ingest(ledger, contract_version=9)
    assert error.value.code == "contract_not_found"
    with pytest.raises(IntakeError) as error:
        ledger.batch("missing")
    assert error.value.code == "batch_not_found"


def test_unknown_application_id_rejected(ledger):
    with sqlite3.connect(ledger.path) as connection:
        connection.execute(f"PRAGMA application_id={APPLICATION_ID + 1}")
    with pytest.raises(IntakeError) as error:
        Ledger(ledger.path)
    assert error.value.code == "incompatible_database"


def test_seeded_row_conservation_and_order(ledger):
    rng = random.Random(90210)
    for trial in range(30):
        values = [rng.randint(-5, 5) for _ in range(rng.randint(1, 30))]
        records = [{"event_id": str(i), "units": n} for i, n in enumerate(values)]
        data = b"\n".join(json.dumps(record).encode() for record in records)
        result = ingest(ledger, data, key=str(trial), max_invalid="1")
        expected = [record for record in records if record["units"] >= 0]
        assert ledger.export(result["id"]) == expected
        rows = ledger.rows(result["id"])
        assert len(rows) == len(values)
        assert sum(not row["issues"] for row in rows) == len(expected)
        assert len(rows) - result["valid_count"] == sum(value < 0 for value in values)
