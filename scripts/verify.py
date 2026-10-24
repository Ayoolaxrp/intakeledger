"""Run release checks and record their actual exit codes."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--security", action="store_true")
    args = parser.parse_args()
    log_dir = ROOT / "reports" / "checks"
    log_dir.mkdir(parents=True, exist_ok=True)
    commands = [
        ("dependencies_inventory", ["scripts/dependencies.py"]),
        ("lint", ["-m", "ruff", "check", "src", "tests", "scripts"]),
        ("format", ["-m", "ruff", "format", "--check", "src", "tests", "scripts"]),
        ("types", ["-m", "mypy", "src"]),
        ("tests", ["-m", "coverage", "run", "-m", "pytest", "-q", "--tb=short"]),
        ("coverage", ["-m", "coverage", "report", "--fail-under=90"]),
        ("repository", ["scripts/check_repository.py"]),
        ("build", ["-m", "build", "--no-isolation"]),
        ("package", ["scripts/package_smoke.py"]),
        ("pipeline_demo", ["scripts/pipeline_demo.py"]),
        ("pip_check", ["-m", "pip", "check"]),
        ("ci_configuration", ["scripts/check_ci.py"]),
    ]
    if args.security:
        commands += [
            (
                "bandit",
                ["-m", "bandit", "-r", "src", "-q", "-f", "json", "-o", "reports/BANDIT.json"],
            ),
            (
                "dependencies",
                [
                    "-m",
                    "pip_audit",
                    "--disable-pip",
                    "--require-hashes",
                    "--format",
                    "json",
                    "--output",
                    "reports/PIP_AUDIT.json",
                    "-r",
                    "requirements-dev.lock",
                    "--progress-spinner",
                    "off",
                ],
            ),
        ]
    environment = os.environ.copy()
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONPATH"] = str(ROOT / "src")
    records = []
    for name, command in commands:
        result = subprocess.run(
            [sys.executable, *command],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        output = result.stdout + result.stderr
        (log_dir / f"{name}.txt").write_text(output, encoding="utf-8")
        records.append(
            {
                "check": name,
                "command": "python " + " ".join(command),
                "exit_code": result.returncode,
                "output_tail": output[-5000:],
            }
        )
        print(f"{name}: {'PASS' if result.returncode == 0 else 'FAIL'}", flush=True)
        if result.returncode:
            print(output[-5000:], flush=True)
            break
    versions = {}
    for name in ("pytest", "coverage", "ruff", "mypy", "build", "setuptools"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "unavailable"
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.system(),
        "sqlite": sqlite3.sqlite_version,
        "tools": versions,
        "checks": records,
        "security_requested": args.security,
        "all_requested_passed": len(records) == len(commands)
        and all(record["exit_code"] == 0 for record in records),
        "artifacts": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT / "dist").glob("*")
            if path.is_file()
        },
    }
    (ROOT / "reports" / "VERIFICATION.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if report["all_requested_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
