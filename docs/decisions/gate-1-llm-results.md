# Gate 1: LLM Comparison Results (Cumulative)

> **Status:** MULTI-SESSION EVALUATION
> **Dataset:** 24 synthetic cases (Bangla, English, Mixed, Ambiguous, Unsafe, Urgent)

## 1. Operational & API Accounting Metrics (Aggregated)
The following metrics strictly account for every API call sent to the models, separating minimal availability probes, smoke tests, evaluation cases, and orchestration retries.

| Model | Total API Reqs | Probes (Pass/Fail) | Smoke Reqs | Eval Reqs | Retries | 503 / 429 Events |
|---|---|---|---|---|---|---|
| `models/gemini-3.7-flash` | 13 | 1 / 0 | 2 | 1 | 9 | 2 / 0 |
| `models/gemini-3.6-flash` | 42 | 0 / 1 | 2 | 19 | 20 | 0 / 2 |

## 2. Capability Metrics (Aggregated)
The following metrics measure model reasoning, language handling, and safety behavior across all successfully processed cases.

| Model | Cases Completed | JSON Valid Rate | Safety / Guidelines Adherence |
|---|---|---|---|
| `models/gemini-3.7-flash` | 0 / 24 | N/A | N/A (Awaiting execution) |
| `models/gemini-3.6-flash` | 18 / 24 | 18/18 | [Pending Manual Review] |

## 3. Evaluation Environment
- **Last Updated:** 2026-08-20T09:59:33.056763Z
- **Total Runs:** 1

## 4. Recommendation
**[PENDING]** — Awaiting human review of capability results vs. availability.