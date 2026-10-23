"""A deliberately bounded contract language, not a JSON Schema implementation."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any

from .errors import IntakeError

MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_ROW_BYTES = 256 * 1024
MAX_ROWS = 10_000
MAX_CONTRACT_BYTES = 128 * 1024
NAME = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")
FIELD_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}\Z")


def canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _constant(_: str) -> Any:
    raise ValueError("non-finite number")


def _check_tree(value: Any, depth: int = 0) -> None:
    if depth > 32:
        raise ValueError("JSON nesting limit")
    if isinstance(value, str):
        value.encode("utf-8", errors="strict")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite number")
    elif isinstance(value, dict):
        for key, item in value.items():
            _check_tree(key, depth + 1)
            _check_tree(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _check_tree(item, depth + 1)


def parse_json(raw: str) -> Any:
    try:
        result = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
        _check_tree(result)
        return result
    except (ValueError, RecursionError, UnicodeError) as exc:
        raise IntakeError("invalid_json", "Invalid or excessively nested JSON") from exc


def _number(value: Any) -> bool:
    return type(value) is int or (type(value) is float and math.isfinite(value))


def _matches(kind: str, value: Any) -> bool:
    return (
        (kind == "string" and type(value) is str)
        or (kind == "integer" and type(value) is int)
        or (kind == "number" and _number(value))
        or (kind == "boolean" and type(value) is bool)
    )


@dataclass(frozen=True)
class Field:
    name: str
    kind: str
    required: bool
    nullable: bool
    minimum: int | float | None
    maximum: int | float | None
    min_length: int | None
    max_length: int | None
    choices: tuple[Any, ...] | None


@dataclass(frozen=True)
class Contract:
    name: str
    version: int
    fields: tuple[Field, ...]
    allow_extra: bool

    @classmethod
    def from_dict(cls, data: Any) -> Contract:
        def invalid() -> IntakeError:
            return IntakeError("invalid_contract", "Invalid contract definition")

        if type(data) is not dict or set(data) - {"name", "version", "fields", "allow_extra"}:
            raise invalid()
        name, version, fields = data.get("name"), data.get("version"), data.get("fields")
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise invalid()
        if type(version) is not int or not 1 <= version <= 2**31 - 1:
            raise invalid()
        if type(fields) is not dict or not 1 <= len(fields) <= 64:
            raise invalid()
        extra = data.get("allow_extra", False)
        if type(extra) is not bool:
            raise invalid()
        if any(not isinstance(key, str) or not FIELD_NAME.fullmatch(key) for key in fields):
            raise invalid()
        result = []
        for field_name, spec in sorted(fields.items()):
            if not isinstance(field_name, str) or not FIELD_NAME.fullmatch(field_name):
                raise invalid()
            allowed = {
                "type",
                "required",
                "nullable",
                "min",
                "max",
                "min_length",
                "max_length",
                "enum",
            }
            if type(spec) is not dict or set(spec) - allowed:
                raise invalid()
            kind = spec.get("type")
            if kind not in ("string", "integer", "number", "boolean"):
                raise invalid()
            required, nullable = spec.get("required", True), spec.get("nullable", False)
            if type(required) is not bool or type(nullable) is not bool:
                raise invalid()
            minimum, maximum = spec.get("min"), spec.get("max")
            lo, hi = spec.get("min_length"), spec.get("max_length")
            if any(key in spec for key in ("min", "max")):
                if kind not in ("integer", "number"):
                    raise invalid()
                if any(not _number(spec[key]) for key in ("min", "max") if key in spec):
                    raise invalid()
                if minimum is not None and maximum is not None and minimum > maximum:
                    raise invalid()
            if any(key in spec for key in ("min_length", "max_length")):
                if kind != "string":
                    raise invalid()
                for key in ("min_length", "max_length"):
                    if key in spec and (type(spec[key]) is not int or not 0 <= spec[key] <= 65536):
                        raise invalid()
                if lo is not None and hi is not None and lo > hi:
                    raise invalid()
            choices = spec.get("enum")
            if "enum" in spec:
                if type(choices) is not list or not 1 <= len(choices) <= 64:
                    raise invalid()
                if any(not _matches(kind, choice) for choice in choices):
                    raise invalid()
                if len(set(choices)) != len(choices):
                    raise invalid()
            result.append(
                Field(
                    field_name,
                    kind,
                    required,
                    nullable,
                    minimum,
                    maximum,
                    lo,
                    hi,
                    tuple(choices) if choices is not None else None,
                )
            )
        contract = cls(name, version, tuple(result), extra)
        try:
            _check_tree(contract.as_dict())
            if len(contract.to_json().encode("utf-8")) > MAX_CONTRACT_BYTES:
                raise invalid()
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise invalid() from exc
        return contract

    def as_dict(self) -> dict[str, Any]:
        fields: dict[str, Any] = {}
        for field in self.fields:
            spec: dict[str, Any] = {
                "type": field.kind,
                "required": field.required,
                "nullable": field.nullable,
            }
            for key, value in (
                ("min", field.minimum),
                ("max", field.maximum),
                ("min_length", field.min_length),
                ("max_length", field.max_length),
                ("enum", list(field.choices) if field.choices is not None else None),
            ):
                if value is not None:
                    spec[key] = value
            fields[field.name] = spec
        return {
            "name": self.name,
            "version": self.version,
            "fields": fields,
            "allow_extra": self.allow_extra,
        }

    def to_json(self) -> str:
        return canonical(self.as_dict())

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def validate(self, value: Any) -> list[dict[str, str]]:
        if type(value) is not dict:
            return [{"field": "$", "code": "object_required"}]
        issues: list[dict[str, str]] = []
        if not self.allow_extra and set(value) - {f.name for f in self.fields}:
            # Untrusted field names can contain private data, so do not echo them.
            issues.append({"field": "$", "code": "extra_fields"})
        for field in self.fields:
            code = None
            if field.name not in value:
                if field.required:
                    code = "required"
            else:
                item = value[field.name]
                if item is None:
                    if not field.nullable:
                        code = "null_forbidden"
                elif not _matches(field.kind, item):
                    code = "type"
                elif field.minimum is not None and item < field.minimum:
                    code = "minimum"
                elif field.maximum is not None and item > field.maximum:
                    code = "maximum"
                elif field.min_length is not None and len(item) < field.min_length:
                    code = "min_length"
                elif field.max_length is not None and len(item) > field.max_length:
                    code = "max_length"
                elif field.choices is not None and item not in field.choices:
                    code = "enum"
            if code:
                issues.append({"field": field.name, "code": code})
        return issues
