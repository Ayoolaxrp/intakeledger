# IntakeLedger remediation â€” 2026-10-24

Status: local remediation and final verification completed. All 14 release checks
passed on a clean tracked source export in a fresh environment. The authorized push
failed because Git could not obtain a valid password/token. Changes are committed
locally and are not claimed as published.

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
The supplied Test Coverage score of 62 is not directly comparable to our local
combined statement/branch metric: the original suite measured 93% locally. No raw
DataFactor coverage algorithm was available, so that discrepancy cannot be resolved
by asserting either metric is wrong. Dependency concerns were independently verified
by actual advisory findings against the old pins.
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
| No reproducible integrated example | pipeline_demo.py, examples/pipeline.json | Real rejected ingest â†’ replay â†’ derived output â†’ lineage â†’ backfill â†’ retry |
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

Verified revision: `4448785c13a96554343c2fa53b41d41bebbaab9b`. Subsequent changes
are audit evidence and handoff documentation. The fresh directory was exported by
`git archive HEAD`; its tracked source/configuration diff remained empty. A new
standard-library venv hash-installed the lock and editable-installed the package.
After interrupting the setup wrapper, the final verifier ran directly in that same
prepared directory/environment. CLEAN_CHECKOUT.json records that procedure explicitly;
it does not claim an uninterrupted wrapper run.

Command: `python scripts/verify.py --security`, Python 3.11.15 on Windows. All 14
checks returned zero; exact versions, commands, output summaries and artifact hashes
are in VERIFICATION.json. The corrected installation succeeded using a temporary path
without braces. The first failed installation remains in CLEAN_CHECKOUT_BEFORE.json.

| Check | Verified result |
| --- | --- |
| Locked dependency inventory | 43 active development distributions, no missing packages, zero third-party runtime dependencies |
| Ruff lint | Passed |
| Ruff formatting | Passed |
| Strict mypy | Passed, all 8 runtime source files |
| Full behaviour suite | 143 passed in 79.30s; all original 103 tests retained |
| Combined statement/branch coverage | 94%; 875 statements, 380 branches; enforced minimum 90% |
| Local repository heuristic | No findings; bounded pattern/AST check, not a comprehensive secret audit |
| Build | Wheel and source archive built |
| Installed-package verification | Wheel installed outside checkout; library and CLI ran with site-packages disabled; installed pipeline/lineage worked; source archive rebuilt |
| Real pipeline demonstration | Passed rejection, replay, projection, ancestry, retry and ordered backfill |
| pip dependency consistency | No broken requirements |
| CI configuration | YAML structure, file references, action SHAs, read-only permissions and Dependabot ecosystems passed local checks |
| Bandit | No findings, no suppressions |
| Dependency advisory audit | No known vulnerabilities in the hash lock at query time |

Critical exercised failure paths include malformed plans, schema-invalid and rejected
rows, referential violations, checkpoint rollback, migration rollback, KeyboardInterrupt,
real worker termination, explicit takeover fencing, concurrent retries, changed retry
identity and partial backfill recovery. Remaining uncovered paths include uncommon
CLI errors, defensive guards and module-entry coverage in subprocesses. No coverage
percentage is used to claim every error or platform has been tested.

The source audit, scans and final diff contain no known secrets or real input records.
Ownership and legal originality are assumptions for the owner to verify. Hosted CI,
Linux and Python 3.12 were not executed here. Do not convert local results into a
DataFactor category score.

Publication attempt: `git -c credential.interactive=never push origin main` returned
exit 1: `fatal: unable to get password from user`. A preceding dry run failed for
the same reason; `gh auth status` reported an invalid saved login. Fetch confirmed
remote main remained `9fd7a196090f0fd634770ee56138cedb5ed176ca` before the attempt.
No force push, authentication bypass or credential extraction was attempted.

From the owner's authenticated terminal, the remaining publication command is:

```powershell
git -C "C:\Users\User\Projects\intakeledger" push origin main
```

After publication, verify the remote SHA and hosted CI before requesting a fresh
evaluation. No external evaluation request has been sent by this session.

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

No DataFactor submission, agreement, deployment or licence grant has been performed by this session.

## Environmental failure found during final checks
A direct editable install from the clean source export failed: setuptools/distutils
interpreted the sandbox temporary path's `{GUID}` as a substitution variable. This
is a verified tooling/environment failure. The verifier now gives only child
processes an unbraced temporary path when necessary, and the clean helper creates
its disposable environment beside the checkout. No dependency warnings are suppressed.
The failed attempt is not counted as a successful installation. The corrected clean
installation and all 14 release checks subsequently passed independently.
