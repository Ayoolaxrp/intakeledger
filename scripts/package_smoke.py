"""Install the built wheel outside the checkout and run without site-packages."""

import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    wheel = next((ROOT / "dist").glob("intakeledger-*.whl"))
    archive = next((ROOT / "dist").glob("intakeledger-*.tar.gz"))
    with tempfile.TemporaryDirectory(prefix="intakeledger-package-") as directory:
        base = Path(directory)
        target = base / "installed"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                "--target",
                str(target),
                str(wheel),
            ],
            check=True,
            capture_output=True,
        )
        with tarfile.open(archive) as package:
            members = package.getnames()
            required = [
                "src/intakeledger/schema.sql",
                "tests/test_processes.py",
                "docs/ARCHITECTURE.md",
                "PROVENANCE.md",
            ]
            if any(not any(name.endswith(item) for name in members) for item in required):
                raise RuntimeError("Source archive is missing required review material")
            if any(".venv/" in name or name.endswith(".db") for name in members):
                raise RuntimeError("Source archive contains unwanted files")
            package.extractall(base / "source", filter="data")
        extracted = next((base / "source").iterdir())
        subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--no-isolation",
                "--wheel",
                str(extracted),
                "--outdir",
                str(base / "rebuilt"),
            ],
            check=True,
            capture_output=True,
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(target)
        environment["PYTHONUTF8"] = "1"
        script = """
import json
from intakeledger import Contract, Ledger
ledger = Ledger.initialize("installed.db")
ledger.register(Contract.from_dict({"name":"smoke","version":1,
                                   "fields":{"id":{"type":"integer"}}}))
batch = ledger.ingest(b'{"id":1}', source="package", key="one",
                      contract_name="smoke", contract_version=1)
if ledger.export(batch["id"]) != [{"id":1}]:
    raise RuntimeError("Installed export failed")
print(json.dumps(ledger.health()))
"""
        result = subprocess.run(
            [sys.executable, "-S", "-c", script],
            cwd=base,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        health = json.loads(result.stdout)
        if not health["ok"] or health["rows"] != 1:
            raise RuntimeError("Installed ledger health failed")
        cli = subprocess.run(
            [sys.executable, "-S", "-m", "intakeledger", "--db", "installed.db", "health"],
            cwd=base,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        if json.loads(cli.stdout) != health:
            raise RuntimeError("Installed CLI disagrees with library")
    print(
        json.dumps(
            {
                "wheel_install": "passed",
                "site_packages_disabled": True,
                "sdist_rebuild": "passed",
                "installed_workflow": "passed",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
