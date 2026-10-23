# 0001. One SQLite ledger and a bounded batch
Status: accepted for this core. Date: 2026-10-23.

## Context
The project needs credible correctness work and independent local verification. Hosted infrastructure, brokers, and external connectors add setup and failure modes before they add useful behaviour.

## Decision
Use Python 3.11 and SQLite with a flat contract language, bounded feeds, atomic intake transactions, and full-batch replay. Use exact rational gate comparisons. Keep original bytes' digest and row hashes distinct.

No third-party runtime package is required. Validation is intentionally narrower than JSON Schema. Migration 1 is a bundled SQL resource, applied atomically only to an empty unidentified database.

## Alternatives and consequences
A schema library would add broader validation, but the small primitive-field language has a bounded, testable purpose. Do not quietly expand it into a competing general schema standard.

PostgreSQL would support more writers but require a running server. SQLite gives portable transaction and crash-recovery tests. One writer and local-filesystem restrictions are accepted.

Replaying quarantine alone would be smaller, but it could silently accept previously valid rows under a now stricter contract. Full replay makes every decision traceable to the child contract and reapplies the quality gate.

Record hashes do not authenticate an operator. A signed archive or externally witnessed log would be separate future work justified only by a concrete requirement.
