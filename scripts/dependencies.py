"""Inventory exact development packages from installed metadata."""

import importlib.metadata
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if metadata["project"]["dependencies"]:
        raise RuntimeError("Runtime dependency inventory needs review")
    packages = []
    for line in (ROOT / "requirements-dev.lock").read_text().splitlines():
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==(.+)", line)
        if not match:
            continue
        name, expected = match.groups()
        distribution = importlib.metadata.distribution(name)
        if distribution.version != expected:
            raise RuntimeError(f"Installed version differs from lock for {name}")
        licence = distribution.metadata.get("License-Expression")
        if not licence:
            licence = distribution.metadata.get("License", "unknown")
        packages.append(
            {"name": name, "version": expected, "license_metadata": licence, "redistributed": False}
        )
    result = {
        "runtime_packages": [],
        "development_packages": packages,
        "review_limit": "Installed metadata only; upstream files not audited",
    }
    (ROOT / "reports" / "DEPENDENCIES.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"runtime_packages": 0, "development_packages": len(packages)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
