# Current quality gate - 2026-10-28

IntakeLedger 0.2.3 source `b544b7b` passes all 16 full verification gates and a
separate fresh offline setup, with 212 tests and 94% combined coverage. The full
results, numeric-input corrections, consumer gate semantics and unresolved hosted
publication/authentication status are in [REMEDIATION_REPORT.md](REMEDIATION_REPORT.md).
The latest supplied score is 68.6, not a prediction for this revision. New hosted
CI, owner-only Dependabot diagnosis, legal rights/licence approval and independent
security/load/power-loss review remain unverified. No new publication or commercial
licence grant is claimed. The original audit below is retained as historical evidence.

---

> Historical 0.1 audit. The 2026-10-24 remediation and executed results in
> [REMEDIATION_REPORT.md](REMEDIATION_REPORT.md) supersede current-state claims here.
> Public visibility was owner-authorized; no licence grant has been approved.

# Final engineering and commercial audit
Audit date: 2026-10-23. Product: IntakeLedger 0.1.0. Status: locally implemented and verified, not approved for external publication or commercial licensing.

## Verified execution
The final verification run executed on Windows, Python 3.11.15, SQLite 3.53.1. See VERIFICATION.json for actual commands, return codes, versions, output summaries, and artifact hashes.

| Check | Observed result |
| --- | --- |
| Behaviour suite | 103 tests passed, including success, failure, boundary, replay, SQL injection labels, unrelated-database preservation, concurrent processes, and writer-process death |
| Coverage | 93% combined statement and branch coverage. 489 statements, 194 branches. Contract and ledger modules each reported 99%. CLI subprocess runs are not included in parent-process coverage. |
| Ruff lint and format | Passed for source, tests, and scripts |
| Strict mypy | Passed for all 6 runtime source files |
| Dependency inventory | 0 runtime packages, 13 pinned development distributions matched installed versions |
| Repository inspection | Local credential-pattern and code-execution checks reported no findings. This is a bounded heuristic, not a comprehensive secret-scanning service. |
| Build | Wheel and source archive built successfully |
| Installed package | Wheel installed into a temporary location, library and CLI ran with Python site-packages disabled, and the extracted source archive rebuilt |
| CI configuration | YAML parsed locally. Read-only permissions, pinned action commits, and Windows/Linux Python 3.11/3.12 jobs are present. Hosted execution was not performed. |

The workflow was exercised end to end with synthetic data. Rejected batches block export. Whole-batch replay preserves the original result and row lineage. A process terminated during an actual row insert left no partial rows or batch after SQLite recovery.

## Checks not completed
- pip-audit and Bandit were not installed. Installation of pinned scanner tools failed because the configured package source returned no matching distribution. No vulnerability scan or Bandit pass is claimed.
- Hosted CI, Linux, Python 3.12, power-loss behaviour, performance limits under load, and external security review were not executed here.
- Legal ownership, jurisdictional treatment of AI-assisted work, and the owner's project licence are unapproved.
- No real Git author identity is configured. No commits, remote creation, pushes, DataFactor submissions, contract acceptance, or customer integrations occurred.

## Quality gate
| Requirement | Status and evidence |
| --- | --- |
| Coherent problem and substantive original implementation | Verified bounded intake workflow. Original session implementation, no cloned source. Global uniqueness and legal originality are not guaranteed. |
| Proportionate architecture | Reviewed CLI, contract validation, one transactional ledger, and one migration |
| End-to-end operation | Tests and installed-package workflow passed |
| Clean-checkout build | Clean extracted source archive rebuilt using the pinned local build tools. A fresh network installation of all tool packages was not validated. |
| Tests executed and failure paths covered | 103 passed. Process death, lock conflict, insert failure, malformed input, and identity conflicts covered. |
| Reproducible setup and schema | Explicit initialization, schema identity checks, pinned development lock, bounded configuration. No external database service. |
| Dependencies and notices reviewed | Runtime platform and direct/transitive development inventory reviewed. Top-level metadata plus selected installed licence files inspected. Vendored tooling notices are not a complete file-level legal audit. |
| No known secrets or real records | Synthetic fixtures and local heuristic scan plus source review. Not a mathematical absence proof. |
| Documentation matches code | Commands, limits, replay, errors, and transaction boundaries reviewed |
| CI present and locally checked | YAML structure checked, hosted jobs unrun |
| Genuine history and contributors | No fabricated history, reviews, contributors, or adoption |
| Limitations documented | docs/KNOWN_LIMITATIONS.md and docs/THREAT_MODEL.md |
| Independent inspection | README, specification, decision record, tests, verifier, and source archive available |
| Ownership and licence assumptions | PROVENANCE.md documents owner checks. Commercial approval remains pending. |
| No unsupported commercial claims | No promised score, buyer interest, offer, or payout |

No known failing application behaviour remains in the executed test scope. The untested cases and tooling gaps above remain material limits.

## Commercial assessment
1. **Technical value.** The useful work is atomic intake with explicit rejection policy, strict contracts, retry conflict detection, source identity, and replay under changed rules. Those behaviours solve a coherent local data-engineering problem.
2. **Differentiation.** The combination of whole-batch replay, unchanged parent decisions, line-level provenance, exact gate arithmetic, and process-failure tests is more specific than a CRUD template. Data validation itself is established software, and no invention claim is made.
3. **Evidence.** The executed suite, type and lint checks, installed package test, source rebuild, and reviewable failure tests support quality within the bounded scope.
4. **Possible buyer relevance.** Contracts, transactional invariants, parsing boundaries, concurrent retries, crash recovery, and real implementation decisions can support engineering tasks. Actual buyer demand is unverified.
5. **Weaknesses.** This is a small new project with no production history, users, issue discussions, or natural maintenance evolution. Comparable validation and ingestion tools exist. Missing external scans and cross-platform execution reduce confidence.
6. **DataFactor uncertainty.** No public internal scoring weights, offer threshold, new-repository policy, AI-assistance policy, or definitive effect of additional repositories on existing offers was verified. Public scoring examples do not establish licensing eligibility.
7. **Further work with defensible return.** Confirm eligibility first. If a buyer expresses concrete interest, run hosted CI, complete dependency/security scans, approve ownership/licensing, and address actual reviewer findings. Connectors, dashboards, and larger code volume have no present justification.
8. **Recommendation.** Stop feature development. Keep the repository private and request eligibility guidance before submitting code. It is inspectable engineering work, but commercial acceptance is not established.
9. **Cheapest next step.** Ask whether DataFactor evaluates newly created, AI-assisted, privately held repositories without production users, and what rights or history it requires. Ask whether a new submission can alter existing offers. No message has been sent.
10. **Evidence that changes the recommendation.** Written acceptance criteria, a specific buyer request, a genuine evaluation report, failing independent tests, or legal restrictions would change the next investment. A payout estimate alone would not justify major expansion.

The evidence supports a completed local core. It does not support a favourable grade prediction or further speculative development spending.
