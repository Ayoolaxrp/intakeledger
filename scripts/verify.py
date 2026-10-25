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
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_check(command, environment):
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 124, "Check exceeded the 300 second timeout"
    except OSError:
        return 127, "Check process could not be started"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--security", action="store_true")
    args = parser.parse_args()
    log_dir = ROOT / "reports" / "checks"
    log_dir.mkdir(parents=True, exist_ok=True)
    commands = [
        ("lock_consistency", ["scripts/check_lock.py"]),
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
    # distutils interprets braces in temporary paths as variable substitutions.
    # Keep this host-specific workaround inside build/test child processes.
    if any(char in tempfile.gettempdir() for char in "{}"):
        environment["TEMP"] = str(ROOT.parent)
        environment["TMP"] = str(ROOT.parent)
    records = []
    for name, command in commands:
        returncode, output = run_check([sys.executable, *command], environment)
        (log_dir / f"{name}.txt").write_text(output, encoding="utf-8")
        records.append(
            {
                "check": name,
                "command": "python " + " ".join(command),
                "exit_code": returncode,
                "output_tail": output[-5000:],
            }
        )
        print(f"{name}: {'PASS' if returncode == 0 else 'FAIL'}", flush=True)
        if returncode:
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
