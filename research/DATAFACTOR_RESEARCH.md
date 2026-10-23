# DataFactor research
Checked 2026-10-23. Research precedes implementation. Official pages were read through a browser because the search reader returned empty pages. No repository, credential, form, or private data was submitted.

## Official evidence
| Source | Evidence and conclusion | Confidence and limits |
| --- | --- | --- |
| [Repository assessment](https://datafactor.com/score) | Assesses technical quality, complexity, history, documentation, and AI-development value. Named dimensions include architecture, testing, maintainability, security, and development history. | Verified public statements, not a disclosed scoring formula. |
| Same assessment page | Backend, infrastructure, developer tooling, data engineering, applications, and specialized software are listed. Multiple repositories can be assessed. Quality, scope, uniqueness, volume, and history affect compensation. | Marketing guidance, not a price model. |
| Same assessment page | Static analysis and a Claude judgment pass produce estimates. Submitted code is not executed or used for training during scoring. Code is described as ephemeral; scores persist. Tokens are saved for follow-up. | Vendor claims, not independently audited. Do not confuse static scoring with execution verification. |
| Same assessment page | Figures are non-binding. An offer requires review and a separate agreement. Necessary submission rights are required. | No guaranteed offer, grade, or payout. |
| [Home](https://datafactor.com/) | Focuses on private proprietary data, production code, commits, pull requests, issues, tests, and reviews. Provenance, uniqueness, scale, structure, and buyer fit matter. | Does not establish that a fresh synthetic project will be purchased. |
| [Terms](https://datafactor.com/terms), effective 2026-09-15 | Sections 2-4 require authority and accurate submissions. Commercial rights need a separate signed agreement. Submitters retain ownership and grant a limited non-exclusive site-evaluation licence. Scores may be refreshed or withdrawn. | Read on check date. This research is not a legal determination. |
| [Partner programme](https://datafactor.com/data-partner) | Scope, security, anonymization, permitted use, retention, and commercial terms require review. | Enterprise workflow programme differs from the repository scoring form. Its company payout ranges are not estimates for this project. |

## Questions public evidence does not settle
- Public repositories can appear as scoring examples, but that does not prove licensing eligibility. Keep this project unpublished.
- No explicit minimum age, commit count, source line threshold, or public eligibility rule for new or AI-assisted repositories was found in the reviewed pages and focused searches.
- No published grade-to-offer threshold, internal weights, or reliable payout calculation was found.
- Multiple repositories are supported. No statement establishes whether adding one affects previous evaluations or offers. The terms permit score changes, so neither independence nor harm can be assumed.
- No claim is made about approval of this owner's rights, jurisdiction, AI-generated material, or future licence.
- Website content and terms can change. Confirm current contract terms before sharing code or tokens.

## Engineering judgment
A small working repository with failure tests and traceable decisions has defensible inspection value. Production use and long development history cannot be recreated in one session. The commercial hypothesis is weak until DataFactor confirms appetite for newly built AI-assisted code. Limit spending, preserve genuine history only, and stop adding speculative features.

## Other primary references
- [SQLite transaction semantics](https://www.sqlite.org/lang_transaction.html), checked 2026-10-23. One writer at a time; BEGIN IMMEDIATE acquires the writer transaction early. This supports the persistence design, not a DataFactor prediction.
- [Python sqlite3](https://docs.python.org/3.11/library/sqlite3.html), checked 2026-10-23. Standard-library embedded persistence and parameterized SQL.
- [Great Expectations introduction](https://docs.greatexpectations.io/docs/core/introduction/), checked 2026-10-23. Established data-validation workflows exist. IntakeLedger must justify its bounded transactional intake and replay workflow rather than claim to invent validation.
