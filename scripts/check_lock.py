"""Check direct constraints, build pins and SHA-256 integrity declarations offline."""

import re
import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]


def read_lock(path):
    locked = {}
    text = path.read_text(encoding="utf-8")
    for block in text.replace("\\\n", " ").splitlines():
        block = block.strip()
        if not block or block.startswith("#"):
            continue
        requirement_text, *hashes = block.split(" --hash=")
        requirement = Requirement(requirement_text.strip())
        specs = list(requirement.specifier)
        if len(specs) != 1 or specs[0].operator != "==" or "*" in specs[0].version:
            raise ValueError("Every lock entry must have one exact version")
        if not hashes or any(not re.fullmatch(r"sha256:[0-9a-f]{64}", h.strip()) for h in hashes):
            raise ValueError("Every lock entry must declare SHA-256 hashes")
        if requirement.marker and not requirement.marker.evaluate():
            continue
        name = canonicalize_name(requirement.name)
        if name in locked:
            raise ValueError("Duplicate active lock entry")
        locked[name] = (specs[0].version, frozenset(h.strip() for h in hashes))
    if not locked:
        raise ValueError("Lock must not be empty")
    return locked


def validate(root=ROOT):
    locked = {name: value[0] for name, value in read_lock(root / "requirements-dev.lock").items()}
    inputs = (root / "requirements-dev.in").read_text().splitlines()
    metadata = tomllib.loads((root / "pyproject.toml").read_text())
    for line in inputs + metadata["build-system"]["requires"]:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        requirement = Requirement(line)
        if requirement.marker and not requirement.marker.evaluate():
            continue
        version = locked.get(canonicalize_name(requirement.name))
        if version is None or version not in requirement.specifier:
            raise ValueError(f"Input/build constraint differs from lock: {requirement.name}")
    return len(locked)


def validate_test_lock(root=ROOT):
    development = read_lock(root / "requirements-dev.lock")
    tests = read_lock(root / "requirements-test.lock")
    if any(development.get(name) != entry for name, entry in tests.items()):
        raise ValueError("Test lock must use the development lock's versions and hashes")
    for line in (root / "requirements-test.in").read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        requirement = Requirement(line)
        if requirement.marker and not requirement.marker.evaluate():
            continue
        version = tests.get(canonicalize_name(requirement.name), (None,))[0]
        if version is None or version not in requirement.specifier:
            raise ValueError("Test input differs from test lock")
    return len(tests)


if __name__ == "__main__":
    print(f"Validated {validate()} active hash-locked packages against inputs and build pins")
    print(f"Validated {validate_test_lock()} active test packages as a consistent lock subset")
