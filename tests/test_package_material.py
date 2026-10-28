import importlib.util
from pathlib import Path

import pytest

FILES = (
    "requirements-dev.in",
    "requirements-dev.lock",
    "requirements-security.txt",
    "requirements-test.in",
    "requirements-test.lock",
)


def checker():
    path = Path(__file__).resolve().parents[1] / "scripts/package_smoke.py"
    spec = importlib.util.spec_from_file_location("package_smoke", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify_dependency_bundle


def bundle(tmp_path):
    expected, extracted = tmp_path / "source", tmp_path / "release"
    expected.mkdir()
    extracted.mkdir()
    for name in FILES:
        data = f"# synthetic dependency material for {name}\n".encode()
        (expected / name).write_bytes(data)
        (extracted / name).write_bytes(data)
    return expected, extracted


def test_source_bundle_records_exact_dependency_material(tmp_path):
    expected, extracted = bundle(tmp_path)
    digests = checker()(extracted, expected)
    assert set(digests) == set(FILES)
    assert all(len(digest) == 64 for digest in digests.values())
    assert digests == checker()(extracted, expected)


@pytest.mark.parametrize("name", FILES)
@pytest.mark.parametrize("defect", ["missing", "changed"])
def test_source_bundle_rejects_missing_or_changed_locks(tmp_path, name, defect):
    expected, extracted = bundle(tmp_path)
    if defect == "missing":
        (extracted / name).unlink()
    else:
        (extracted / name).write_bytes(b"# synthetic altered release")
    with pytest.raises(RuntimeError, match="Source archive"):
        checker()(extracted, expected)
