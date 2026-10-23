"""A small local secret and package hygiene check, not a full secret-scanning service."""

import ast
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{50,}"),
    re.compile(r"AKIA[A-Z0-9]{16}"),
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{40,}"),
]


def candidates(root=ROOT):
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=True,
    )
    return [root / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def inspect_text(text):
    return any(pattern.search(text) for pattern in PATTERNS)


def main():
    findings = []
    paths = candidates()
    for path in paths:
        if path.suffix in {".db", ".pyc", ".whl"} or path.name == ".env":
            findings.append(
                {"path": str(path.relative_to(ROOT)), "rule": "generated_or_secret_file"}
            )
            continue
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            if inspect_text(text):
                findings.append({"path": str(path.relative_to(ROOT)), "rule": "credential_pattern"})
    for path in (ROOT / "src" / "intakeledger").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"eval", "exec", "compile"}
            ):
                findings.append({"path": str(path.relative_to(ROOT)), "rule": "code_execution"})
    print(json.dumps({"files_checked": len(paths), "findings": findings}, indent=2))
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
