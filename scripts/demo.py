"""Run the documented synthetic workflow in a disposable local database."""

import json
import tempfile
from pathlib import Path

from intakeledger import Contract, Ledger


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="intakeledger-demo-") as directory:
        ledger = Ledger.initialize(Path(directory) / "demo.db")
        for version in (1, 2):
            definition = json.loads((root / "examples" / f"shipments-v{version}.json").read_text())
            ledger.register(Contract.from_dict(definition))
        original = ledger.ingest(
            (root / "examples" / "shipments.jsonl").read_bytes(),
            source="synthetic",
            key="first",
            contract_name="shipments",
            contract_version=1,
        )
        if original["status"] != "rejected":
            raise RuntimeError("Version 1 should reject the synthetic return")
        replay = ledger.replay(
            original["id"],
            key="replay",
            contract_name="shipments",
            contract_version=2,
        )
        exported = ledger.export(replay["id"])
        if replay["status"] != "committed" or len(exported) != 3:
            raise RuntimeError("Version 2 should accept all three synthetic records")
        if ledger.batch(original["id"])["status"] != "rejected":
            raise RuntimeError("Replay changed the original batch")
        print(
            json.dumps(
                {
                    "original_status": original["status"],
                    "replay_status": replay["status"],
                    "accepted_rows": exported,
                    "health": ledger.health(),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
