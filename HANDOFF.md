# IntakeLedger handoff

## Where we stopped
Updated 2026-10-27. Version 0.2.2. Do not use Ponytail.

Read the owner-provided DataFactor email PDF: latest overall 65.7; full nine-category
breakdown and pre-change plan in reports/EXTENDED_SCORE_AUDIT.md. The PDF contains
contact details and was not committed. Its evaluated SHA is unknown. No score or
payout promise, fabricated contributor/history or DataFactor submission was made.

Implemented native structured LogRecord events with JSON-message compatibility,
scoped metadata-only JSON verbose CLI output, host/root handler preservation,
source-package lock-byte verification, clear clean setup, validation/scope docs and
real changelog. No runtime packages, schema change, orchestrator or external service.
Code commits: 48bc299 (logging/tests/docs), 7abc45d (release bundle/tests/onboarding).
The preceding audit commit is fdc1009. Tests were paired with their real changes.

Verified on a new tracked export/venv of 7abc45d: hash install, editable install and
all 15 full verifier gates passed. 171 tests, 94% combined coverage; original 158
preserved. Strict mypy (nine modules), lint/format, package build/installed CLI and
pipeline/lineage, source rebuild, real demo, pip check, semantic CI, Bandit and
pip-audit passed. See reports/REMEDIATION_REPORT.md and CLEAN_CHECKOUT.json.
The source package demonstrably includes exact requirements-dev.in/.lock/security
bytes. The provider's missing-lock inference conflicts with this proof; do not
add arbitrary locks or change architecture just to match its scanner.

Last independently observed public main: 396c667, hosted run 40381082305 successful.
This is not hosted verification of new 0.2.2. Both authorized push attempts failed
(configured GitHub CLI helper and native credential-manager override): Git for
Windows could not launch the helper child process (NtCreateDirectoryObject,
0xC0000022), then reported password unavailable. gh also reports an invalid session
token. New 0.2.2 commits remain local; host-side authenticated PowerShell can push.
Never force-push or extract tokens. Working tree is clean after the evidence commit.

Next: publish under existing owner authorization when authentication works, verify
new hosted CI, then have the owner request a fresh evaluation of that exact SHA.
If lock detection still fails, show paths, SHA, lock hashes and clean installation
results to DataFactor. Only a new evaluation can confirm a score change. Additional
frameworks/cosmetic history are not justified. Owner rights/licence decision,
independent security review, resource/load and power-loss testing remain open.
