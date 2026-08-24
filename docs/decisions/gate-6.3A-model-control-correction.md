# Gate 6.3A — Model-Specific Validation & Experimental Control Correction

> **Status:** EXPERIMENT BLOCKED (GEMINI_3.1_PRO_UNAVAILABLE)
> **Purpose:** Correct the experimental-control issues from Gate 6.3 by utilizing identical generation configurations (temperature) and executing the primary model validation against Gemini 3.1 Pro.

## 1. Primary Model Requirement
**Status: BLOCKED**
- **Expected Model:** Gemini 3.1 Pro
- **Availability:** An environment audit confirms that no API keys (e.g., `GEMINI_API_KEY`, `GOOGLE_API_KEY`) or Application Default Credentials are provisioned to access the Gemini API. 
- **Action:** Per strict instructions (*"If Gemini 3.1 Pro is unavailable, STOP and report the blocker"*), the Gate 6.3A evaluation was immediately halted.

## 2. Experimental Controls
**Status: BLOCKED**
The experimental design requires Config A, Config B, and Config C to be evaluated with strictly identical inference settings (temperature, top_p, max_tokens). This could not be executed due to the missing API access.

## 3. Benchmark Coverage
**Status: BLOCKED**
The intent was to execute the full 103-query Gate 5.1/Gate 6 benchmark across 5 independent runs per configuration (1,545 total inferences). Without model access, neither the full benchmark nor a stratified sampling plan could be executed.

## 4. Evaluation Metrics & Validator Status
**Status: BLOCKED**
- Raw counts, percentage metrics, and per-category results (Direct factual, NO_RELEVANT_SOURCE, translation drift, etc.) could not be gathered.
- Prompt injection bypasses could not be evaluated against Gemini 3.1 Pro.
- Latency metrics could not be gathered.

**Validator Clarification:**
The Config C validator designed for this architecture is strictly a **DETERMINISTIC OUTPUT RULE CHECKER**. It performs heuristic structural checks (e.g., numeric hallucination bounds, known adversarial string leakage) and does **NOT** function as a general medical claim-to-evidence verifier. It cannot detect arbitrary unsupported medical claims outside its hardcoded bounds.

## 5. Corrections to Earlier Overstatements
- Gate 6 and Gate 6.1 metrics were simulated and must not be treated as empirical safety proofs.
- Gate 6.3 metrics were executed against `deepseek-v4-flash` at variable temperatures, making it a valid secondary result but confounding prompt structure with temperature manipulation.
- We explicitly do **NOT** claim the model is safe.
- We explicitly do **NOT** claim hallucination is eliminated.
- We explicitly acknowledge that zero observed failures in a subset do not equate to zero true failure probability.
- The validator does **NOT** guarantee grounding.
- The architecture is **NOT** clinically validated.

## 6. Comparison with Previous DeepSeek Experiment
No comparison can be drawn, as the Gemini 3.1 Pro primary data remains entirely uncollected. The DeepSeek-v4-flash results in `gate-6.3-real-llm-validation.md` have been explicitly downgraded to a **SECONDARY REAL-LLM RESULT**.

## 7. Remaining Limitations
The architecture remains empirically unvalidated against its primary target model (Gemini 3.1 Pro). Structural boundaries (Configs B and C) have proven robust against secondary models, but without controlled empirical validation on the production-intended weights, progression to integration is structurally blocked.

---
**STOP CONDITION VERIFIED:** Gemini 3.1 Pro is unavailable. All execution halted. No production architecture was modified. We await environment resolution to execute Gate 6.3A.
