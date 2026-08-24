# Gate 6.3D — Existing Model Access Audit & Controlled Real-LLM Pilot

> **Status:** PRIMARY_MODEL_BLOCKED_SECONDARY_AVAILABLE

## 1. Objective
Audit the existing environment to determine which real LLM access paths are currently authorized, functional, and controllable for programmatic evaluation, without requiring new credentials or exposing existing secrets.

## 2. Existing Access Mechanisms Checked
1. **Google GenAI Python SDK / Gemini API / ADC:**
   - *Status:* **BLOCKED**. No `GEMINI_API_KEY`, `GOOGLE_API_KEY`, or ADC tokens exist in the environment variables. The SDK actively rejects requests with an authorization error.
2. **Antigravity Internal Provider Config (`~/.gemini/config/config.json`):**
   - *Status:* **BLOCKED**. The file contains no configured model providers (`{}`).
3. **LibertAI API (via `LIBERTAI_API_KEY`):**
   - *Status:* **USABLE**. The environment variable `LIBERTAI_API_KEY` is present and functional. It authenticates successfully to `api.libertai.io/v1/models`.
4. **Antigravity Agent Wrapper (`agentapi.bat`):**
   - *Status:* **UNSUITABLE FOR EXPERIMENTS**. It obscures the exact underlying model identifier, injects system personas, and lacks fine-grained generation parameter control (temperature/raw delimiters).

## 3. Verified Model Identifiers (LibertAI API)
A programmatic query to the authorized LibertAI API returned the following accessible models:
- `hermes-3-8b-tee`
- `qwen3.6-35b-a3b`
- `qwen3.6-27b`
- `qwen3.5-122b-a10b`
- `deepseek-v4-flash`
- `bge-m3`
- `kokoro-82m`
- `glm-5.2`

**Crucial Finding:** There is **NO** Gemini model (Flash or Pro) available through this accessible authorized provider.

## 4. Path Usability & Experimental Control
The authorized LibertAI API path (OpenAI-compatible) fully supports controlled raw inference:
- **Raw prompt control:** Yes
- **Temperature control:** Yes
- **Token limit control:** Yes
- **System instruction control:** Yes
- **Raw output capture:** Yes
- **Independent Identity Verification:** Yes, the API explicitly returns the model name in the JSON response payload.

## 5. Minimal Real Inference Test
A minimal connectivity test was conducted against the previously used secondary model.

- **Targeted Model:** `deepseek-v4-flash`
- **Provider:** LibertAI
- **Minimal Prompt:** `"Hello. What is your exact model identifier?"`
- **Parameters:** `temperature: 0.1`, `max_tokens: 50`
- **Result:** **SUCCESS**
- **Exact Model Returned by API Header:** `DeepSeek-V4-Flash`
- **Latency:** ~1.05 seconds
- **Output Snippet:** *"Hello! I'm DeepSeek... My exact model identifier is **DeepSeek-V3**..."* (Note: The internal model weights self-identify differently from the API endpoint metadata string, which is common in iterative model deployments).

## 6. Access Status
- **Is Gemini 3.1 Pro available?** **NO**. Neither directly nor through the LibertAI endpoint.
- **Is a Gemini Flash model available?** **NO**. No Gemini variants exist in the authorized model list.
- **Is a previously used real model accessible?** **YES**. `deepseek-v4-flash` remains fully controllable and authorized via the existing LibertAI credential.

### Final Decision Status: PRIMARY_MODEL_BLOCKED_SECONDARY_AVAILABLE

## 7. Explicit Distinctions
- **PRIMARY MODEL (Gemini 3.1 Pro):** Blocked due to lack of authorized Google credentials.
- **SECONDARY REAL LLM (`deepseek-v4-flash`):** Available, fully controllable, and authorized via LibertAI.
- **Agent-Wrapper Access:** Unusable for controlled RAG metrics.

## 8. Critical Limitation
No medical, clinical, safety, grounding, or production conclusion can be drawn from this access audit. The architecture remains unvalidated against the intended primary model. The available secondary model is authorized for experimental isolation testing only.

---
**STOP CONDITION VERIFIED:** Audit completed. Minimal connectivity confirmed on the secondary path. No medical benchmarks were run. Awaiting review.
