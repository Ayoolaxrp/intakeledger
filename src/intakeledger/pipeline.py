"""Sequential SQLite stage execution with durable, generation-fenced checkpoints."""

from __future__ import annotations

import hashlib
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .contracts import MAX_INPUT_BYTES, MAX_ROW_BYTES, NAME, canonical, parse_json
from .errors import IntakeError
from .ledger import Ledger, PreparedRow, _label, _prepare, _threshold
from .quality import QualityRules, _fields

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class Pipeline:
    definition: str
    order: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: Any) -> Pipeline:
        def invalid() -> IntakeError:
            return IntakeError(
                "invalid_pipeline", "Invalid pipeline definition or dependency graph"
            )

        if type(data) is not dict or set(data) != {"name", "version", "stages"}:
            raise invalid()
        if not isinstance(data["name"], str) or not NAME.fullmatch(data["name"]):
            raise invalid()
        if type(data["version"]) is not int or not 1 <= data["version"] <= 2**31 - 1:
            raise invalid()
        if type(data["stages"]) is not list or not 1 <= len(data["stages"]) <= 32:
            raise invalid()
        stages: dict[str, dict[str, Any]] = {}
        for raw in data["stages"]:
            if type(raw) is not dict or set(raw) - {
                "name",
                "operation",
                "contract",
                "input",
                "depends_on",
                "fields",
                "rules",
                "references",
                "max_invalid",
            }:
                raise invalid()
            name, operation = raw.get("name"), raw.get("operation")
            if not isinstance(name, str) or not NAME.fullmatch(name) or name in stages:
                raise invalid()
            contract = raw.get("contract")
            if type(contract) is not dict or set(contract) != {"name", "version"}:
                raise invalid()
            if not isinstance(contract["name"], str) or not NAME.fullmatch(contract["name"]):
                raise invalid()
            if type(contract["version"]) is not int or not 1 <= contract["version"] <= 2**31 - 1:
                raise invalid()
            deps = raw.get("depends_on", [])
            if type(deps) is not list or not all(isinstance(dep, str) for dep in deps):
                raise invalid()
            if len(set(deps)) != len(deps) or name in deps:
                raise invalid()
            refs = raw.get("references", {})
            if type(refs) is not dict or len(refs) > 32:
                raise invalid()
            if any(not isinstance(key, str) or not NAME.fullmatch(key) for key in refs):
                raise invalid()
            inputs = [raw.get("input", "$input"), *refs.values()]
            if any(
                not isinstance(item, str) or (item != "$input" and item not in deps)
                for item in inputs
            ):
                raise invalid()
            if operation not in ("replay", "project"):
                raise invalid()
            if operation == "project" and not _fields(raw.get("fields")):
                raise invalid()
            if operation == "replay" and "fields" in raw:
                raise invalid()
            rules = QualityRules.from_dict(raw.get("rules", {})).as_dict()
            if any(rule["dataset"] not in refs for rule in rules.get("references", [])):
                raise invalid()
            stages[name] = {
                **raw,
                "input": inputs[0],
                "depends_on": sorted(deps),
                "references": refs,
                "rules": rules,
                "max_invalid": str(_threshold(raw.get("max_invalid", "0"))),
            }
        if any(dep not in stages for stage in stages.values() for dep in stage["depends_on"]):
            raise invalid()
        order: list[str] = []
        while len(order) < len(stages):
            ready = sorted(
                name
                for name, stage in stages.items()
                if name not in order and set(stage["depends_on"]) <= set(order)
            )
            if not ready:
                raise invalid()
            order.append(ready[0])
        result = {**data, "stages": [stages[name] for name in order]}
        try:
            definition = canonical(result)
            if len(definition.encode("utf-8")) > 128 * 1024:
                raise invalid()
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise invalid() from exc
        return cls(definition, tuple(order))

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = parse_json(self.definition)
        return result


class PipelineEngine:
    def __init__(self, ledger: Ledger) -> None:
        self.ledger = ledger

    def _create(
        self,
        pipeline: Pipeline,
        inputs: list[str],
        key: str,
        kind: str,
        parent: str | None = None,
    ) -> str:
        _label(key)
        pipeline = Pipeline.from_dict(pipeline.as_dict())
        for batch_id in inputs:
            self.ledger.batch(batch_id)
        definition = pipeline.as_dict()
        for stage in definition["stages"]:
            self.ledger._contract(stage["contract"]["name"], stage["contract"]["version"])
        with self.ledger._connect() as connection, self.ledger._transaction(connection):
            previous = connection.execute(
                "SELECT * FROM executions WHERE pipeline=? AND idempotency_key=?",
                (definition["name"], key),
            ).fetchone()
            if previous:
                if (
                    previous["definition"],
                    previous["inputs"],
                    previous["kind"],
                    previous["parent_id"],
                ) != (
                    pipeline.definition,
                    canonical(inputs),
                    kind,
                    parent,
                ):
                    raise IntakeError(
                        "idempotency_conflict", "Execution key has a different request"
                    )
                return str(previous["id"])
            execution_id = uuid.uuid4().hex
            connection.execute(
                """INSERT INTO executions
                (id,pipeline,idempotency_key,definition,inputs,parent_id,kind,status,created_at)
                VALUES (?,?,?,?,?,?,?,'pending',?)""",
                (
                    execution_id,
                    definition["name"],
                    key,
                    pipeline.definition,
                    canonical(inputs),
                    parent,
                    kind,
                    _now(),
                ),
            )
            if kind == "pipeline":
                connection.executemany(
                    "INSERT INTO stages (execution_id,name,ordinal,status) VALUES "
                    "(?,?,?,'pending')",
                    [(execution_id, name, index) for index, name in enumerate(pipeline.order)],
                )
            self._event(connection, execution_id, 0, None, "pending")
        return execution_id

    def run(
        self,
        pipeline: Pipeline,
        input_id: str,
        key: str,
        *,
        parent_execution_id: str | None = None,
    ) -> dict[str, Any]:
        execution_id = self._create(pipeline, [input_id], key, "pipeline", parent_execution_id)
        return self._drive(execution_id, recover=False)

    def backfill(self, pipeline: Pipeline, input_ids: list[str], key: str) -> dict[str, Any]:
        if (
            type(input_ids) is not list
            or not 1 <= len(input_ids) <= 100
            or not all(isinstance(item, str) for item in input_ids)
            or len(set(input_ids)) != len(input_ids)
        ):
            raise IntakeError(
                "invalid_backfill", "Supply 1 to 100 distinct ordered batch identifiers"
            )
        execution_id = self._create(pipeline, input_ids, key, "backfill")
        return self._drive(execution_id, recover=False)

    def resume(self, execution_id: str) -> dict[str, Any]:
        """Operator-authorized takeover; completed stage effects are reused."""
        return self._drive(execution_id, recover=True)

    def execution(self, execution_id: str) -> dict[str, Any]:
        with self.ledger._connect() as connection:
            row = connection.execute(
                "SELECT * FROM executions WHERE id=?", (execution_id,)
            ).fetchone()
            if row is None:
                raise IntakeError("execution_not_found", "Execution does not exist")
            result = dict(row)
            result["definition"] = parse_json(result["definition"])
            result["inputs"] = parse_json(result["inputs"])
            result["stages"] = [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM stages WHERE execution_id=? ORDER BY ordinal",
                    (execution_id,),
                )
            ]
            result["events"] = [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM execution_events WHERE execution_id=? ORDER BY sequence",
                    (execution_id,),
                )
            ]
            result["children"] = [
                dict(row)
                for row in connection.execute(
                    "SELECT id,status,inputs FROM executions WHERE parent_id=? ORDER BY rowid",
                    (execution_id,),
                )
            ]
        return result

    @staticmethod
    def _owned(connection: sqlite3.Connection, execution_id: str, generation: int) -> None:
        row = connection.execute(
            "SELECT status,generation FROM executions WHERE id=?", (execution_id,)
        ).fetchone()
        if row["generation"] != generation or row["status"] != "running":
            raise IntakeError("execution_superseded", "Another recovery owns this execution")

    @staticmethod
    def _event(
        connection: sqlite3.Connection,
        execution_id: str,
        generation: int,
        stage: str | None,
        status: str,
        error: str | None = None,
    ) -> None:
        connection.execute(
            """INSERT INTO execution_events
            (execution_id,generation,stage,status,at,error) VALUES (?,?,?,?,?,?)""",
            (execution_id, generation, stage, status, _now(), error),
        )

    def _drive(self, execution_id: str, *, recover: bool) -> dict[str, Any]:
        snapshot = self.execution(execution_id)
        with self.ledger._connect() as connection, self.ledger._transaction(connection):
            row = connection.execute(
                "SELECT * FROM executions WHERE id=?", (execution_id,)
            ).fetchone()
            if row["status"] == "completed" or (
                row["status"] in ("failed", "interrupted") and not recover
            ):
                return self.execution(execution_id)
            if row["status"] == "running" and not recover:
                raise IntakeError(
                    "execution_busy", "Execution is running; recovery must be explicit"
                )
            generation = int(row["generation"]) + 1
            connection.execute(
                "UPDATE executions SET "
                "status='running',generation=?,started_at=?,finished_at=NULL,error=NULL "
                "WHERE id=?",
                (generation, _now(), execution_id),
            )
            connection.execute(
                "UPDATE stages SET status=CASE WHEN batch_id IS NULL THEN 'pending' ELSE "
                "status END,error=CASE WHEN batch_id IS NULL THEN NULL ELSE error END "
                "WHERE execution_id=? AND status!='completed'",
                (execution_id,),
            )
            self._event(connection, execution_id, generation, None, "running")
        stage_name = None
        try:
            if snapshot["kind"] == "backfill":
                pipeline = Pipeline.from_dict(snapshot["definition"])
                for index, batch_id in enumerate(snapshot["inputs"]):
                    with self.ledger._connect() as connection, self.ledger._transaction(connection):
                        self._owned(connection, execution_id, generation)
                    child_id = self._create(
                        pipeline,
                        [batch_id],
                        f"backfill:{execution_id}:{index}",
                        "pipeline",
                        execution_id,
                    )
                    child = self._drive(child_id, recover=recover)
                    if child["status"] != "completed":
                        raise IntakeError(
                            "backfill_child_failed", "Backfill stopped at a failed partition"
                        )
            else:
                for stage in snapshot["definition"]["stages"]:
                    stage_name = stage["name"]
                    self._stage(execution_id, generation, stage, snapshot["inputs"][0])
            with self.ledger._connect() as connection, self.ledger._transaction(connection):
                self._owned(connection, execution_id, generation)
                connection.execute(
                    "UPDATE executions SET status='completed',finished_at=? WHERE id=?",
                    (_now(), execution_id),
                )
                self._event(connection, execution_id, generation, None, "completed")
        except (Exception, KeyboardInterrupt) as exc:
            code = exc.code if isinstance(exc, IntakeError) else "stage_error"
            status = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
            with self.ledger._connect() as connection, self.ledger._transaction(connection):
                row = connection.execute(
                    "SELECT generation FROM executions WHERE id=?", (execution_id,)
                ).fetchone()
                if row["generation"] == generation:
                    connection.execute(
                        "UPDATE executions SET status=?,error=?,finished_at=? WHERE id=?",
                        (status, code, _now(), execution_id),
                    )
                    connection.execute(
                        "UPDATE stages SET status='failed',error=?,finished_at=? WHERE "
                        "execution_id=? AND name=? AND status='running'",
                        (code, _now(), execution_id, stage_name),
                    )
                    connection.execute(
                        "UPDATE stages SET status='blocked' WHERE execution_id=? AND "
                        "status='pending'",
                        (execution_id,),
                    )
                    self._event(connection, execution_id, generation, stage_name, status, code)
            if isinstance(exc, KeyboardInterrupt):
                raise
        return self.execution(execution_id)

    def _stage(
        self, execution_id: str, generation: int, stage: dict[str, Any], input_id: str
    ) -> None:
        name = stage["name"]
        with self.ledger._connect() as connection, self.ledger._transaction(connection):
            self._owned(connection, execution_id, generation)
            previous = connection.execute(
                "SELECT * FROM stages WHERE execution_id=? AND name=?", (execution_id, name)
            ).fetchone()
            if previous["status"] == "completed":
                return
            # A rejected output is a durable deterministic outcome, not a retryable effect.
            if previous["batch_id"]:
                raise IntakeError(
                    "quality_rejected",
                    "Stage output failed the quality gate; use a new definition and key",
                )
            connection.execute(
                "UPDATE stages SET "
                "status='running',attempts=attempts+1,started_at=?,finished_at=NULL "
                "WHERE execution_id=? AND name=?",
                (_now(), execution_id, name),
            )
            self._event(connection, execution_id, generation, name, "running")
        logger.info(
            canonical(
                {
                    "event": "stage_started",
                    "execution_id": execution_id,
                    "stage": name,
                    "generation": generation,
                }
            )
        )
        with self.ledger._connect() as connection, self.ledger._transaction(connection):
            self._owned(connection, execution_id, generation)

            def resolve(selector: str) -> str:
                if selector == "$input":
                    return input_id
                row = connection.execute(
                    "SELECT batch_id,status FROM stages WHERE execution_id=? AND name=?",
                    (execution_id, selector),
                ).fetchone()
                if row["status"] != "completed":
                    raise IntakeError(
                        "dependency_failed", "Stage dependency has no completed output"
                    )
                return str(row["batch_id"])

            parent_id = resolve(stage["input"])
            reference_ids = {key: resolve(value) for key, value in stage["references"].items()}
            batch = self._process(connection, stage, parent_id, reference_ids, execution_id)
            for reference in sorted(set(reference_ids.values())):
                connection.execute(
                    "INSERT OR IGNORE INTO batch_edges VALUES (?,?,'reference')",
                    (reference, batch["id"]),
                )
            status = "completed" if batch["status"] == "committed" else "failed"
            error = None if status == "completed" else "quality_rejected"
            connection.execute(
                "UPDATE stages SET status=?,batch_id=?,finished_at=?,error=? WHERE "
                "execution_id=? AND name=?",
                (status, batch["id"], _now(), error, execution_id, name),
            )
            self._event(connection, execution_id, generation, name, status, error)
        logger.info(
            canonical(
                {
                    "event": "stage_finished",
                    "execution_id": execution_id,
                    "batch_id": batch["id"],
                    "stage": name,
                    "status": status,
                    "error": error,
                }
            )
        )
        if error:
            raise IntakeError(error, "Stage output failed its quality gate")

    def _process(
        self,
        connection: sqlite3.Connection,
        stage: dict[str, Any],
        parent_id: str,
        references: dict[str, str],
        execution_id: str,
    ) -> dict[str, Any]:
        parent = self.ledger.batch(parent_id)
        contract = self.ledger._contract(stage["contract"]["name"], stage["contract"]["version"])
        if stage["operation"] == "replay":
            raw = [
                (row["line"], row["raw"])
                for row in connection.execute(
                    "SELECT line,raw FROM rows WHERE batch_id=? ORDER BY line", (parent_id,)
                )
            ]
            digest = parent["source_digest"]
            kind = "replay"
        else:
            values = self.ledger.export(parent_id)
            raw = [
                (index, canonical({key: value[key] for key in stage["fields"] if key in value}))
                for index, value in enumerate(values, 1)
            ]
            if not raw:
                raise IntakeError(
                    "empty_projection", "Projection requires at least one accepted row"
                )
            encoded = "\n".join(text for _, text in raw).encode("utf-8")
            if len(encoded) > MAX_INPUT_BYTES or any(
                len(text.encode("utf-8")) > MAX_ROW_BYTES for _, text in raw
            ):
                raise IntakeError("input_limit", "Projection exceeds a batch limit")
            digest = hashlib.sha256(encoded).hexdigest()
            kind = "derived"
        rows = _prepare(raw, contract)
        records = [parse_json(row.value) if row.value is not None else None for row in rows]
        reference_values = {
            key: self.ledger.export(batch_id) for key, batch_id in references.items()
        }
        issues = QualityRules.from_dict(stage["rules"]).validate(records, reference_values)
        rows = [
            PreparedRow(
                row.line,
                row.raw,
                row.digest,
                None if extra else row.value,
                canonical(parse_json(row.issues) + extra),
            )
            for row, extra in zip(rows, issues, strict=True)
        ]
        return self.ledger._write_batch(
            connection,
            f"pipeline:{execution_id}",
            stage["name"],
            contract,
            rows,
            digest,
            _threshold(stage["max_invalid"]),
            parent_id,
            kind=kind,
            execution_id=execution_id,
            stage=stage["name"],
        )
