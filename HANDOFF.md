# IntakeLedger handoff

## Where we stopped
Updated 2026-10-26. Version 0.2.1.

Audited all eight DataFactor categories in reports/EXTENDED_SCORE_AUDIT.md. Overall
64.3 is owner-reported; the owner chose to proceed without the current category
breakdown. Missing facts are labelled unavailable, old scores historical; no score
forecast or payout is promised.

Implemented: offline lock/input/build consistency, explicit semantic CI guards,
failed-tool evidence replacement, clean-checkout failure reporting, safe batch quality
summary API/CLI, terminal execution logs/timestamps, isolated CI environments, docs
and 15 new regression cases. SQLite, runtime dependencies (none), schema v2 and
existing intake/replay APIs are preserved. Code commit: 985b71f6ebc13ed51fb3f4ba70b0e2410c5f9cf1.

Verified: all 15 full verifier checks passed; 158 tests, 94% combined coverage;
format, lint, strict mypy, lock/inventory/pip consistency, repository heuristic,
0.2.1 wheel/sdist build, installed library/CLI/pipeline/lineage with site-packages
disabled, source rebuild, real demo, CI configuration, Bandit and pip-audit.
See reports/REMEDIATION_REPORT.md and VERIFICATION.json. On 2026-10-26,
scripts/clean_checkout.py exported tracked ef4100e into a new environment,
hash-installed all 43 tooling distributions, installed editable and passed all 15
verifier gates. Fresh suite: 158 passed in 60.05s, 94% coverage; scans/build/demo
passed. CLEAN_CHECKOUT.json records all_passed=true and the exact source revision.

Remote: public main now matches ef4100eba5823fffb0dc16444c91ef441e76c1b4.
The audit/remediation commits are published. Hosted push run 40201420345 passed
all four Windows/Linux Python 3.11/3.12 quality jobs and security, including the
previously failing Windows 3.12 dependency step. The historical exact cause remains
unknown. Current API metadata is in HOSTED_CI_OBSERVATIONS.json.

This follow-up updates publication/hosted evidence and stale documentation without
runtime changes. This session's gh token still reports invalid. New follow-up
documentation/evidence remains local: the authorized push failed with
`fatal: unable to get password from user`. The working tree is clean after commit;
the implementation through ef4100e is already published. Retry the follow-up push
only with working authentication; never force-push.
The attached Pasted text(3).txt could be identified but not read or downloaded:
no parsed text, then two TLS transport failures. Do not invent its findings.

Next: obtain actual latest DataFactor category report/evaluated SHA as readable text
and review ownership/licensing before
commercial commitments. Stop additional speculative features pending that feedback.
No submission, agreement, deployment or licence grant was performed.

Do not use Ponytail. Keep work focused. Do not manufacture history or external users.
