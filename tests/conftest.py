import os
import runpy
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
    source = str(Path(__file__).resolve().parents[1] / "src")
    environment["PYTHONPATH"] = os.pathsep.join([source, environment.get("PYTHONPATH", "")])
    environment["PYTHONUTF8"] = "1"
    return environment


@pytest.fixture(scope="session", autouse=True)
def offline_network():
    guard = Path(__file__).resolve().parent / "_offline"
    policy = runpy.run_path(str(guard / "sitecustomize.py"))
    with pytest.MonkeyPatch.context() as patch:
        for target, name in policy["TARGETS"]:
            patch.setattr(target, name, policy["deny_network"])
        patch.setenv("INTAKELEDGER_TEST_OFFLINE", "1")
        patch.setenv("PYTHONPATH", os.pathsep.join([str(guard), os.environ.get("PYTHONPATH", "")]))
        yield
