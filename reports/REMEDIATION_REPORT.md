# IntakeLedger remediation — 2026-10-24

Status: implementation and baseline checks completed; final clean-source verification
and push are pending. This report will be finalized from actual execution results.

## Scope and evidence boundary

Restored public main at 9fd7a19 into a fresh local clone. The vanished workspace's
unpublished changes were not present remotely and were not claimed as recovered.
This session rebuilt the changes against the inspected 0.1 source. BASELINE.md
records the original 103 passing tests, passing static checks and build pin mismatch.

The DataFactor results (54.9 overall, 70 threshold and approximately 29 possible
additional points) were supplied by the owner. They are not an independently
verified rubric, a score forecast or a promise of an offer. Pipeline/data quality
gaps are real: original replay had parent links and row hashes but no execution DAG,
transformation stages, reusable cross-record rules or historical coordinator.
The original implementation already had strong transactions and process tests;
those were preserved rather than assuming the supplied category scores meant absence.

## Changes and traceability

| Original problem | Implementation and affected files | Added behaviour evidence |
| --- | --- | --- |
| No integrated pipeline model | pipeline.py, CLI, exports, PIPELINES.md, examples/pipeline.json | Dependency ordering, canonical definitions, invalid graphs, full CLI workflow |
| No persisted execution outcomes | migration_2.sql, pipeline.py | Stage attempts/timings, failure codes, events, active-run rejection |
| No atomic stage checkpoint or recovery | ledger.py internal batch writer, pipeline.py | SQL checkpoint failure rolls back output, KeyboardInterrupt, real process death, concurrent retries, stale generation fencing |
| Replay ancestry was only a parent pointer | migration_2.sql origins/typed edges, Ledger.lineage | Multi-hop hashes/parents, derived/reference ancestry, deterministic query, SQL cycle/update/FK rejection |
| Historical reprocessing not coordinated | PipelineEngine.backfill | 12-partition order, duplicate-input rejection, fail-fast recovery, unchanged completed child identities, changed manifest conflict |
| Row-only quality validation | quality.py reuses contracts and quarantine | Required/type checks, all-occurrence duplicates, reference integrity, grouped consistency, typed comparison rules, missing keys, safe issues |
| Schema changes needed safe deployment | Atomic v1-to-v2 migration using complete_statement | Preserved legacy batch/row/parent records, idempotent open, collision rollback; original future/unrelated DB tests retained |
| Lock lacked hashes and scanner transitives | requirements-dev.in/.lock, requirements-security.txt, dependency inventory | Universal hash resolution, clean isolated installs, active platform markers, pip check; zero runtime packages |
| Vulnerable original development pins | pytest 9.0.3, setuptools 84.1.0 and matching build pin | Actual before/after advisory JSON; no ignored advisories |
| CI grouped checks and no coverage gate | CI workflow, check_ci.py, Dependabot | Separate formatting/lint/types/tests/coverage/build/package steps, 90% branch-aware floor, YAML/path/SHA/permission validation |
| Package smoke could select stale artifacts | package_smoke.py exact version selection and installed pipeline | Wheel and source archive checks, bundled SQL, installed library/CLI with site-packages disabled |
| No reproducible integrated example | pipeline_demo.py, examples/pipeline.json | Real rejected ingest → replay → derived output → lineage → backfill → retry |
| Current-state documents were stale | README, architecture/spec/development/threat/limits, ADR 0002, provenance, third-party inventory, HANDOFF | Cross-checked against actual API; old audit explicitly marked historical |

All original tests remain. New tests use temporary SQLite databases and synthetic
records, with meaningful success and failure assertions. No artificial history,
contributors, production usage, benchmarks or endorsements were created.

## Commands actually executed so far

- `git clone https://github.com/Ayoolaxrp/intakeledger.git`, `git status --short`, `git log` and `git diff --check`.
- Original suite: `python -m coverage run -m pytest -q`: 103 passed in 40.67s.
- Expanded suite before final three additional regressions: 140 passed in 200.48s;
  combined statement/branch coverage 93% (875 statements, 380 branches).
- `python -m ruff check src tests scripts`, `python -m ruff format --check ...`
  and `python -m mypy src`: original checks passed; new-source lint and strict types passed.
- `uv pip compile requirements-dev.in --universal --python-version 3.11 --generate-hashes --output-file requirements-dev.lock`: succeeded, uv 0.12.0.
- `uv venv --seed` and `uv pip install --require-hashes -r requirements-dev.lock`
  into separate Python 3.11.15 and 3.13.15 environments: succeeded. Installation
  on 3.13 is not a complete application verification on that Python version.
- `python scripts/dependencies.py`: 43 active locked distributions, no runtime dependencies, no missing packages.
- `python -m pip check`: no broken requirements.
- `python scripts/check_ci.py`: passed local workflow structure/path/action/permission checks.
- `PYTHONPATH=src python scripts/pipeline_demo.py`: passed with 3 exported rows,
  2 backfill partitions, 8 total batches, 24 rows, healthy schema v2.
- Baseline `pip_audit --disable-pip --no-deps -r ORIGINAL_LOCK`: exit 1, 5 advisory
  entries across pytest/setuptools. Aliased entries are not five independent defects.
- New `pip_audit --disable-pip --no-deps --require-hashes -r requirements-dev.lock`:
  exit 0, no known vulnerabilities found at query time. JSON in PIP_AUDIT.json.
- `python -m bandit -r src -q -f json -o reports/BANDIT.json`: exit 0, no findings.

## Final release verification

Pending: verify the final committed source export in a newly created environment,
including complete tests, build, installed package and advisory checks. Record exact
revision and results in CLEAN_CHECKOUT.json and VERIFICATION.json. No hosted CI pass
or public push is claimed until independently observed.

## Remaining limits and commercial recommendation

Manual recovery, one local SQLite writer and bounded in-memory stages are deliberate.
No external sink, distributed scheduling, row-level projection mapping, signed audit
history, retention/pagination or automatic dead-worker detector exists. OS-level file
access is the security boundary. Operators must back up before migration and inspect
before takeover. No real customer data, services or credentials were used.

Linux, Python 3.12, hosted Actions, power loss, production load and external security
review remain unexecuted here. Dependency metadata is reviewed but is not a complete
file-level legal audit. Zero known advisory findings is not a security guarantee.
Project licence and rights to grant commercial licences still require owner review.

1. Technical value comes from atomic output/checkpoint semantics, explicit ancestry,
   reproducible quality decisions and recoverable ordered historical processing.
2. Specific failure invariants and real process/database tests distinguish this work
   from disconnected demonstrations; uniqueness or invention is not claimed.
3. Executed behaviour, types, coverage, package and scanner evidence support quality
   only within their tested environment and scope.
4. Contracts, DAG validation, SQLite migrations, recovery and lineage can be useful
   engineering data. Actual licensing-buyer demand remains unverified.
5. A small recent project has no production track record or organic maintenance
   history; generic validation/replay alternatives exist.
6. DataFactor's internal weighting, eligibility interpretation and fresh score remain
   unknown. The owner's report cannot establish a future offer.
7. Additional feature work has no current defensible return. Complete verification,
   authorized push, hosted CI and owner licensing review first.
8. After those gates, request a fresh evaluation rather than speculative expansion.
9. Cheapest next step is the hosted CI/evaluation feedback on this bounded improvement.
10. Specific independent failures, written buyer requirements or licensing restrictions
    would justify changing the recommendation. A projected score alone would not.

No DataFactor submission, agreement, deployment or licence grant has been performed.
