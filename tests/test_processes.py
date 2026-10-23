import json
import sqlite3
import subprocess
import sys


def test_concurrent_process_retries_create_one_batch(ledger, cli_env):
    script = """
import sys
from intakeledger import Ledger
ledger = Ledger(sys.argv[1])
batch = ledger.ingest(b'{"event_id":"process-test","units":2}', source="processes",
                     key="same", contract_name="shipments", contract_version=1)
print(batch["id"])
"""
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(ledger.path)],
            env=cli_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(4)
    ]
    results = [process.communicate(timeout=30) for process in processes]
    assert all(process.returncode == 0 for process in processes), results
    assert len({stdout.strip() for stdout, _ in results}) == 1
    assert ledger.health()["batches"] == 1
    assert ledger.health()["rows"] == 1


def test_competing_different_keys_preserve_all_batches(ledger, cli_env):
    script = """
import sys
from intakeledger import Ledger
batch = Ledger(sys.argv[1]).ingest(b'{"event_id":"parallel","units":1}', source="processes",
                                  key=sys.argv[2], contract_name="shipments", contract_version=1)
print(batch["id"])
"""
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(ledger.path), str(i)],
            env=cli_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for i in range(4)
    ]
    results = [process.communicate(timeout=30) for process in processes]
    assert all(process.returncode == 0 for process in processes), results
    assert len({stdout.strip() for stdout, _ in results}) == 4
    assert ledger.health()["batches"] == 4


def test_process_death_during_actual_ingestion_recovers(ledger, cli_env):
    with sqlite3.connect(ledger.path) as connection:
        connection.execute("""CREATE TRIGGER terminate_writer BEFORE INSERT ON rows
                            WHEN NEW.line=2 BEGIN SELECT crash_writer(); END""")
    script = """
import os
import sys
from contextlib import contextmanager
from intakeledger import Ledger

class CrashLedger(Ledger):
    @contextmanager
    def _connect(self):
        with super()._connect() as connection:
            connection.create_function("crash_writer", 0, lambda: os._exit(87))
            yield connection

row = b'{"event_id":"crash-fixture","units":1}'
CrashLedger(sys.argv[1]).ingest(row + b"\\n" + row, source="crash", key="one",
                             contract_name="shipments", contract_version=1)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(ledger.path)],
        env=cli_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 87, result.stderr
    assert ledger.health()["batches"] == 0
    assert ledger.health()["rows"] == 0
    with sqlite3.connect(ledger.path) as connection:
        connection.execute("DROP TRIGGER terminate_writer")
    script = """
import json
import sys
from intakeledger import Ledger
batch = Ledger(sys.argv[1]).ingest(b'{"event_id":"recovered","units":1}', source="crash", key="one",
                                 contract_name="shipments", contract_version=1)
print(json.dumps(batch))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(ledger.path)],
        env=cli_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "committed"
