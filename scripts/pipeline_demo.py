"""Exercise real rejection, replay, projection, lineage, retries and historical backfill."""

import json
import tempfile
from pathlib import Path

from intakeledger import Contract, Ledger, Pipeline, PipelineEngine

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="intakeledger-pipeline-") as directory:
        ledger = Ledger.initialize(Path(directory) / "demo.db")
        for version in (1, 2):
            ledger.register(
                Contract.from_dict(
                    json.loads((ROOT / f"examples/shipments-v{version}.json").read_text())
                )
            )
        data = (ROOT / "examples/shipments.jsonl").read_bytes()
        inputs = [
            ledger.ingest(
                data,
                source="synthetic",
                key=f"day-{day}",
                contract_name="shipments",
                contract_version=1,
            )
            for day in (1, 2)
        ]
        assert all(batch["status"] == "rejected" for batch in inputs)
        pipeline = Pipeline.from_dict(json.loads((ROOT / "examples/pipeline.json").read_text()))
        engine = PipelineEngine(ledger)
        execution = engine.run(pipeline, inputs[0]["id"], "first")
        assert execution["status"] == "completed", execution
        output = execution["stages"][-1]["batch_id"]
        assert len(ledger.export(output)) == 3
        assert {node["kind"] for node in ledger.lineage(output)["nodes"]} == {
            "ingest",
            "replay",
            "derived",
        }
        assert engine.run(pipeline, inputs[0]["id"], "first") == execution
        backfill = engine.backfill(pipeline, [batch["id"] for batch in inputs], "history")
        assert backfill["status"] == "completed" and len(backfill["children"]) == 2
        assert engine.backfill(pipeline, [batch["id"] for batch in inputs], "history") == backfill
        assert ledger.batch(inputs[0]["id"]) == inputs[0]
        assert ledger.health()["ok"]
        print(
            json.dumps(
                {
                    "workflow": "passed",
                    "accepted_rows": ledger.export(output),
                    "backfill_partitions": len(backfill["children"]),
                    "health": ledger.health(),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
