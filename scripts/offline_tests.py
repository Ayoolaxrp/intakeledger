"""Test tracked HEAD in a new venv using only a pre-downloaded local wheelhouse."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def execute(wheelhouse, report):
    wheelhouse = Path(wheelhouse).resolve(strict=True)
    if not wheelhouse.is_dir():
        raise ValueError("Wheelhouse must be an existing directory")
    report["revision"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    with tempfile.TemporaryDirectory(prefix="intakeledger-offline-", dir=ROOT.parent) as directory:
        base = Path(directory)
        archive = base / "source.zip"
        subprocess.run(
            ["git", "archive", "HEAD", "--format=zip", "-o", str(archive)],
            cwd=ROOT,
            check=True,
            timeout=60,
        )
        checkout = base / "checkout"
        with zipfile.ZipFile(archive) as source:
            source.extractall(checkout)
        environment = os.environ.copy()
        environment.update(
            INTAKELEDGER_TEST_OFFLINE="1",
            PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
            PYTHONUTF8="1",
            PYTHONPATH=os.pathsep.join([str(checkout / "tests/_offline"), str(checkout / "src")]),
            TEMP=str(base),
            TMP=str(base),
            PIP_CONFIG_FILE=os.devnull,
        )
        venv = base / "environment"
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        commands = [
            ("venv", [sys.executable, "-m", "venv", str(venv)]),
            (
                "offline_hash_install",
                [
                    str(python),
                    "-m",
                    "pip",
                    "--isolated",
                    "--no-cache-dir",
                    "--disable-pip-version-check",
                    "install",
                    "--no-index",
                    "--find-links",
                    str(wheelhouse),
                    "--only-binary=:all:",
                    "--require-hashes",
                    "-r",
                    "requirements-test.lock",
                ],
            ),
            (
                "dependency_consistency",
                [str(python), "-m", "pip", "--disable-pip-version-check", "check"],
            ),
            ("offline_tests", [str(python), "-m", "pytest", "-q", "--tb=short"]),
        ]
        for name, command in commands:
            result = subprocess.run(
                command,
                cwd=checkout,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
            )
            report["checks"].append(
                {
                    "check": name,
                    "exit_code": result.returncode,
                    "output_tail": (result.stdout + result.stderr)[-4000:],
                }
            )
            print(f"{name}: {result.returncode}", flush=True)
            if result.returncode:
                print(report["checks"][-1]["output_tail"], flush=True)
                return
    report["all_passed"] = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheelhouse", required=True, help="Existing local dependency wheels")
    args = parser.parse_args()
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "all_passed": False,
        "checks": [],
        "source": "git archive HEAD; fresh venv; no index/cache; Python socket guard",
    }
    try:
        execute(args.wheelhouse, report)
    except (OSError, ValueError, subprocess.SubprocessError, KeyboardInterrupt) as exc:
        report["error"] = type(exc).__name__
    destination = ROOT / "reports/OFFLINE_TESTS.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
