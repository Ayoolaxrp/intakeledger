# Publication and verification follow-up - 2026-10-26

The implementation and audit commits through **ef4100e** are now published on
GitHub main. `git ls-remote origin refs/heads/main` matched the full local revision.
The earlier statements below about these commits being unpublished or awaiting a
hosted matrix are historical and superseded by this section.

Independently queried the public GitHub API for run **40201420345**, event `push`,
at ef4100eba5823fffb0dc16444c91ef441e76c1b4. All four quality jobs
(Windows/Linux, Python 3.11/3.12) and the security job completed successfully.
Every reported step succeeded, including Windows 3.12 dependency consistency.
See HOSTED_CI_OBSERVATIONS.json and
https://github.com/Ayoolaxrp/intakeledger/actions/runs/40201420345.
The exact cause of the historical failed run remains unknown; the successful
replacement run is evidence of the current revision, not a retrospective diagnosis.

Updated README.md, docs/KNOWN_LIMITATIONS.md, EXTENDED_SCORE_AUDIT.md and the hosted
evidence to remove stale current-state uncertainty. No runtime code or public API
was changed. Repository heuristic and semantic CI checks passed; `git diff --check`
passed. The full existing verification result remains 158 tests and 94% coverage.

## Fresh clean-checkout proof

Executed `python scripts/clean_checkout.py` with the existing isolated Python 3.11
interpreter. It exported tracked **ef4100e** with `git archive HEAD`, initialized a
temporary index for the repository heuristic, created a new virtual environment,
hash-installed all 43 locked tooling distributions, installed the package editable
without build isolation or dependency resolution, then ran
`python scripts/verify.py --security`. All three stages exited **0**; the complete
helper exited **0**. CLEAN_CHECKOUT.json records `all_passed: true`, the source
revision and embedded actual results. VERIFICATION.json and the scanner/inventory
reports were refreshed from that clean run.

All **15** verification gates passed: lock consistency, dependency inventory,
formatting, linting, strict types, tests, coverage, repository hygiene, package build,
installed-package smoke, real pipeline demo, pip consistency, workflow contracts,
Bandit and pip-audit. **158 tests passed in 60.05s**, with **94%** combined
statement/branch coverage against the existing 90% floor. Wheel/source builds and
installed CLI/library/pipeline checks passed. Bandit reported no findings and
pip-audit reported no known vulnerabilities at query time. These are bounded
automated checks, not a comprehensive security audit or a performance benchmark.

This supersedes the earlier missing-0.2.1-clean-install limitation below. The export
excludes this follow-up's documentation/evidence edits; runtime code and lock pins
remain unchanged from the tested revision. Recommend using that published revision
for a fresh evaluation before funding speculative features. No evaluation was
submitted and no score increase is claimed.

No new DataFactor score or current category findings are verified. The newly
attached text had no readable content through the file reader, and its supported
download helper failed twice with a TLS transport error. Its findings have not
been assumed. Direct feedback text and the evaluated commit remain the next useful
inputs; speculative framework work is not justified by a score target alone.

---

# Extended remediation results - 2026-10-25

Current version: **0.2.1**. Implemented source revision: `985b71f6ebc13ed51fb3f4ba70b0e2410c5f9cf1`.
Pre-change audit: [EXTENDED_SCORE_AUDIT.md](EXTENDED_SCORE_AUDIT.md), initially
committed as 8935a48 before the engineering changes were committed. All 15 full
verification gates passed. The older report below is retained as historical evidence.

## Evaluation evidence boundary
The owner reports **64.3 overall**, with goals of 70 and 80+. The owner explicitly
chose to proceed without the latest category scores/findings or evaluated SHA.
All eight categories are audited; missing current evaluator facts are marked
unavailable, and historical scores are labelled historical. No uplift or score is
predicted. A framework migration is not justified by the observed requirements.

At inspection, public main and the clean local tree matched 1e81e2f. This supersedes
the old unpublished/authentication-failure handoff. This round's commits have not
been pushed, and no DataFactor resubmission, agreement, licence grant or deployment
was performed. Git history is genuine; no contributors or adoption were invented.

## Implemented tasks and evidence

| ID / original problem | Change and files | Added tests / verification |
| --- | --- | --- |
| A1: interrupted tool could leave stale green evidence | verify.py records launch/timeout failures; clean_checkout.py records failed setup and never consumes an unexecuted bundled verifier | Seed green JSON, inject timeout/launch failure, require fresh failed JSON and nonzero result |
| A2: direct manifest/build changes could drift from hash lock | check_lock.py checks exact active resolutions, hashes, duplicates, direct constraints and build pin; verifier and CI gate added | Missing hashes, wrong input/build pin and duplicate active package fail; actual 43-package lock passes |
| A3: CI guard used removable asserts and trusted step names | check_ci.py uses explicit errors, verifies commands, rejects skipped/allowed-failure/no-op gates and write permissions | Malformed fixtures fail; optimized Python also rejects a no-op gate; current YAML passes |
| A3 hosted finding: Windows 3.12 PR fails pip check | quality/security jobs now create isolated venvs using GITHUB_PATH before hash installation | YAML locally validated. Hosted resolution is unverified; exact failed dependency was not obtained |
| A4: missing safe terminal failure logs | pipeline.py logs UTC execution/stage context, generation, outcome and stable failure code | Inject sensitive exception text, verify correlated failure log omits values, recovery emits success |
| A5: no operational aggregate quality export | Ledger.quality_summary and CLI quality command count rows, issues and gate-blocked valid rows | Mixed rows, multiple issues per row, committed/rejected gate, safe CLI JSON, missing batch |
| A6: documentation and traceability | README, ARCHITECTURE, PIPELINES, DEVELOPMENT, KNOWN_LIMITATIONS, audit, handoff; version 0.2.1 | Commands and scope reviewed against implementation; all existing tests preserved |

The lockfile already contained universal transitive hashes. Its bytes and dependency
pins remain unchanged: validation strengthened an existing working lock rather than
creating competing lock formats or adding runtime dependencies. No new database
migration or service is needed; existing intake/replay interfaces remain.

## Commands and actual results

- `git fetch origin main` and `git rev-list --left-right --count origin/main...HEAD`:
  zero divergence at initial audit; no unrelated initial working changes.
- Narrow connected-email search for DataFactor/IntakeLedger: no matching report.
- `python -m pytest tests/test_audit_guards.py -q --tb=short`: **15 passed**.
- `python scripts/check_lock.py`: **43 active locked packages** match direct/build constraints.
- `python scripts/check_ci.py`: current workflow structure and semantic gates passed.
- `python -m ruff check src tests scripts` and format check: passed. Formatting
  failures during editing were fixed; they were not suppressed.
- `python scripts/verify.py --security`: **all 15 checks passed**, Windows/Python
  3.11.15. Exact tool versions, command tails and build hashes are in VERIFICATION.json.

| Final check | Actual outcome |
| --- | --- |
| Full suite | 158 passed in 163.00s; original 143 cases retained plus 15 new regression cases |
| Combined statement/branch coverage | 94%, 891 statements and 388 branches; 90% floor retained |
| Strict mypy | Passed, all 8 runtime modules |
| Lock / installed dependency inventory / pip check | Passed, 43 locked development distributions, zero runtime dependencies |
| Local repository heuristic | Passed; bounded working-tree check, not full-history/comprehensive secret scanning |
| Wheel and source archive | Built 0.2.1; exact-version installed package smoke passed |
| Installed library, CLI, pipeline and lineage | Passed with site-packages disabled; source archive rebuilt |
| Real pipeline demo | Passed |
| CI configuration | Passed locally, including the final isolated-environment YAML |
| Bandit | No findings |
| pip-audit | No known vulnerabilities found at query time |

A new network install/entire clean-checkout helper run was not repeated this round:
the dependency lock is unchanged. The full installed-wheel and clean extracted
source-archive tests did execute. Historical CLEAN_CHECKOUT/FINAL_PACKAGE evidence
remains dated to its own revision; it is not claimed as a new 0.2.1 clean checkout.

## Hosted evidence and unresolved issues
Public GitHub API data is recorded in HOSTED_CI_OBSERVATIONS.json. Run
https://github.com/Ayoolaxrp/intakeledger/actions/runs/40131231743 is a Dependabot
setup-python PR at e57b291, not this source revision. Its Windows 3.12 dependency
consistency step failed. Its other three matrix jobs and security job succeeded.
The exact failing package/cause is unknown. Environment isolation is a defensible
boundary improvement, not a verified cure; **the hosted matrix must be rerun**.

Remaining: latest DataFactor category breakdown/evaluated SHA, current hosted matrix,
strict memory/time quotas under worst-case rules, complete history secret scanning,
production load/power loss, external security review and owner rights/licensing review.
The local OS account remains the trust boundary; SQLite remains one writer with
explicit operator recovery. No invented production/benchmark evidence is substituted.

Recommendation: stop speculative feature work. Publish only under the owner's
applicable authorization, rerun hosted CI and investigate the actual Windows 3.12
log if it still fails. Obtain the latest category report and evaluated SHA, then
request a fresh evaluation when those evidence gates and owner rights review are
satisfactory. Do not budget against an assumed score or payment. Specific independent
failures or buyer requirements would justify further investment; a target alone does not.

---

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
