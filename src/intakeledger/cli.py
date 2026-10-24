"""Machine-readable CLI. No network access or shell execution."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any, NoReturn

from .contracts import MAX_CONTRACT_BYTES, MAX_INPUT_BYTES, Contract, parse_json
from .errors import IntakeError
from .ledger import Ledger
from .pipeline import Pipeline, PipelineEngine

EXIT_CODES = {
    "idempotency_conflict": 3,
    "contract_conflict": 3,
    "database_busy": 4,
    "execution_busy": 4,
    "batch_rejected": 5,
}


def _read(path: str, limit: int) -> bytes:
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise IntakeError("input_limit", "Input file exceeds the byte limit")
    return data


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        print(
            json.dumps(
                {"error": {"code": "usage_error", "message": "Invalid arguments; run --help"}}
            ),
            file=sys.stderr,
        )
        raise SystemExit(2)


def parser() -> argparse.ArgumentParser:
    result = ArgumentParser(prog="intakeledger", description=__doc__)
    result.add_argument("--db", required=True, help="Local ledger database path")
    result.add_argument("--verbose", action="store_true", help="Log batch metadata to stderr")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Initialize or verify an existing ledger")
    register = commands.add_parser("register", help="Register an immutable contract version")
    register.add_argument("contract_file")
    ingest = commands.add_parser("ingest", help="Validate and record a JSONL feed")
    ingest.add_argument("input")
    ingest.add_argument("--source", required=True)
    replay = commands.add_parser("replay", help="Revalidate a complete recorded batch")
    replay.add_argument("batch_id")
    for child in (ingest, replay):
        child.add_argument("--key", required=True)
        child.add_argument("--contract", required=True, help="Registered contract name")
        child.add_argument("--version", required=True, type=int)
        child.add_argument("--max-invalid", default="0", help="Allowed invalid fraction, 0 to 1")
    for command in ("show", "rows", "export"):
        child = commands.add_parser(command)
        child.add_argument("batch_id")
        if command == "rows":
            child.add_argument("--include-payload", action="store_true")
    for command in ("pipeline", "backfill"):
        child = commands.add_parser(command)
        child.add_argument("definition")
        child.add_argument("batch_ids", nargs="+" if command == "backfill" else 1)
        child.add_argument("--key", required=True)
    for command in ("execution", "resume"):
        commands.add_parser(command).add_argument("execution_id")
    commands.add_parser("lineage").add_argument("batch_id")
    commands.add_parser("health")
    return result


def _run(args: argparse.Namespace) -> tuple[Any, int]:
    ledger = Ledger.initialize(args.db) if args.command == "init" else Ledger(args.db)
    if args.command == "init":
        return ledger.health(), 0
    if args.command == "register":
        try:
            text = _read(args.contract_file, MAX_CONTRACT_BYTES).decode("utf-8")
        except UnicodeError as exc:
            raise IntakeError("invalid_encoding", "Contract must contain UTF-8 text") from exc
        return ledger.register(Contract.from_dict(parse_json(text))), 0
    if args.command in ("ingest", "replay"):
        options = {
            "key": args.key,
            "contract_name": args.contract,
            "contract_version": args.version,
            "max_invalid": args.max_invalid,
        }
        if args.command == "ingest":
            batch = ledger.ingest(_read(args.input, MAX_INPUT_BYTES), source=args.source, **options)
        else:
            batch = ledger.replay(args.batch_id, **options)
        return batch, 5 if batch["status"] == "rejected" else 0
    if args.command in ("pipeline", "backfill", "execution", "resume"):
        engine = PipelineEngine(ledger)
        if args.command in ("pipeline", "backfill"):
            try:
                definition = _read(args.definition, MAX_CONTRACT_BYTES).decode("utf-8")
            except UnicodeError as exc:
                raise IntakeError("invalid_encoding", "Pipeline must contain UTF-8 text") from exc
            pipeline = Pipeline.from_dict(parse_json(definition))
            execution = (
                engine.run(pipeline, args.batch_ids[0], args.key)
                if args.command == "pipeline"
                else engine.backfill(pipeline, args.batch_ids, args.key)
            )
        else:
            execution = (
                engine.resume(args.execution_id)
                if args.command == "resume"
                else engine.execution(args.execution_id)
            )
        return execution, 0 if execution["status"] == "completed" else 5
    if args.command == "lineage":
        return ledger.lineage(args.batch_id), 0
    if args.command == "show":
        return ledger.batch(args.batch_id), 0
    if args.command == "rows":
        return ledger.rows(args.batch_id, include_payload=args.include_payload), 0
    if args.command == "export":
        return ledger.export(args.batch_id), 0
    if args.command == "health":
        health = ledger.health()
        return health, 0 if health["ok"] else 2
    raise AssertionError("argparse accepted an unknown command")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        result, code = _run(args)
        if args.command == "export":
            for row in result:
                print(json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":")))
        else:
            print(json.dumps(result, sort_keys=True, ensure_ascii=True))
        sys.stdout.flush()
        return code
    except IntakeError as exc:
        print(json.dumps({"error": {"code": exc.code, "message": str(exc)}}), file=sys.stderr)
        return EXIT_CODES.get(exc.code, 2)
    except BrokenPipeError:
        with suppress(BrokenPipeError):
            sys.stdout.close()
        return 0
    except OSError:
        print(
            json.dumps({"error": {"code": "io_error", "message": "File operation failed"}}),
            file=sys.stderr,
        )
        return 2
    except KeyboardInterrupt:
        return 130
