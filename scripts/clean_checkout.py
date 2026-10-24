"""Verify an exported tracked HEAD in a new directory and a new hashed environment."""

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    records = []
    with tempfile.TemporaryDirectory(prefix="intakeledger-clean-") as directory:
        base = Path(directory)
        checkout = base / "checkout"
        checkout.mkdir()
        archive = base / "head.zip"
        subprocess.run(
            ["git", "archive", "HEAD", "--format=zip", "-o", str(archive)], cwd=ROOT, check=True
        )
        with zipfile.ZipFile(archive) as source:
            source.extractall(checkout)
        # No commits: initialize an index only for the repository heuristic's file inventory.
        subprocess.run(["git", "init", "--quiet"], cwd=checkout, check=True)
        subprocess.run(["git", "add", "."], cwd=checkout, check=True, capture_output=True)
        environment = base / "environment"
        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        commands = [
            (
                "hash_install",
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--require-hashes",
                    "-r",
                    "requirements-dev.lock",
                ],
            ),
            (
                "editable_install",
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--no-build-isolation",
                    "--no-deps",
                    "-e",
                    ".",
                ],
            ),
            ("verification", [str(python), "scripts/verify.py", "--security"]),
        ]
        for name, command in commands:
            result = subprocess.run(
                command,
                cwd=checkout,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=1200,
            )
            records.append(
                {
                    "check": name,
                    "exit_code": result.returncode,
                    "output_tail": (result.stdout + result.stderr)[-5000:],
                }
            )
            print(f"{name}: {result.returncode}", flush=True)
            if result.returncode:
                break
        verification_path = checkout / "reports/VERIFICATION.json"
        verification = (
            json.loads(verification_path.read_text()) if verification_path.is_file() else None
        )
        if len(records) == len(commands) and records[-1]["exit_code"] == 0:
            for name in ("VERIFICATION.json", "DEPENDENCIES.json", "BANDIT.json", "PIP_AUDIT.json"):
                (ROOT / "reports" / name).write_bytes((checkout / "reports" / name).read_bytes())
    passed = len(records) == len(commands) and all(item["exit_code"] == 0 for item in records)
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "revision": revision,
        "source": "git archive HEAD; excludes working-tree and ignored files",
        "all_passed": passed,
        "checks": records,
        "verification": verification,
    }
    (ROOT / "reports/CLEAN_CHECKOUT.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
