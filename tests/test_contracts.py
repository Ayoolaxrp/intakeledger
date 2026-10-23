import copy

import pytest

from intakeledger import Contract, IntakeError
from intakeledger.contracts import parse_json


@pytest.mark.parametrize(
    "value,code",
    [
        ([], "object_required"),
        ({}, "required"),
        ({"event_id": "", "units": 1}, "min_length"),
        ({"event_id": "a", "units": True}, "type"),
        ({"event_id": "a", "units": 1.0}, "type"),
        ({"event_id": "a", "units": -1}, "minimum"),
        ({"event_id": "a", "units": 1001}, "maximum"),
        ({"event_id": "a", "units": None}, "null_forbidden"),
        ({"event_id": "a", "units": 1, "untrusted": 4}, "extra_fields"),
    ],
)
def test_validation_boundary(contract, value, code):
    assert code in {issue["code"] for issue in contract.validate(value)}


def test_canonical_defaults_and_order(contract):
    definition = {
        "fields": {
            "units": {"max": 1000, "min": 0, "type": "integer"},
            "event_id": {"min_length": 1, "type": "string"},
        },
        "version": 1,
        "name": "shipments",
    }
    assert Contract.from_dict(definition).digest == contract.digest
    assert contract.validate({"event_id": "a", "units": 0}) == []
    assert contract.validate({"event_id": "a", "units": 1000}) == []


@pytest.mark.parametrize(
    "spec",
    [
        {"type": "unsupported"},
        {"type": "string", "typo": True},
        {"type": "integer", "required": 1},
        {"type": "string", "nullable": 0},
        {"type": "string", "min": 1},
        {"type": "integer", "max_length": 2},
        {"type": "number", "min": True},
        {"type": "number", "min": None},
        {"type": "integer", "min": 5, "max": 4},
        {"type": "string", "min_length": -1},
        {"type": "string", "max_length": 1.5},
        {"type": "string", "min_length": 5, "max_length": 4},
        {"type": "string", "enum": []},
        {"type": "integer", "enum": [True]},
        {"type": "string", "enum": ["x", "x"]},
        {"type": "number", "enum": [float("inf")]},
    ],
)
def test_invalid_field_specifications(spec):
    with pytest.raises(IntakeError, match="Invalid contract"):
        Contract.from_dict({"name": "a", "version": 1, "fields": {"a": spec}})


@pytest.mark.parametrize(
    "change",
    [
        {"version": True},
        {"version": 0},
        {"version": 2**32},
        {"name": "../bad"},
        {"name": "Bad"},
        {"fields": {}},
        {"fields": {1: {"type": "string"}}},
        {"fields": {"bad name": {"type": "string"}}},
        {"allow_extra": 1},
        {"surprise": "ignored?"},
        {"fields": []},
    ],
)
def test_reject_bad_contracts(contract, change):
    definition = copy.deepcopy(contract.as_dict())
    definition.update(change)
    with pytest.raises(IntakeError):
        Contract.from_dict(definition)


@pytest.mark.parametrize(
    "raw",
    [
        '{"a":1,"a":2}',
        '{"a":NaN}',
        '{"a":Infinity}',
        '{"a":1e999}',
        '{"a":"\\ud800"}',
        '{"a":',
        "[" * 40 + "0" + "]" * 40,
    ],
)
def test_strict_json_parser(raw):
    with pytest.raises(IntakeError) as error:
        parse_json(raw)
    assert error.value.code == "invalid_json"


def test_nullable_optional_enum_and_extra_fields():
    contract = Contract.from_dict(
        {
            "name": "a",
            "version": 1,
            "allow_extra": True,
            "fields": {
                "a": {
                    "type": "string",
                    "enum": ["x"],
                    "nullable": True,
                    "required": False,
                    "max_length": 2,
                },
                "b": {"type": "number", "min": 0.5, "max": 10},
                "c": {"type": "boolean"},
            },
        }
    )
    assert contract.validate({"b": 1.2, "c": False, "other": []}) == []
    assert contract.validate({"a": None, "b": 1, "c": True}) == []
    assert contract.validate({"a": "yy", "b": 1, "c": True}) == [{"field": "a", "code": "enum"}]
    assert contract.validate({"a": "xxx", "b": 1, "c": True}) == [
        {"field": "a", "code": "max_length"},
    ]
