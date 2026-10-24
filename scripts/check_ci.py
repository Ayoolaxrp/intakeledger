"""Validate local workflow contracts; this does not execute hosted GitHub Actions."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    workflow = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    assert workflow["permissions"] == {"contents": "read"}
    names = set()
    for job in workflow["jobs"].values():
        assert int(job["timeout-minutes"]) <= 20
        for step in job["steps"]:
            names.add(step.get("name"))
            if "uses" in step:
                assert re.fullmatch(r"[\w/-]+@[0-9a-f]{40}", step["uses"])
            for path in re.findall(
                r"(?:scripts/[\w.]+\.py|requirements-[\w.]+)", step.get("run", "")
            ):
                assert (ROOT / path).is_file(), path
    assert {
        "Format",
        "Lint",
        "Types",
        "Tests",
        "Coverage",
        "Build",
        "Package",
        "Demo",
        "Audit",
    } <= names
    updates = yaml.load((ROOT / ".github/dependabot.yml").read_text(), Loader=yaml.BaseLoader)
    assert {item["package-ecosystem"] for item in updates["updates"]} == {"pip", "github-actions"}
    print("CI structure, local file references, permissions and pinned actions validated")


if __name__ == "__main__":
    main()
