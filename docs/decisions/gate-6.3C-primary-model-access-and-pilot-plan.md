# Gate 6.3C — Primary Model Access & Minimal Pilot Planning

> **Status:** PRIMARY_MODEL_ACCESS_STILL_BLOCKED

## 1. Official Access Requirements
A strict distinction exists between authorized access to Gemini via the Antigravity agent interface and the direct programmatic access required for this controlled architectural experiment. 
- **Agent Interface Access:** While the research environment can spawn agents using an underlying Gemini model (via `agentapi.bat --model=pro`), this path automatically wraps the LLM in an autonomous agent persona. It injects a massive system prompt and overrides generation parameters, destroying the strict grounding delimiters required for RAG evaluation.
- **Direct Programmatic Access:** Controlled RAG experimentation requires a raw API connection where the experiment script explicitly controls the prompt text, system instructions, temperature, and token limits, without any intervening agent middleware.

## 2. Exact Model Identifier Verification
- **Intended Target:** Gemini 3.1 Pro
- **Status:** **MODEL_IDENTIFIER_UNVERIFIED**
- **Reason:** Because direct access to the Google GenAI or Vertex AI model listing endpoints is currently unauthorized/unavailable in this environment, the exact API endpoint string (e.g., `gemini-3.1-pro`, `models/gemini-3.1-pro-001`, or a specific Vertex publisher path) cannot be verified. This must be confirmed prior to execution to prevent silent model substitution.

## 3. Minimal Pilot Experiment Design
To validate the experimental environment against the primary model without consuming significant quota, a minimal pilot has been designed:

- **Query Selection (5 total):**
  1. Grounded factual answer (Direct match)
  2. Partial retrieval / missing information (Child vs Adult)
  3. NO_RELEVANT_SOURCE (Out of scope)
  4. Translation meaning drift (Banglish ambiguity)
  5. Prompt injection attempt (Nested override)
- **Runs:** 3 independent runs per query (sufficient to verify stochastic variance existence).
- **Configurations:** Config A, Config B, Config C.
- **Total Inference Calls:** 5 queries × 3 runs × 3 configs = 45 total calls.
- **Parameters:**
  - `temperature`: 0.1
  - `top_p`: 0.95
  - `max_tokens`: 150
  - `timeout`: 15 seconds
  - `retry_policy`: Exponential backoff (max 3 retries for 429/500 errors).
- **Latency Measurement:** Python `time.perf_counter()` delta immediately wrapping the asynchronous SDK call to capture pure network + inference latency.

## 4. Preservation of Experimental Control
The previous secondary validation (Gate 6.3 with DeepSeek) confounded prompt architecture with temperature manipulation (Config A ran at 0.7, while Configs B/C ran at 0.1). 
This Gemini pilot corrects the confound by mandating **strictly identical inference settings** (`temperature=0.1`) across Config A, Config B, and Config C. The only independent variable will be the grounding instructions (the prompt architecture). This ensures any difference in hallucination or prompt injection resistance is purely attributable to the RAG boundary, not a temperature-induced decrease in stochastic creativity.

## 5. Honest Reassessment of Config C
Config C adds an output validation layer. However, it must be explicitly classified as a **Deterministic Output Rule Checker**, not a general medical claim-to-evidence verifier.
- **What it detects:** Hardcoded adversarial strings (e.g., "ignore previous instructions", "json") and unsupported numeric hallucinations (e.g., a dosage digit appearing in the output that does not exist in the retrieved text).
- **What it CANNOT detect:** Subtle medical hallucinations, semantic hallucinations, or incorrect treatments that don't trigger numeric checks (e.g., advising "apply ice" instead of "apply heat" when no digits are involved).
- **Metric Correction:** Gate 6.3's claim of "0 False Negatives" for Config C is misleading; it simply means no rule-based boundaries were breached. It does not prove the absence of subtle medical hallucination.

## 6. User-Side Setup Requirement
To authorize the environment for the future experiment, the user must establish raw programmatic access using one of the following methods. The research environment's Python SDK will automatically detect these without requiring the user to expose secrets in chat or repository files.

**OPTION A: Direct Gemini API Access**
- **What is needed:** A valid Gemini API Key from Google AI Studio.
- **Configuration:** Set the environment variable `GEMINI_API_KEY` on the host machine running the sandbox.
- **Detection:** The `google-genai` SDK will automatically authorize requests if this variable is present.

**OPTION B: Google Cloud / Vertex AI Access**
- **What is needed:** Google Cloud Application Default Credentials (ADC) tied to a GCP project with the Vertex AI API enabled.
- **Configuration:** Run `gcloud auth application-default login` on the host machine, OR set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to a local service account JSON file (which must be `.gitignore`d).
- **Detection:** The SDK natively scans for ADC tokens in the background to authenticate silently.

---
**Status:** PRIMARY_MODEL_ACCESS_STILL_BLOCKED
