# Extended IntakeLedger audit

Checked 2026-10-25, before this round's implementation. Source: local and public
`1e81e2f`; clean working tree; fetch showed zero divergence. The owner reports a
new overall score of **64.3**, a milestone of 70 and an aspiration of 80+. These
are goals, not predictions. The owner elected to proceed without the latest
category breakdown. Neither that report nor its evaluated SHA was supplied or
found in the repository or the narrowly scoped connected-email search.

Consequently, every **current category score and latest evaluator weakness is
unavailable**. The older owner-provided 54.9 evaluation is historical evidence
only. No quotation, framework recommendation or current category number is
attributed to the latest evaluator. Matching the evaluated SHA and obtaining the
actual report are prerequisites to resolving evaluator-specific disagreements.

## Method and evidence

Inspected runtime contracts/ledger/pipeline/quality/CLI/schema, tests, packaging,
dependency inputs/hash lock, verification and CI scripts, workflow, threat model,
architecture/ADRs, README, provenance, handoff and prior audit evidence. Earlier
executed evidence records 143 tests and 94% combined statement/branch coverage;
these are local metrics, not DataFactor's coverage calculation. A new full verifier
was started before edits; its live process was unavailable after the intervening
turn, so final results will be independently rerun, not inferred from that process.

## Category findings

Each section records score/source, evaluator evidence, current condition, additional
weaknesses, improvements, estimated cost, verification, dependencies and decision.
Costs are rough engineering-hour estimates for focused work, not billing promises.

### Pipeline & Data Quality

- Current score/latest observations: **unavailable**. Historical score: 15 in the
  older 54.9 report; its detailed findings were not supplied.
- Current evidence: pipeline.py interprets bounded dependency graphs, deterministic
  stage ordering, persisted attempts/outcomes, replay/projection, reference inputs
  and ordered backfill. quality.py provides duplicates, references, group consistency
  and business comparisons; contracts supply schema/required/type checks. Tests cover
  rejection, lineage, retries, rollback, process death and backfill recovery.
- Staleness check: any claim that the current code lacks these capabilities would
  conflict with implementation and tests. We cannot assert the latest report made it.
- Additional gap: row diagnostics exist, but no concise batch quality summary counts
  accepted/quarantined/exportable/blocked rows and issue codes for operations/export.
- Improvement: add a payload-free aggregate quality query and CLI, retaining exact
  threshold and whole-batch rejection semantics. Cost 0.5–1.5h. Evidence: mixed rows,
  rejected gate, multiple issues per row, empty accepted export, retry consistency and
  CLI tests. Depends on existing ledger rows, not a new validation framework.
- Decision: **pursue** the summary; retain the working pipeline. Defer joins, external
  orchestration, connectors and global deduplication without a concrete use case.

### Architecture & Robustness

- Current score/latest observations: **unavailable**; historical score 70.
- Current evidence: one SQLite writer, output/checkpoint/lineage in one transaction,
  generation fencing, explicit recovery, atomic v1 migration, immutable contracts,
  bounded input and fail-fast backfill. Failure tests support these boundaries.
- Additional gap: verification scripts can exit via TimeoutExpired/OSError before
  replacing an earlier green VERIFICATION.json; this makes release evidence stale.
  clean_checkout.py can also read a bundled old verification report after setup fails.
- Improvement: record launch/timeout failures as failing checks, replace old evidence
  and make clean-checkout evidence consume only a verifier actually executed this run.
  Cost 0.5–1.5h. Evidence: force timeout/missing executable, preseed a green report,
  verify failure return code and fresh failed JSON. Depends on verification harness.
- Decision: **pursue** evidence reliability. Defer architectural rewrite, distributed
  workers and automatic lease takeover: they would expand operational failure modes.

### Dependency Health

- Current score/latest observations: **unavailable**; historical score 30.
- Current evidence: zero third-party runtime packages; universal transitive hash lock,
  direct-tool input file, exact build pin, shared scanner lock, monthly Dependabot,
  installed licence inventory and before/after advisory results.
- Staleness check: absence of a lock, hashes or dependency scans is not true of this
  revision. Historical vulnerable pytest/setuptools pins were replaced; rerun audits
  because advisory status changes. No claim that all packages are the newest versions.
- Additional gap: CI verifies installed versions but does not enforce that direct
  input constraints and the build pin agree with the committed lock. Lock regeneration
  is manual; a manifest-only dependency update could leave stale pins unnoticed.
- Improvement: validate exact locked versions, nonempty SHA-256 hashes, unique active
  resolutions, direct constraints and build-system consistency before installation/
  release. Cost 0.5–1.5h. Evidence: remove a hash, alter an input/build pin, duplicate a
  requirement; checks must fail; committed lock and clean hash installation must pass.
- Dependencies: packaging is already locked development tooling. No runtime package
  addition or resolver replacement is needed. **Pursue** lock consistency; do not
  churn all versions or add a framework merely to appear current.

### Test Coverage

- Current score/latest observations: **unavailable**; historical score 62.
- Local evidence: prior full run 143 tests, 94% combined coverage, 90% enforced floor;
  process tests include concurrency and abrupt termination, plus migration and SQL
  checkpoint failures. The historical 62 cannot be compared directly without the
  evaluator's measurement method and evaluated revision.
- Additional gaps: verifier/lock/CI guard failures lack behavioural regression tests;
  module CLI subprocess coverage is not aggregated into the parent measurement.
- Improvement: regression tests for the new guards and operational summaries; keep
  original assertions. Cost 0.5–1h alongside their features. Evidence: the new tests
  fail against the audited implementation and pass after fixes; full suite and branch
  coverage run. Depends on the corresponding features.
- Decision: **pursue** failure tests. Defer subprocess coverage aggregation unless its
  added configuration serves a reviewer need; do not chase 100% or weaken the floor.

### Code Cleanliness

- Current score/latest observations: **unavailable**; historical score 78.
- Current evidence: Ruff lint/format and strict mypy; small domain modules, no runtime
  eval/plugins, parameterized SQL, no new distributed layers.
- Additional gap: check_ci.py uses Python asserts for release invariants; `python -O`
  removes them. It accepts required step names without checking their actual commands.
- Improvement: explicit validation errors and tests that reject renamed/no-op gates,
  writable permissions, missing hashes and disabled coverage enforcement. Cost 0.5–1h.
  Evidence: malformed workflow fixtures fail even under optimized Python; actual YAML
  passes. Depends on the existing YAML development dependency.
- Decision: **pursue** the guard correction. Defer cosmetic module splitting and API
  rewrites; private ledger composition is intentional and transactionally tested.

### CI/CD Maturity

- Current score/latest observations: **unavailable**; historical score 68.
- Current evidence: Windows/Linux × Python 3.11/3.12, separate named quality steps,
  independent security job, timeouts, SHA-pinned actions, read-only token permissions,
  hash installation, package smoke and real demo.
- Additional gaps: YAML validation currently proves names, not functioning gates;
  no explicit direct-input/build-lock consistency gate. Hosted run status has not
  been independently verified in this audit; configured is not equivalent to passed.
- Improvement: enforce real gate commands in the local checker and add the lock
  consistency gate to CI/full verifier. Cost 0.25–0.75h after the two guard fixes.
  Evidence: CI contract regression tests, local full verifier, then actual hosted
  matrix results after authorized publication. **Pursue** local gates now; external
  branch protection/release deployment require a separate owner decision. No deployment
  pipeline is needed for a local library merely to add CI/CD features.

### Security Hygiene

- Current score/latest observations: **unavailable**; historical score 72.
- Current evidence: declarative bounded input, safe errors, no credentials/network
  service at runtime, parameterized SQL, no runtime dependencies, Bandit/pip-audit,
  metadata-only logs and a documented local-file trust boundary.
- Additional gaps: pipeline exceptions before output completion produce database
  events but no structured failure log; execution terminal logs/timestamps are incomplete.
  Repository secret checks are bounded working-tree heuristics, not full history or
  comprehensive secret detection. No application encryption, access-control service
  or hostile SQLite sandbox is claimed.
- Improvement: structured execution success/failure logs with execution/stage/generation,
  UTC time and safe reason codes, no exception text or payload. Cost 0.5–1h. Evidence:
  inject sensitive exception text, verify only stable code is persisted/logged; assert
  completion and interruption log context. Depends on existing engine, no telemetry SDK.
- Decision: **pursue** failure visibility and fresh scans. Defer auth services/encryption
  framework until multi-user/network use is justified; owner filesystem protections
  and retention practices remain explicit operational responsibilities.

### History & Maintenance

- Current score/latest observations: **unavailable**; historical score 20.
- Current evidence: genuine focused commits; new small project, no claimed external
  contributors, production deployments or organic long-term usage. Remote now matches
  the local revision, superseding the handoff's earlier unpublished/auth-failure status.
- Additional gap: historical handoff/audit text is still easy to confuse with current
  publication/verification state; owner licence/ownership checks remain outstanding.
- Improvement: update current handoff and append dated remediation evidence while
  preserving historical results. Cost 0.25–0.75h. Evidence: Git status/history/fetch,
  source revision recorded in reports, commands cross-checked against output. Depends
  on final verification. **Pursue** accurate documentation and meaningful commits.
  Do not manufacture age, issues, reviews, contributors or extra commits. Legal licence
  choice belongs to the owner; no licence grant will be added without approval.

## Prioritised implementation plan

Priorities weigh engineering value (40%), confidence in the verified gap (25%),
relevance to the named evaluation categories (20%) and low implementation/maintenance
cost (15%). These are our decision criteria, not DataFactor weights. Ordinal ranks
avoid inventing payout or score effects. All selected gaps have high confidence from
direct source inspection; operational summaries have medium benefit confidence.

| Rank / ID | Improvement | Value / relevance | Cost | Dependencies | Pursue? |
| --- | --- | --- | --- | --- | --- |
| 1 / A1 | Fresh failure-safe verification evidence | High / robustness, CI | 0.5–1.5h | None | Yes |
| 2 / A2 | Lock/input/build consistency | High / dependency, security, CI | 0.5–1.5h | None | Yes |
| 3 / A3 | Explicit semantic CI gates | High / CI, cleanliness | 0.5–1h | A2 for lock step | Yes |
| 4 / A4 | Safe terminal execution observability | High / robustness, security | 0.5–1h | Existing engine | Yes |
| 5 / A5 | Exportable batch quality aggregates | Medium-high / pipeline, quality | 0.5–1.5h | Existing row evidence | Yes |
| 6 / A6 | Regression tests, accurate docs/evidence | High / all categories | 0.75–1.75h | A1–A5 | Yes, paired with fixes |
| Deferred | External orchestration, microservices, dashboard, extra dependencies | Unproven | Days+ | Concrete user/load requirement | No |
| External | Latest category report + evaluated SHA, hosted CI, owner rights review | High evidence value | Owner/provider dependent | Publication/available report | Next evidence gate |

The previous lockfile, coverage gate, pipeline tests and documentation already exist.
This round strengthens their verified weak points. SQLite, public intake/replay
interfaces and lightweight operation remain. No forecast is made for 70 or 80+.
Implementation results and actual commands will be appended to REMEDIATION_REPORT.md;
this document is the pre-change audit and retains that distinction.

## Additional hosted evidence found during implementation
Public GitHub API query on 2026-10-25 confirmed main remains `1e81e2f`.
Run https://github.com/Ayoolaxrp/intakeledger/actions/runs/40131231743 belongs to
`dependabot/github_actions/actions/setup-python-7.1.0`, not main or these changes.
Security and Windows 3.11/Linux 3.11/Linux 3.12 succeeded; Windows 3.12 failed at
Dependency consistency (`pip check`). The job summary establishes that failure,
not its exact dependency cause. Full logs/root cause were not independently obtained.
The audited workflow installs tools directly into setup-python's environment.
Isolated venvs were added for both CI jobs as a proportionate dependency boundary.
This is not proof that the hosted failure is fixed: rerun the matrix after publication.

## Publication and hosted verification follow-up - 2026-10-26

Public main now resolves to ef4100eba5823fffb0dc16444c91ef441e76c1b4, matching
the audited/remediated local HEAD at the start of this follow-up. The three commits
are published. Public API run 40201420345 for that exact revision completed
successfully: all four Windows/Linux Python 3.11/3.12 quality jobs and security.
The Windows 3.12 dependency-consistency step therefore passed on this revision.
HOSTED_CI_OBSERVATIONS.json records the run, revision and individual step outcomes.
This supersedes the earlier pending-hosted-verification statement; it does not
establish the exact cause of the historical PR failure or predict a DataFactor score.
