# Gate 6.3F — Secondary Real-LLM Pilot Results

> **Status:** EXPERIMENT BLOCKED (QUOTA EXHAUSTED)

## 1. Experiment Identity and Scope
This document records the attempt to execute a **SECONDARY_MODEL_SINGLE_RUN_PILOT**. The pilot was designed strictly for real-LLM harness validation and exploratory observation using an available secondary model, not as a substitute for primary validation.

## 2. Exact Model and Generation Controls
All controls were fixed prior to execution:
- **Exact Model ID:** `gemini-3.7-flash`
- **Thinking Level:** `low` (Used strictly for reasoning variance control, not a medical safety claim).
- **Max Output Tokens:** 512
- **Response Modality:** text
- **Legacy Parameters:** Temperature, top_p, and top_k were omitted as they are unsupported/ignored for 3.x reasoning models.
- **Retrieval Context:** Identical per-query.

## 3. Quota Accounting
- **Planned Experiment Calls:** 15 calls.
- **Model Quota Failures:** 1 call immediately failed due to a hard 429 `RESOURCE_EXHAUSTED` error. The API specified `GenerateRequestsPerDayPerProjectPerModel-FreeTier` limit reached (20 calls/day limit).
- **Retry Attempts:** 0 silent retries. Execution was halted immediately as the quota remained exhausted from prior testing.

## 4. Frozen Test Cases
The 5 frozen test cases (Factual Retrieval, Missing Information, Out-of-Corpus, Translation Drift, Prompt Injection) were strictly coded into the execution harness, enforcing the deterministic rule checks without modification.

## 5. Per-Call Execution Results
No successful inferences were generated during this run. The environment quota rejected the very first call.
- **Case 1 (Factual):** MODEL_ERROR (429 Quota Exhausted)
- **Case 2 (Missing Info):** NOT_ATTEMPTED
- **Case 3 (Out-of-Corpus):** NOT_ATTEMPTED
- **Case 4 (Translation Drift):** NOT_ATTEMPTED
- **Case 5 (Prompt Injection):** NOT_ATTEMPTED

## 6. Deterministic Checker Observations
The deterministic output rule checker did not process any outputs due to the immediate API rejection.

## 7. Failures/Anomalies
A hard environment failure occurred. The Free Tier daily quota for `gemini-3.7-flash` (20 Requests Per Day) was entirely exhausted by prior environment activity. Despite observing the reset window, the quota could not accommodate the required 15-call burst without hitting the ceiling again.

## 8. What Was Observed
The experimental script successfully instantiated the SDK, proved the prompt logic was correctly structured with the new `thinking_level` controls, and strictly enforced quota accounting by cleanly halting execution upon exhaustion.

## 9. What Was NOT Established
This pilot is single-run evidence for a secondary model. It does NOT establish or support:
- Statistical safety or robustness claims
- Hallucination-rate estimates
- Medical or clinical validation
- Reproducibility or production readiness

## 10. Comparison Boundary against Gemini 3.1 Pro
**This is Gemini 3.7 Flash only.** It is not evidence about Gemini 3.1 Pro. The primary model (Gemini 3.1 Pro) remains entirely untested due to lack of authorization, and no clinical or medical safety conclusion can be made.

## 11. Remaining Unknowns
- How the primary model responds to strict bounding prompts.
- Whether the RAG architecture is resilient against prompt injection on the primary model.
- Whether the secondary model behaves differently than previous baseline models.

## 12. Stop Condition
**STOP CONDITION VERIFIED.** The API returned a daily quota exhaustion error on the first planned call. In strict compliance with instructions, the script aborted execution. 

Execution has been stopped. I will not proceed to Gate 6.4, Gate 7, or production integration. Awaiting independent review.
