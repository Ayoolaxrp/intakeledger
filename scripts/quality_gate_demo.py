"""Exercise consumer gating and pipeline replay through the real CLI and SQLite."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from intakeledger import Contract, Ledger, Pipeline, PipelineEngine


def main():
    with tempfile.TemporaryDirectory(prefix="intakeledger-gate-") as directory:
        ledger = Ledger.initialize(Path(directory) / "demo.db")
        ledger.register(
            Contract.from_dict(
                {"name": "demo", "version": 1, "fields": {"id": {"type": "integer"}}}
            )
        )
        batch = ledger.ingest(
            b'{"id":1}\n{"id":"invalid"}',
            source="synthetic",
            key="mixed",
            contract_name="demo",
            contract_version=1,
            max_invalid="1/2",
        )
        pipeline = Pipeline.from_dict(
            {
                "name": "demo",
                "version": 1,
                "stages": [
                    {
                        "name": "validate",
                        "operation": "replay",
                        "contract": {"name": "demo", "version": 1},
                        "max_invalid": "1/2",
                    }
                ],
            }
        )
        engine = PipelineEngine(ledger)
        execution = engine.run(pipeline, batch["id"], "once")
        output = execution["stages"][0]["batch_id"]
        for threshold, expected in [("0", 5), ("1/2", 0)]:
            process = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "intakeledger",
                    "--db",
                    str(ledger.path),
                    "quality",
                    output,
                    "--fail-on-threshold",
                    "--max-invalid",
                    threshold,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if process.returncode != expected:
                raise RuntimeError("Quality gate CLI returned an unexpected exit code")
            report = json.loads(process.stdout)
            if report["gate"]["passed"] != (expected == 0) or report["exportable_rows"] != 1:
                raise RuntimeError("Quality gate did not enforce the requested policy")
        if engine.run(pipeline, batch["id"], "once") != execution:
            raise RuntimeError("Gate observation changed execution retry identity")
        if len(ledger.lineage(output)["nodes"]) != 2 or ledger.export(output) != [{"id": 1}]:
            raise RuntimeError("Gate observation changed lineage or export")
    print(json.dumps({"quality_gate_demo": "passed", "strict_exit": 5, "boundary_exit": 0}))


if __name__ == "__main__":
    main()
