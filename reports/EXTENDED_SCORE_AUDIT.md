# Verified 68.6 feedback audit - 2026-10-28

Source: owner-supplied four-page DataFactor email dated 2026-10-28, titled
"intakeledger scored 68.6. Here's what gets it to offer territory". Read all four
pages; the original contains contact details and is not committed. It identifies
`ycent/intakeledger`, but does not identify the evaluated Git SHA. This supersedes
older category scores below. The goals of 70 and 80 are not predicted outcomes.
The provider's estimates are approximate; its scoring formula remains unknown.

Inspected baseline: local and public main `018275e6c6135f60c2db914ffb185047b76c21aa`,
clean before verification, repository ID 1431555822, owner ycent. All 15 existing
`python scripts/verify.py --security` gates passed: 171 tests, 94% combined
statement/branch coverage, strict typing, package build/smoke, real pipeline demo,
Bandit and advisory scan. Public application workflow run 40560106454 succeeded.
Dependabot pip update 40675941587 failed; public annotations only say updater error
and require write access for the detailed log. Do not invent its cause or claim
that dependency automation is healthy merely because its configuration exists.

Costs are focused engineering estimates, not score estimates. Priorities combine
engineering benefit, report relevance, confidence and cost.

| Category / score | Report weaknesses | Verified state and additional weaknesses | Proposed improvement / cost | Dependencies / evidence / worth pursuing |
| --- | --- | --- | --- | --- |
| Architecture & Robustness / 78 | No metrics/error-tracking integration | Structured native events, health, atomic stages and recovery exist. No hosted metrics service; threshold parsing allows unbounded scientific exponents despite a 32-character limit | P0 bound exponent before exact rational allocation (0.25-0.5h); retain local architecture | Tests prove dangerous values never reach Fraction; ordinary exact boundaries preserved. Yes; external error tracking not justified |
| Pipeline & Data Quality / 35 | No external orchestration, scheduling or cross-system lineage; recommends threshold gate | Local DAG/replay/backfill/rules and lineage exist. `quality` currently exits 0 even for rejected batches; no consumer-specific enforcement | P1 opt-in `quality --fail-on-threshold`, exact threshold override, minimum exportable rows, JSON reasons and safe event (1-2h) | Existing immutable summaries; CLI/library boundary, pipeline output, retry and no-mutation tests; real gate demo. Yes; framework/warehouse integration deferred |
| Docs & Onboarding / 85 | No container or env example | No environment configuration required. Offline commands do not explain prior dependency acquisition; THIRD_PARTY and handoff have stale top-level statements | P1 document connected preparation then offline setup, concrete lineage graph, current handoff/provenance inventory (0.5-1h) | Actual offline/installed workflows; avoid implying pip can install absent artifacts offline. Yes; no empty env template/container |
| Test Coverage / 82 | Existing nine modules, enforced 90 floor; recommends isolated offline execution | 171 baseline tests really pass, 94% local coverage differs from category score. No enforced guard against accidental network use in tests | P1 block Python socket/DNS operations for tests and child interpreters; test guard and isolated dependency installation (1-2h paired with tooling) | Minimal complete test dependency set and wheelhouse; retain all tests; full suite with guard. Yes |
| Code Cleanliness / 88 | Strong lint/typing and small modules | No rewrite justified. Reuse existing Fraction parser/quality summary, avoid parallel validation engine | Retain strict Ruff/mypy, pair fixes with tests (included above) | Full static checks; no new runtime dependency. Yes |
| Dependency Health / 55 | Scanner says no locks; cannot confirm Dependabot | Contradicted: three root dependency files and .github/dependabot.yml tracked; clean installation and sdist byte checks exist. Actual pip updater failed; no tests-only environment | P1 minimal test lock constrained by existing dev lock, drift/package checks, honest wheelhouse preparation; keep pip as sole supported installer (1-2h) | Resolver-generated hashes, fresh no-index/no-cache install, all tests, package inventory. Yes; no Poetry/uv project migration or arbitrary new runtime packages |
| CI/CD Maturity / 85 | No deploy stage | Library/CLI needs no deployment. Published application CI passed; pip updater failed separately | P1 enforce real quality-gate demo and offline suite in existing matrix; semantic guard against skipping new checks (0.5h) | Local configuration tests/full verifier; hosted result after branch publication. Yes; deployment stage no |
| Security Hygiene / 78 | Input validation detector empty | Detector misses custom guards; documentation maps them. New exponent allocation risk is real; raw data already excluded from diagnostics | P0 exponent bound; P1 safe gate events and network-denial test guard; repeat security audits (included above) | Regression tests before fraction construction, CLI rejection/privacy checks, Bandit/pip-audit. Yes |
| History & Maintenance / 20 | 15 commits/3 days, one author, no releases/tags/production users | Age, adoption and limited authorship are real; no instant honest fix | Focused genuine feature/fix commits with tests, no backdating, fake contributors or delayed work for appearance (normal workflow) | Actual diff/history. Worth normal maintenance; not cosmetic activity |

Order: baseline -> audit -> threshold resource fix -> enforceable quality gate ->
minimal offline test setup/CI -> documentation -> full clean verification -> branch
publication/PR if authentication permits. No direct main push under the new owner.
No DataFactor submission, agreement or paid service is authorized in this work.
A fresh evaluation of the published SHA is required to establish any score change.

---

# Verified feedback follow-up - 2026-10-27

Owner-supplied DataFactor email PDF dated 2026-10-27 reports **65.7 overall**,
not the previous 64.3. Report SHA-256: `4a1a730998b6edb67932ab442d07ce3b1e25db5b2198264a3e0d3311bd4f5e33`.
The report's evaluated Git SHA is absent. Local and public main both resolve to
396c667 at this inspection, with a clean working tree. The document was read
locally; the original contains personal contact details and is not committed.
Targets of 70/80+ remain goals. The provider's approximate point estimates are
not forecasts we can validate. No score, offer or payment is promised.

## Latest categories and verified disposition

Costs below are focused engineering estimates, not pricing or predicted points.
Historical audits below are retained; this table supersedes their unavailable
current category scores. The latest report includes a ninth category, Docs.

| Category / reported score | Report finding | Current verification / additional gap | Action, cost, dependencies and proof | Worth pursuing? |
| --- | --- | --- | --- | --- |
| Architecture & Robustness / 72 | Layered modules, SQLite atomicity and logging; truncated external-system comment | Transactions, recovery and bounded local design exist. JSON messages lack native event attributes; embedding CLI verbose logging depends on root configuration | Structured LogRecord metadata and scoped JSON CLI handler, 0.5-1.5h; depends on current logging calls; native-field, CLI, privacy and host-handler tests | Yes; no distributed rewrite |
| Pipeline & Data Quality / 45 | Stages, retries, backfill and rules exist; no Airflow/dbt/Dagster or external lineage | Pipeline.from_dict already supplies a declarative dependency graph; SQLite lineage is internal by design. Cross-system delivery/lineage is absent | Clarify scope and validation mapping, 0.25-0.5h; existing engine/tests are proof. External connectors need a real source/sink requirement | Documentation yes; framework adoption no |
| Docs & Onboarding / 80 | Docs exist; no changelog/container/env example | No environment variables are needed. README verification relies on reader following earlier setup; a direct clean development recipe and release notes are useful | Explicit isolated hash install, editable install, pytest and full verifier commands; concise changelog and validation reference, 0.25-0.75h; verify commands/build | Yes; no empty env example or unjustified container |
| Test Coverage / 68 | Seven test files, ratio and 90 floor; claims pytest-cov configured | Seven test modules plus conftest agree with that file count. Coverage uses coverage.py directly; pytest-cov is not a dependency. Last clean run: 158 tests and 94% combined coverage, a different metric from provider score | Pair new logging/package guards with behaviour tests; retain all old assertions; full coverage run, 0.5-1h paired with changes | Yes; do not chase line counts |
| Code Cleanliness / 78 | Ruff/strict mypy; pipeline largest module | Verified checks exist; no useful rewrite justified solely by file length. Logging formatting is repeated | Central metadata emitter/formatter removes repeated logging wrappers; lint/type/build/full tests; included in logging cost | Yes, scoped reuse only |
| Dependency Health / 40 | Scanner lockfiles_found empty; concludes fresh clone unreproducible | Contradicted: git tracks requirements-dev.in/.lock/security, MANIFEST includes them, and CLEAN_CHECKOUT.json records a successful fresh hash install at ef4100e. Zero runtime dependencies. Scanner bundle/parser cause unknown | Assert exact lock/input/security bytes survive sdist packaging, record filenames/hashes in smoke evidence, 0.25-0.75h; missing/tampered bundle regression and actual package rebuild | Yes; do not add competing locks or regenerate unchanged pins for appearance |
| CI/CD Maturity / 88 | Matrix, semantic gates, scans and pinned actions recognized | Public run 40201420345 passed all five jobs. Future changes need another hosted run | Preserve gates; local full verifier and subsequent hosted run, 0.25-0.5h validation overhead; requires publication/auth | Yes; no CD service needed |
| Security Hygiene / 78 | No secret hits; validation-pattern stats empty | Manual boundary validation exists despite scanner heuristic. Logging must omit values, labels and exception text. Full history/independent audit remain absent | Validation map and formatter allowlist, privacy/failure tests and fresh audits; included above | Yes; do not reshape validators to satisfy regexes |
| History & Maintenance / 30 | New single-author project, 11 commits/two days/no tags | New project is real; sustained adoption/maintenance cannot be created on demand. Current history has genuine later evidence commits | Commit real fixes with tests; do not fabricate contributors, backdate, churn code or create tags solely for score. Organic maintenance depends on real work | Normal maintenance yes; cosmetic history no |

## Ordered plan before code changes

1. Preserve and rerun current baseline. Check tracked lock files and package manifest.
2. Add structured event attributes plus a JSON stderr formatter for CLI verbose
   logging; preserve legacy JSON messages, stdout contracts, host logging handlers,
   safe metadata and current transaction/retry behaviour. Pair with tests/docs.
3. Verify exact dependency-lock material in source archives, including negative
   missing/tampered fixtures; keep the existing pip/hash-lock workflow and pins.
4. Document CLI/library validation, exact clean setup/test commands, supported scope
   and real release changes. Update remediation evidence after full verification.
5. Publish under existing authorization when authentication permits; inspect hosted
   CI, then obtain a fresh evaluation. No submission or agreement is authorized here.

Dependency chain: baseline -> feature/test changes -> full verification/package
proof -> authentic commit -> published revision/hosted CI -> new score. No defensible
numeric uplift can be calculated from the provider's partially unknown formula.
The highest-confidence evaluation discrepancy is missing-lock detection; independent
engineers can reproduce the committed lock regardless of that scanner result.

---

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
