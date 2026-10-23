import os
from pathlib import Path

import pytest

from intakeledger import Contract, Ledger


@pytest.fixture
def contract():
    return Contract.from_dict(
        {
            "name": "shipments",
            "version": 1,
            "fields": {
                "event_id": {"type": "string", "min_length": 1},
                "units": {"type": "integer", "min": 0, "max": 1000},
            },
        }
    )


@pytest.fixture
def ledger(tmp_path, contract):
    value = Ledger.initialize(tmp_path / "ledger.db")
    value.register(contract)
    return value


@pytest.fixture
def cli_env():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    environment["PYTHONUTF8"] = "1"
    return environment
