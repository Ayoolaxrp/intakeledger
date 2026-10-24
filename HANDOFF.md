# IntakeLedger handoff

## Where we stopped
Updated 2026-10-24.

Done: Restored public 0.1 main from https://github.com/Ayoolaxrp/intakeledger into
C:\Users\User\Projects\intakeledger after the previous local folder disappeared.
Implemented 0.2 durable SQLite pipelines, declarative quality checks, atomic stage
checkpoints, explicit generation-fenced recovery, typed lineage, ordered backfill,
v1 migration, library/CLI integration, real synthetic demo and failure tests.
Added a universal hash lock, aligned build pin, coverage gate and separate CI jobs.
No runtime dependencies, project licence or external deployment were added.

Checked: Final clean tracked export at 4448785 passed all 14 verification checks
on Windows/Python 3.11.15: 143 tests in 79.30s, 94% combined coverage, lint, format,
strict types, zero-runtime dependency inventory, repository heuristic, wheel/sdist
build, installed library/CLI/pipeline with site-packages disabled, source rebuild,
real demo, pip check, CI configuration, Bandit and dependency audit. The fresh venv
hash-installed all dependencies and editable-installed the package. Actual results
are recorded in VERIFICATION.json, CLEAN_CHECKOUT.json and REMEDIATION_REPORT.md.

Environment: Default Windows sandbox temp names contain braces; setuptools fails
editable installation with an invalid substitution variable. A failed clean attempt
is preserved in CLEAN_CHECKOUT_BEFORE.json. Build children now use a plain temporary
path and the helper creates a disposable directory beside the checkout. The corrected
fresh setup succeeded, and the final verifier completed directly in that prepared
environment after the setup wrapper was interrupted. This is recorded explicitly.

GitHub: Owner authorized public visibility and a push of verified remediation.
Remote was still original 9fd7a19 at restoration. Saved gh authentication is invalid;
the actual authorized push returned exit 1, unable to get a password. No
successful remediation push is claimed. Genuine commits record this work. A prior
ycent invitation exists; no new invitation or acceptance was performed.

Next: Restore authentication in the owner's terminal and run
`git -C "C:\Users\User\Projects\intakeledger" push origin main`.
Verify the remote SHA and hosted CI. No additional speculative features are justified
before independent CI/evaluation feedback. Linux/Python 3.12, production load, legal
ownership/licensing and a fresh DataFactor score remain unverified. No licence or
external evaluation submission was authorized by this session.

Owner constraints: Do not use Ponytail. Keep work focused and fast. Do not submit to
DataFactor, sign agreements, deploy or add a project licence without authorization.
