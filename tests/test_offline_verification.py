import importlib.util
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("operation", ["dns", "tcp", "udp"])
def test_test_process_denies_network(operation):
    with pytest.raises(RuntimeError, match="Network access is disabled"):
        if operation == "dns":
            socket.getaddrinfo("example.invalid", 443)
        elif operation == "tcp":
            with socket.socket() as stream:
                stream.connect(("127.0.0.1", 9))
        else:
            with socket.socket(type=socket.SOCK_DGRAM) as stream:
                stream.sendto(b"synthetic", ("127.0.0.1", 9))


def test_child_python_inherits_network_denial(cli_env):
    result = subprocess.run(
        [sys.executable, "-c", "import socket; socket.create_connection(('127.0.0.1',9))"],
        env=cli_env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert "Network access is disabled" in result.stderr


def test_offline_setup_failure_replaces_stale_success(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "offline_tests", ROOT / "scripts/offline_tests.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "reports").mkdir()
    result = tmp_path / "reports/OFFLINE_TESTS.json"
    result.write_text('{"all_passed":true}')
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["offline_tests.py", "--wheelhouse", str(tmp_path / "missing")]
    )
    assert module.main() == 1
    report = json.loads(result.read_text())
    assert report["all_passed"] is False and report["checks"] == []
    assert report["error"] == "FileNotFoundError"


@pytest.mark.parametrize("defect", ["pin", "hash", "input", "missing"])
def test_test_lock_rejects_divergence_from_development(tmp_path, defect):
    spec = importlib.util.spec_from_file_location("test_lock", ROOT / "scripts/check_lock.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.validate_test_lock(ROOT) > 0
    for name in ("requirements-dev.lock", "requirements-test.lock", "requirements-test.in"):
        (tmp_path / name).write_bytes((ROOT / name).read_bytes())
    lock = tmp_path / "requirements-test.lock"
    text = lock.read_text()
    if defect == "pin":
        text = text.replace("pytest==9.0.3", "pytest==0.0.1")
    elif defect == "hash":
        import re

        text = re.sub(r"sha256:[0-9a-f]{64}", "sha256:" + "0" * 64, text)
    elif defect == "input":
        (tmp_path / "requirements-test.in").write_text("pytest==0.0.1")
    else:
        text = text.replace("pytest==9.0.3", "missing-package==9.0.3")
    lock.write_text(text)
    with pytest.raises(ValueError):
        module.validate_test_lock(tmp_path)


@pytest.mark.parametrize("name", ["Offline tests", "Prepare test wheels"])
def test_ci_requires_offline_setup_and_execution(name):
    import yaml

    spec = importlib.util.spec_from_file_location("offline_ci", ROOT / "scripts/check_ci.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    workflow = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    step = next(step for step in workflow["jobs"]["quality"]["steps"] if step.get("name") == name)
    step["run"] = "echo skipped"
    with pytest.raises(ValueError, match=name):
        module.validate(workflow)
