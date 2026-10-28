# Changelog

## 0.2.3

- Added a minimal generated test lock constrained to the development lock, with
  drift and source-bundle checks. Fresh offline verification uses pre-downloaded
  wheels, no index/cache, and a Python socket guard for tests and child processes.
- Added separate wheel preparation/offline execution steps to the CI matrix.
- Rejected non-roundtrippable normalized thresholds before creating executions.

- Added an opt-in consumer quality gate with exact invalid fractions, minimum
  exportable rows, actionable JSON reasons and metadata events. Existing report-only
  quality calls and ingestion/export decisions remain compatible.
- Bound scientific threshold exponents before Fraction allocation to prevent small
  inputs from requesting huge integer powers.
- Added a real CLI/pipeline quality-gate demonstration to local verification and CI.

These entries describe real repository changes, not production deployments.

## 0.2.2 - 2026-10-27
- Native event fields, scoped JSON verbose CLI logging and metadata-only formatting
  with privacy, correlation and host-configuration regression tests.
- Source-package checks reject missing/changed dependency inputs, hash lock and
  security requirements, and report their SHA-256 digests.
- Explicit development setup, input-validation map and pipeline scope clarification.

## 0.2.1 - 2026-10-25
- Batch quality summaries and terminal execution diagnostics.
- Lock consistency, semantic CI guards, failure-safe verification evidence and
  isolated CI environments. Hosted and clean-source verification followed.

## 0.2.0 - 2026-10-24
- Durable declarative pipelines, quality rules, lineage, ordered backfill and
  generation-fenced manual recovery. Schema v2 upgrades recognized v1 ledgers.

## 0.1.0 - 2026-10-23
- Bounded JSONL intake, contracts, quarantine, quality gates, transactional SQLite
  persistence, replay and CLI.
