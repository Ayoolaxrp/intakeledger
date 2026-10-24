"""Bounded declarative rules. Diagnostics contain rule identifiers, never values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import FIELD_NAME, NAME, canonical, parse_json
from .errors import IntakeError


def _fields(value: Any) -> bool:
    return (
        type(value) is list
        and 1 <= len(value) <= 64
        and all(isinstance(item, str) and FIELD_NAME.fullmatch(item) for item in value)
        and len(set(value)) == len(value)
    )


def _key(record: dict[str, Any], fields: list[str]) -> str | None:
    if any(record.get(field) is None for field in fields):
        return None
    return canonical([record[field] for field in fields])


@dataclass(frozen=True)
class QualityRules:
    definition: str

    @classmethod
    def from_dict(cls, data: Any) -> QualityRules:
        def invalid() -> IntakeError:
            return IntakeError("invalid_rules", "Invalid quality rule definition")

        if type(data) is not dict or set(data) - {"unique", "references", "consistent", "compare"}:
            raise invalid()
        for category, rules in data.items():
            if type(rules) is not list or len(rules) > 32:
                raise invalid()
            for rule in rules:
                if category == "unique":
                    if not _fields(rule):
                        raise invalid()
                    continue
                if type(rule) is not dict:
                    raise invalid()
                if category == "references":
                    if set(rule) != {"fields", "dataset", "target_fields"}:
                        raise invalid()
                    if not _fields(rule["fields"]) or not _fields(rule["target_fields"]):
                        raise invalid()
                    if len(rule["fields"]) != len(rule["target_fields"]):
                        raise invalid()
                    if not isinstance(rule["dataset"], str) or not NAME.fullmatch(rule["dataset"]):
                        raise invalid()
                elif category == "consistent":
                    if set(rule) != {"by", "fields"}:
                        raise invalid()
                    if not _fields(rule["by"]) or not _fields(rule["fields"]):
                        raise invalid()
                elif (
                    set(rule) != {"left", "op", "right"}
                    or rule["op"] not in ("eq", "le", "ge")
                    or not all(_fields([rule[field]]) for field in ("left", "right"))
                ):
                    raise invalid()
        try:
            definition = canonical(data)
            if len(definition.encode("utf-8")) > 32 * 1024:
                raise invalid()
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise invalid() from exc
        return cls(definition)

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = parse_json(self.definition)
        return result

    def validate(
        self,
        records: list[dict[str, Any] | None],
        references: dict[str, list[dict[str, Any]]] | None = None,
    ) -> list[list[dict[str, str]]]:
        """None denotes a schema-invalid row and is excluded from all group rules."""
        issues: list[list[dict[str, str]]] = [[] for _ in records]
        references = references or {}

        def issue(index: int, category: str, number: int, fields: list[str], code: str) -> None:
            issues[index].append(
                {"field": ",".join(fields), "code": code, "rule": f"{category}:{number}"}
            )

        for category, rules in sorted(self.as_dict().items()):
            for number, rule in enumerate(rules):
                if category in ("unique", "consistent"):
                    fields = rule if category == "unique" else rule["by"]
                    groups: dict[str, list[int]] = {}
                    for index, record in enumerate(records):
                        if record is None:
                            continue
                        key = _key(record, fields)
                        if key is None:
                            issue(index, category, number, fields, "rule_missing")
                        else:
                            groups.setdefault(key, []).append(index)
                    for members in groups.values():
                        if category == "unique":
                            bad = len(members) > 1
                        else:
                            values = {
                                _key(records[index] or {}, rule["fields"]) for index in members
                            }
                            bad = len(values) > 1 or None in values
                        if bad:
                            for index in members:
                                issue(index, category, number, fields, category)
                elif category == "references":
                    if rule["dataset"] not in references:
                        raise IntakeError(
                            "missing_reference", "Quality reference dataset is missing"
                        )
                    allowed = {
                        _key(row, rule["target_fields"]) for row in references[rule["dataset"]]
                    } - {None}
                    for index, record in enumerate(records):
                        if record is not None and _key(record, rule["fields"]) not in allowed:
                            issue(index, category, number, rule["fields"], "foreign_key")
                else:
                    for index, record in enumerate(records):
                        if record is None:
                            continue
                        left, right = record.get(rule["left"]), record.get(rule["right"])
                        if rule["op"] == "eq":
                            valid = left is not None and canonical(left) == canonical(right)
                        elif (
                            left is not None
                            and right is not None
                            and type(left) in (int, float)
                            and type(right) in (int, float)
                        ):
                            valid = left <= right if rule["op"] == "le" else left >= right
                        else:
                            valid = False
                        if not valid:
                            issue(index, category, number, [rule["left"], rule["right"]], "compare")
        return issues
