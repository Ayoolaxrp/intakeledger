# IntakeLedger handoff

## Where we stopped
Updated 2026-10-25. Version 0.2.1.

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
See reports/REMEDIATION_REPORT.md and VERIFICATION.json. New clean-checkout network
installation was not rerun; old clean evidence is historical.

Remote: main matched public 1e81e2f at initial fetch. These new audit/remediation
commits have not been pushed. A public Dependabot setup-python PR failed pip check
on Windows 3.12 while the other matrix jobs/security passed. CI isolation was added,
but the precise failing dependency and a hosted rerun remain unverified. Metadata
is in HOSTED_CI_OBSERVATIONS.json.

Next: owner-authorized publication and hosted matrix verification; obtain actual
latest DataFactor category report/evaluated SHA and review ownership/licensing before
commercial commitments. Stop additional speculative features pending that feedback.
No submission, agreement, deployment or licence grant was performed.

Do not use Ponytail. Keep work focused. Do not manufacture history or external users.
