"""Regenerate the universal pip-compatible hash lock using uv 0.12.0."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    version = subprocess.check_output(["uv", "--version"], text=True).strip()
    if version.split()[:2] != ["uv", "0.12.0"]:
        raise RuntimeError("Use uv 0.12.0 to regenerate this lock")
    subprocess.run(
        [
            "uv",
            "pip",
            "compile",
            "requirements-dev.in",
            "--universal",
            "--python-version",
            "3.11",
            "--generate-hashes",
            "--output-file",
            "requirements-dev.lock",
        ],
        cwd=ROOT,
        check=True,
    )

    subprocess.run(
        [
            "uv",
            "pip",
            "compile",
            "requirements-test.in",
            "--constraint",
            "requirements-dev.lock",
            "--universal",
            "--python-version",
            "3.11",
            "--generate-hashes",
            "--output-file",
            "requirements-test.lock",
        ],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
