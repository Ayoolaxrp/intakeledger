"""Inventory exact development packages from installed metadata."""

import importlib.metadata
import json
import tomllib
from pathlib import Path

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]


def main():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if metadata["project"]["dependencies"]:
        raise RuntimeError("Runtime dependency inventory needs review")
    packages = []
    missing = []
    for line in (ROOT / "requirements-dev.lock").read_text().splitlines():
        if not line or line[0].isspace() or line.startswith("#"):
            continue
        requirement = Requirement(line.removesuffix("\\").strip())
        if requirement.marker and not requirement.marker.evaluate():
            continue
        name = requirement.name
        try:
            distribution = importlib.metadata.distribution(name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(name)
            continue
        if distribution.version not in requirement.specifier:
            raise RuntimeError(f"Installed version differs from lock for {name}")
        licence = distribution.metadata.get("License-Expression")
        if not licence:
            licence = distribution.metadata.get("License", "unknown")
        packages.append(
            {
                "name": name,
                "version": distribution.version,
                "license_metadata": licence,
                "redistributed": False,
            }
        )
    result = {
        "runtime_packages": [],
        "development_packages": packages,
        "missing": missing,
        "review_limit": "Installed metadata only; upstream files not audited",
    }
    (ROOT / "reports" / "DEPENDENCIES.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"runtime_packages": 0, "development_packages": len(packages), "missing": missing}
        )
    )
    return bool(missing)


if __name__ == "__main__":
    raise SystemExit(main())
