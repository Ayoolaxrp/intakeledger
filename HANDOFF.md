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

Checked: Original 103 tests passed. Expanded 140-test suite passed at 93% combined
coverage; 40 pipeline cases including three subsequent regressions passed. New
source lint, format and strict mypy passed. Actual Bandit and updated dependency
audit found no findings. Old pins had known advisory findings. Evidence is in
reports/REMEDIATION_REPORT.md; final clean-source verification remains pending.

Environment: Default Windows sandbox temp names contain braces; setuptools fails
editable installation with an invalid substitution variable. A failed clean attempt
is preserved in CLEAN_CHECKOUT_BEFORE.json. Build children now use a plain temporary
path and the helper creates a disposable directory beside the checkout. The corrected
fresh environment must be verified before claiming release readiness.

GitHub: Owner authorized public visibility and a push of verified remediation.
Remote was still original 9fd7a19 at restoration. Saved gh authentication is invalid;
no successful remediation push is claimed. Genuine commits record this work. A prior
ycent invitation exists; no new invitation or acceptance was performed.

Next: Finish corrected clean-source verification, finalize audit evidence, inspect
the diff, commit reports and attempt the authorized non-force push. Verify the remote
SHA before claiming success. Hosted CI, Linux/Python 3.12, production load, legal
ownership/licensing and a fresh DataFactor score are not verified. Stop speculative
feature work and use CI/evaluation feedback after the owner's licence/rights review.

Owner constraints: Do not use Ponytail. Keep work focused and fast. Do not submit to
DataFactor, sign agreements, deploy or add a project licence without authorization.
