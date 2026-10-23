# Project selection
Decision date 2026-10-23. Weights were assigned before candidate scores. These are engineering estimates, not DataFactor's rubric. Scores are 1-5, higher is better, including lower risk and cost.

## Weights
| ID | Criterion | Weight | Reason |
| --- | --- | ---: | --- |
| A | Technical depth | 12 | Correctness work must be substantive. |
| B | Differentiation | 8 | Generic clones have little distinctive value. |
| C | Practical usefulness | 10 | The system needs a credible purpose. |
| D | Architecture | 8 | Boundaries must support independent review. |
| E | Behavioural tests | 10 | Failure handling must be provable. |
| F | Time fit | 8 | A finished core beats an unfinished platform. |
| G | Reproducibility | 8 | Reviewers need local execution. |
| H | Engineering and AI relevance | 6 | Contracts and recovery are useful engineering examples. |
| I | Less generic competition | 5 | Mature alternatives reduce novelty. |
| J | Lower IP and legal risk | 5 | Avoid copied code and sensitive integrations. |
| K | Agent delivery feasibility | 6 | The core must be testable here. |
| L | Lower cost per useful result | 6 | Commercial demand is uncertain. |
| M | Useful decision trace | 4 | Document actual tradeoffs. |
| N | Verified eligibility fit | 4 | Public guidance is broad; eligibility is unresolved. |

## Matrix
All weights total 100. Total = sum of weight times score / 5.
| Candidate | A | B | C | D | E | F | G | H | I | J | K | L | M | N | /100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| IntakeLedger | 4 | 4 | 4 | 4 | 5 | 5 | 5 | 4 | 3 | 5 | 5 | 5 | 5 | 3 | 87.6 |
| Incremental build inspector | 4 | 3 | 4 | 4 | 4 | 4 | 5 | 5 | 2 | 5 | 5 | 4 | 4 | 3 | 80.6 |
| Settlement reconciliation | 5 | 3 | 5 | 4 | 5 | 3 | 4 | 4 | 2 | 3 | 4 | 3 | 5 | 3 | 79.0 |
| Durable job queue | 5 | 2 | 4 | 5 | 5 | 3 | 4 | 4 | 1 | 5 | 4 | 3 | 5 | 3 | 78.0 |
| Document extraction pipeline | 4 | 3 | 5 | 4 | 4 | 3 | 3 | 5 | 2 | 3 | 4 | 3 | 4 | 3 | 73.4 |
| Policy access service | 5 | 2 | 5 | 5 | 5 | 2 | 3 | 4 | 1 | 3 | 3 | 2 | 5 | 3 | 72.4 |

## Candidate reasoning
- IntakeLedger joins immutable source identity, strict versioned contracts, batch quality gates, row quarantine, and lineage-preserving replay in one local transaction workflow. Validation competition is substantial, including GX. The narrower workflow, offline execution, and recovery tests are its reason to exist.
- A build inspector would analyse dependency changes and affected targets. It is cheap to reproduce but language support and parser correctness widen scope. Build tools already provide much of this.
- Settlement reconciliation has valuable ambiguity and conservation rules, but real finance semantics and grouping behaviour require more domain validation. No payment integration is needed, yet incorrect money handling has higher risk.
- A durable queue has rich lease, retry, and crash semantics. Strong established implementations make differentiation difficult, and process lifecycle testing costs time.
- Document extraction is useful, but OCR and format dependencies reduce reproducibility. Extraction quality needs a representative rights-cleared corpus.
- An access-policy service has deep security rules but is crowded and expensive to validate properly. A rushed implementation is a poor commercial tradeoff.

## Decision
Select IntakeLedger. Build Python 3.11+ plus SQLite and a CLI. The available interpreter and test tools support execution on this machine. No runtime packages, hosted service, UI, or external data is required.

Eligibility receives 3 for every candidate because broad software categories fit, while new AI-assisted code eligibility is unconfirmed. A one-point reduction to IntakeLedger's differentiation and usefulness scores gives 84.0, still above the runner-up. A buyer requirement for production history would invalidate the whole new-build premise, not merely change the winner.

Stop after a complete, validated core. Ask DataFactor about new AI-assisted projects before investing in connectors, dashboards, or scale tuning. Do not submit or publish without owner approval.
