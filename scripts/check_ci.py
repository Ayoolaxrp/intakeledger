"""Validate local workflow contracts; this does not execute hosted GitHub Actions."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message="Invalid CI quality gate"):
    if not condition:
        raise ValueError(message)


def validate(workflow):
    require(workflow["permissions"] == {"contents": "read"})
    expected = {
        "Format": "python -m ruff format --check src tests scripts",
        "Lint": "python -m ruff check src tests scripts",
        "Types": "python -m mypy src",
        "Tests": "python -m coverage run -m pytest -q",
        "Coverage": "python -m coverage report --fail-under=90",
        "Lock consistency": "python scripts/check_lock.py",
        "Quality gate demo": "python scripts/quality_gate_demo.py",
        "Prepare test wheels": "python -m pip download --require-hashes --only-binary=:all: "
        "-r requirements-test.lock --dest .test-wheels",
        "Offline tests": "python scripts/offline_tests.py --wheelhouse .test-wheels",
    }
    steps = {step.get("name"): step for step in workflow["jobs"]["quality"]["steps"]}
    for name, command in expected.items():
        step = steps.get(name, {})
        require(step.get("run") == command, f"Missing or altered gate: {name}")
        require(not step.get("if") and step.get("continue-on-error", "false") == "false")
    for job in workflow["jobs"].values():
        require(not job.get("if"))
        require("permissions" not in job and job.get("continue-on-error", "false") == "false")
        for step in job["steps"]:
            require(not step.get("if") and step.get("continue-on-error", "false") == "false")
            if step.get("name") == "Install":
                require("--require-hashes -r requirements-dev.lock" in step.get("run", ""))
    security = {step.get("name"): step for step in workflow["jobs"]["security"]["steps"]}
    require(security.get("Bandit", {}).get("run") == "python -m bandit -r src -q")
    require(
        security.get("Audit", {}).get("run")
        == "python -m pip_audit --disable-pip --require-hashes "
        "-r requirements-dev.lock --progress-spinner off"
    )


def main():
    workflow = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    validate(workflow)
    names = set()
    for job in workflow["jobs"].values():
        require(int(job["timeout-minutes"]) <= 20)
        for step in job["steps"]:
            names.add(step.get("name"))
            if "uses" in step:
                require(re.fullmatch(r"[\w/-]+@[0-9a-f]{40}", step["uses"]))
            for path in re.findall(
                r"(?:scripts/[\w.]+\.py|requirements-[\w.]+)", step.get("run", "")
            ):
                require((ROOT / path).is_file(), path)
    require(
        {
            "Format",
            "Lint",
            "Types",
            "Tests",
            "Coverage",
            "Build",
            "Package",
            "Demo",
            "Audit",
        }
        <= names
    )
    updates = yaml.load((ROOT / ".github/dependabot.yml").read_text(), Loader=yaml.BaseLoader)
    require({item["package-ecosystem"] for item in updates["updates"]} == {"pip", "github-actions"})
    print("CI structure, local file references, permissions and pinned actions validated")


if __name__ == "__main__":
    main()
