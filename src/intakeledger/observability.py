"""Metadata-only events for library handlers and scoped CLI JSON logging."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from .contracts import canonical

EVENT_FIELDS = (
    "event",
    "at",
    "batch_id",
    "execution_id",
    "generation",
    "stage",
    "status",
    "error",
    "row_count",
)


def emit_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    payload = {key: value for key, value in fields.items() if key in EVENT_FIELDS}
    payload.update(event=event, at=datetime.now(UTC).isoformat())
    # Keep JSON messages usable with existing library handlers; extras support collectors.
    logger.info(canonical(payload), extra=payload)


class JsonFormatter(logging.Formatter):
    """Serialize only approved event metadata, never message or exception text."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {key: record.__dict__[key] for key in EVENT_FIELDS if key in record.__dict__}
        payload.setdefault("event", "unclassified")
        payload.setdefault("at", datetime.fromtimestamp(record.created, UTC).isoformat())
        payload.update(level=record.levelname, logger=record.name)
        return canonical(payload)


@contextmanager
def cli_logging(enabled: bool) -> Iterator[None]:
    """Own only a temporary namespace handler; leave embedding/root logging intact."""
    if not enabled:
        yield
        return
    namespace = logging.getLogger("intakeledger")
    level, propagate = namespace.level, namespace.propagate
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    namespace.addHandler(handler)
    namespace.setLevel(logging.INFO)
    namespace.propagate = False
    try:
        yield
    finally:
        namespace.removeHandler(handler)
        namespace.setLevel(level)
        namespace.propagate = propagate
        handler.close()
