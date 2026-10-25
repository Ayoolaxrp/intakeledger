"""SQLite transactions are the sole writer coordination mechanism."""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from fractions import Fraction
from importlib.resources import files
from pathlib import Path
from typing import Any

from .contracts import (
    MAX_INPUT_BYTES,
    MAX_ROW_BYTES,
    MAX_ROWS,
    NAME,
    Contract,
    canonical,
    parse_json,
)
from .errors import IntakeError

APPLICATION_ID = 0x494C4447
SCHEMA_VERSION = 2
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreparedRow:
    line: int
    raw: str
    digest: str
    value: str | None
    issues: str


def _label(value: str) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 200:
        raise IntakeError("invalid_label", "Source and key must contain 1 to 200 characters")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise IntakeError("invalid_label", "Source and key must not contain control characters")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise IntakeError("invalid_label", "Source and key must be valid UTF-8") from exc


def _threshold(value: str) -> Fraction:
    try:
        if not isinstance(value, str) or len(value) > 32:
            raise ValueError
        result = Fraction(value)
        if not 0 <= result <= 1:
            raise ValueError
        return result
    except (ValueError, ZeroDivisionError) as exc:
        raise IntakeError(
            "invalid_threshold", "Invalid fraction must be between zero and one"
        ) from exc


def _prepare(raw_lines: list[tuple[int, str]], contract: Contract) -> list[PreparedRow]:
    result = []
    for line, raw in raw_lines:
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        try:
            value = parse_json(raw)
            issues = contract.validate(value)
        except IntakeError:
            value = None
            issues = [{"field": "$", "code": "invalid_json"}]
        result.append(
            PreparedRow(
                line, raw, digest, canonical(value) if not issues else None, canonical(issues)
            )
        )
    return result


class Ledger:
    """Open a local ledger. Use create=True only for explicit initialization."""

    def __init__(self, path: str | Path, *, create: bool = False, timeout: float = 5.0) -> None:
        if type(timeout) not in (float, int) or not 0 <= timeout <= 30:
            raise IntakeError(
                "invalid_timeout", "Database timeout must be between 0 and 30 seconds"
            )
        self.path = Path(path).resolve()
        self.timeout = timeout
        if create:
            try:
                with self.path.open("xb"):
                    pass
            except FileExistsError:
                pass
        if not create and not self.path.is_file():
            raise IntakeError("not_initialized", "Initialize the ledger before using it")
        with self._connect() as connection, self._transaction(connection):
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            app_id = connection.execute("PRAGMA application_id").fetchone()[0]
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE name NOT GLOB 'sqlite_*'"
            ).fetchall()
            if version == 0 and app_id == 0 and not tables and create:
                schema = files("intakeledger").joinpath("schema.sql").read_text(encoding="utf-8")
                self._schema(connection, schema)
                self._schema(
                    connection,
                    files("intakeledger").joinpath("migration_2.sql").read_text(encoding="utf-8"),
                )
                connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            elif version == 1 and app_id == APPLICATION_ID:
                self._schema(
                    connection,
                    files("intakeledger").joinpath("migration_2.sql").read_text(encoding="utf-8"),
                )
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            elif version != SCHEMA_VERSION or app_id != APPLICATION_ID:
                raise IntakeError("incompatible_database", "Unrecognized ledger or schema version")

    @staticmethod
    def _schema(connection: sqlite3.Connection, script: str) -> None:
        # executescript implicitly commits; complete_statement keeps migrations atomic.
        statement = ""
        for line in script.splitlines(keepends=True):
            statement += line
            if sqlite3.complete_statement(statement):
                connection.execute(statement)
                statement = ""
        if statement.strip():
            raise IntakeError("invalid_migration", "Incomplete schema statement")

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = None
        try:
            connection = sqlite3.connect(
                self.path.as_uri() + "?mode=rw",
                uri=True,
                timeout=self.timeout,
                isolation_level=None,
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA synchronous = FULL")
            yield connection
        except sqlite3.Error as exc:
            if getattr(exc, "sqlite_errorcode", 0) & 255 in (
                sqlite3.SQLITE_BUSY,
                sqlite3.SQLITE_LOCKED,
            ):
                raise IntakeError(
                    "database_busy", "Ledger is busy; retry the same request"
                ) from exc
            raise IntakeError("database_error", "Database operation failed") from exc
        finally:
            if connection is not None:
                connection.close()

    @contextmanager
    def _transaction(self, connection: sqlite3.Connection) -> Iterator[None]:
        connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise

    @classmethod
    def initialize(cls, path: str | Path) -> Ledger:
        return cls(path, create=True)

    def register(self, contract: Contract) -> dict[str, Any]:
        contract = Contract.from_dict(contract.as_dict())
        with self._connect() as connection, self._transaction(connection):
            existing = connection.execute(
                "SELECT digest FROM contracts WHERE name=? AND version=?",
                (contract.name, contract.version),
            ).fetchone()
            if existing and existing["digest"] != contract.digest:
                raise IntakeError("contract_conflict", "Contract versions cannot be overwritten")
            connection.execute(
                "INSERT OR IGNORE INTO contracts VALUES (?, ?, ?, ?)",
                (contract.name, contract.version, contract.digest, contract.to_json()),
            )
        return {"name": contract.name, "version": contract.version, "digest": contract.digest}

    def _contract(self, name: str, version: int) -> Contract:
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise IntakeError("invalid_contract", "Invalid contract name")
        if type(version) is not int or not 1 <= version <= 2**31 - 1:
            raise IntakeError("invalid_contract", "Invalid contract version")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT definition FROM contracts WHERE name=? AND version=?", (name, version)
            ).fetchone()
        if row is None:
            raise IntakeError("contract_not_found", "Contract version does not exist")
        return Contract.from_dict(parse_json(row["definition"]))

    def ingest(
        self,
        data: bytes,
        *,
        source: str,
        key: str,
        contract_name: str,
        contract_version: int,
        max_invalid: str = "0",
    ) -> dict[str, Any]:
        _label(source)
        _label(key)
        threshold = _threshold(max_invalid)
        if type(data) is not bytes or len(data) > MAX_INPUT_BYTES:
            raise IntakeError("input_limit", "Feed exceeds the input byte limit")
        if not data:
            raise IntakeError("empty_input", "Feed must contain at least one row")
        parts = data.split(b"\n")
        if parts[-1] == b"":
            parts.pop()
        if len(parts) > MAX_ROWS:
            raise IntakeError("row_limit", "Feed exceeds the row count limit")
        raw_lines = []
        for line, part in enumerate(parts, 1):
            part = part.removesuffix(b"\r")
            if len(part) > MAX_ROW_BYTES:
                raise IntakeError("row_size_limit", "Feed row exceeds the byte limit")
            try:
                raw_lines.append((line, part.decode("utf-8")))
            except UnicodeError as exc:
                raise IntakeError("invalid_encoding", "Feed must contain UTF-8 text") from exc
        contract = self._contract(contract_name, contract_version)
        rows = _prepare(raw_lines, contract)
        return self._commit(
            source, key, contract, rows, hashlib.sha256(data).hexdigest(), threshold, None
        )

    def _commit(
        self,
        source: str,
        key: str,
        contract: Contract,
        rows: list[PreparedRow],
        source_digest: str,
        threshold: Fraction,
        parent: str | None,
    ) -> dict[str, Any]:
        with self._connect() as connection, self._transaction(connection):
            result = self._write_batch(
                connection, source, key, contract, rows, source_digest, threshold, parent
            )
        logger.info(
            canonical(
                {
                    "event": "batch_recorded",
                    "batch_id": result["id"],
                    "row_count": result["row_count"],
                    "status": result["status"],
                }
            )
        )
        return result

    def _write_batch(
        self,
        connection: sqlite3.Connection,
        source: str,
        key: str,
        contract: Contract,
        rows: list[PreparedRow],
        source_digest: str,
        threshold: Fraction,
        parent: str | None,
        *,
        kind: str | None = None,
        execution_id: str | None = None,
        stage: str | None = None,
    ) -> dict[str, Any]:
        request_digest = hashlib.sha256(
            canonical(
                {
                    "source_digest": source_digest,
                    "contract_digest": contract.digest,
                    "threshold": str(threshold),
                    "parent": parent,
                }
            ).encode("utf-8")
        ).hexdigest()
        previous = connection.execute(
            "SELECT * FROM batches WHERE source=? AND idempotency_key=?", (source, key)
        ).fetchone()
        if previous:
            if previous["request_digest"] != request_digest:
                raise IntakeError("idempotency_conflict", "Key was used for a different request")
            return dict(previous)
        valid = sum(row.value is not None for row in rows)
        status = "committed" if Fraction(len(rows) - valid, len(rows)) <= threshold else "rejected"
        batch_id = uuid.uuid4().hex
        connection.execute(
            "INSERT INTO batches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                batch_id,
                source,
                key,
                request_digest,
                source_digest,
                contract.name,
                contract.version,
                parent,
                str(threshold),
                status,
                len(rows),
                valid,
                datetime.now(UTC).isoformat(),
            ),
        )
        connection.executemany(
            "INSERT INTO rows VALUES (?, ?, ?, ?, ?, ?)",
            ((batch_id, row.line, row.raw, row.digest, row.value, row.issues) for row in rows),
        )
        connection.execute(
            "INSERT INTO batch_origins VALUES (?, ?, ?, ?)",
            (batch_id, kind or ("replay" if parent else "ingest"), execution_id, stage),
        )
        if parent:
            connection.execute(
                "INSERT INTO batch_edges VALUES (?, ?, ?)", (parent, batch_id, kind or "replay")
            )
        result = dict(
            connection.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
        )
        return result

    def replay(
        self,
        parent_id: str,
        *,
        key: str,
        contract_name: str,
        contract_version: int,
        max_invalid: str = "0",
    ) -> dict[str, Any]:
        _label(key)
        threshold = _threshold(max_invalid)
        parent = self.batch(parent_id)
        contract = self._contract(contract_name, contract_version)
        with self._connect() as connection:
            raw_lines = [
                (row["line"], row["raw"])
                for row in connection.execute(
                    "SELECT line, raw FROM rows WHERE batch_id=? ORDER BY line", (parent_id,)
                )
            ]
        return self._commit(
            parent["source"],
            key,
            contract,
            _prepare(raw_lines, contract),
            parent["source_digest"],
            threshold,
            parent_id,
        )

    def batch(self, batch_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
        if row is None:
            raise IntakeError("batch_not_found", "Batch does not exist")
        return dict(row)

    def rows(self, batch_id: str, *, include_payload: bool = False) -> list[dict[str, Any]]:
        batch = self.batch(batch_id)
        with self._connect() as connection:
            result = []
            for row in connection.execute(
                "SELECT * FROM rows WHERE batch_id=? ORDER BY line", (batch_id,)
            ):
                entry = {
                    "line": row["line"],
                    "row_digest": row["digest"],
                    "issues": json.loads(row["issues"]),
                    "exportable": batch["status"] == "committed" and row["value"] is not None,
                    "batch_id": batch_id,
                    "parent_id": batch["parent_id"],
                    "source_digest": batch["source_digest"],
                    "contract_name": batch["contract_name"],
                    "contract_version": batch["contract_version"],
                }
                if include_payload:
                    entry["raw"] = row["raw"]
                result.append(entry)
        return result

    def export(self, batch_id: str) -> list[dict[str, Any]]:
        batch = self.batch(batch_id)
        if batch["status"] != "committed":
            raise IntakeError("batch_rejected", "Quality gate blocks export of this batch")
        with self._connect() as connection:
            return [
                json.loads(row["value"])
                for row in connection.execute(
                    "SELECT value FROM rows WHERE batch_id=? AND value IS NOT NULL ORDER BY line",
                    (batch_id,),
                )
            ]

    def health(self) -> dict[str, Any]:
        with self._connect() as connection:
            integrity = connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
            references = not connection.execute("PRAGMA foreign_key_check").fetchall()
            return {
                "ok": integrity and references,
                "schema_version": SCHEMA_VERSION,
                "execution_states": {
                    row["status"]: row["n"]
                    for row in connection.execute(
                        "SELECT status, COUNT(*) AS n FROM executions "
                        "GROUP BY status ORDER BY status"
                    )
                },
                "batches": connection.execute("SELECT COUNT(*) FROM batches").fetchone()[0],
                "rows": connection.execute("SELECT COUNT(*) FROM rows").fetchone()[0],
            }

    def lineage(self, batch_id: str) -> dict[str, Any]:
        self.batch(batch_id)
        with self._connect() as connection:
            nodes = [
                dict(row)
                for row in connection.execute(
                    """
                WITH RECURSIVE ancestors(id) AS (
                    SELECT ? UNION SELECT parent_id FROM batch_edges
                    JOIN ancestors ON child_id=ancestors.id
                ) SELECT b.id, b.parent_id, b.source_digest, o.kind, o.execution_id, o.stage
                FROM ancestors a JOIN batches b ON b.id=a.id
                JOIN batch_origins o ON o.batch_id=b.id ORDER BY b.id
                """,
                    (batch_id,),
                )
            ]
            edges = [
                dict(row)
                for row in connection.execute(
                    """
                WITH RECURSIVE ancestors(id) AS (
                    SELECT ? UNION SELECT parent_id FROM batch_edges
                    JOIN ancestors ON child_id=ancestors.id
                ) SELECT e.* FROM batch_edges e JOIN ancestors a ON e.child_id=a.id
                ORDER BY e.parent_id,e.child_id,e.kind
            """,
                    (batch_id,),
                )
            ]
        return {"batch_id": batch_id, "nodes": nodes, "edges": edges}

    def quality_summary(self, batch_id: str) -> dict[str, Any]:
        """Count rows separately from issues; rejected batches block every valid row."""
        with self._connect() as connection:
            batch = connection.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
            if batch is None:
                raise IntakeError("batch_not_found", "Batch does not exist")
            counts: dict[str, int] = {}
            for row in connection.execute(
                "SELECT issues FROM rows WHERE batch_id=? ORDER BY line", (batch_id,)
            ):
                for issue in json.loads(row["issues"]):
                    code = issue["code"]
                    counts[code] = counts.get(code, 0) + 1
            valid = batch["valid_count"]
            return {
                "batch_id": batch_id,
                "status": batch["status"],
                "total_rows": batch["row_count"],
                "valid_rows": valid,
                "quarantined_rows": batch["row_count"] - valid,
                "exportable_rows": valid if batch["status"] == "committed" else 0,
                "blocked_valid_rows": valid if batch["status"] == "rejected" else 0,
                "issue_counts": dict(sorted(counts.items())),
            }
