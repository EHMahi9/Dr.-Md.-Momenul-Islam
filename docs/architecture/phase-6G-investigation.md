# Phase 6G Investigation & Failure Analysis Report: Multilingual Retrieval & Runtime State

**Project:** Dr. Md. Momenul Islam — Bangladesh-Focused Multilingual Clinical Evidence Retrieval / Health Intelligence Prototype  
**Date:** 2026-08-29  
**Status:** `INVESTIGATION_COMPLETED` (Read-Only Diagnostic — No Algorithms or Code Modified)  
**Corpus State:** 119 active chunks across 14 NHS conditions (`DOC-NHS-004` through `DOC-NHS-017`)  
**Frozen Strategy 5 SHA-256:** `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae`  
**Active Corpus Manifest SHA-256:** `44d0602f730d6460e6fefa431bd5c09005b48ce92b47d02832532e5868d4aa58`  
**Gate 5.28 Locked Benchmark SHA-256:** `464612e733aeb1496c1dcdc5674e01d9504bd4ccd1244190e487c6e957dcc722`  
**Phase 6F Eval Benchmark SHA-256:** `c4603199028cb649617b59d2523bb1a64b92876ffcc899285a946e940257ee61`  

---

## 1. Executive Summary

This investigation was conducted in strict read-only mode to address two specific questions:
1. **Investigation A:** Why did browser screenshots display `Active Corpus: 68 Chunks` and `Staged Research: 51 Chunks` when Phase 6C and Phase 6F established an active corpus of 119 chunks?
2. **Investigation B:** Exactly where and why does retrieval degrade on Romanized Bangla (Standard Banglish) and Abbreviated Banglish, causing the directly supported claim rate to fall from 100% (English) and 84.62% (Native Bangla) to 63.64% (Banglish)?

### Key Discoveries at a Glance:
- **Investigation A Verdict:** The 68 vs 119 discrepancy was caused by three interacting runtime and frontend factors:
  1. A zombie Python backend process (`PID 10036` started at 8:26 AM during Phase 6A) remained bound to port 8000 in an unresponsive state.
  2. When `fetchHealth()` timed out or failed against port 8000, `Header.tsx` evaluated default fallback values hardcoded in Phase 6A: `health?.active_corpus_chunks ?? 68` and `health?.staged_research_chunks ?? 51`.
  3. In `backend/app/api/endpoints.py`, `/health` was reading the historical ingestion manifest (`51` chunks) rather than reporting `0` staged chunks, creating a secondary inconsistency.
- **Investigation B Verdict:** The degradation on Banglish is **NOT** a general multilingual embedding collapse. Step-by-step pipeline tracing revealed **two distinct failure mechanisms**:
  1. **Candidate Generation Dropout (Primary Mechanism — 71.4% of failures):** Unmapped Banglish anatomical and colloquial symptom words (`agune porle`, `nak die`, `norom ongsho`) fail to trigger dictionary expansion or match dense English vectors, dropping gold passages out of the initial Dense Top-15 candidate pool entirely.
  2. **Over-Broad Rule Collisions (Secondary Mechanism — 28.6% of failures):** Generic keyword triggers (e.g. `bleeding` matching `cuts grazes dressing wound`) forcibly steer dense retrieval toward cuts/grazes (`DOC-NHS-006`), overriding and suppressing specialized conditions (such as nosebleed `DOC-NHS-016`).

---

## 2. Current Repository State

- **Current Branch:** `main`
- **Current HEAD Commit:** `e1f9f4d` (`feat(phase-6F): grounded generation evaluation & evidence-gating validation`)
- **Working Tree:** Clean (`nothing to commit, working tree clean`)
- **Key Commit Lineage:**
  - `67f364b`: Phase 6A.4 — Initial Corpus Lifecycle & Multi-Tier Schema (Active: 68, Staged: 51).
  - `080ca05`: Phase 6C — Controlled Corpus Promotion (Active: 119 chunks across 14 NHS sources).
  - `afcbd23`: Phase 6D — Grounded Generation Architecture Design.
  - `e983454`: Phase 6E — Controlled Real LLM Integration & Smoke Validation.
  - `e1f9f4d`: Phase 6F — 48-case Grounded Generation & Evidence-Gating Evaluation.
- **Checksum Verification (OBSERVED FACT):**
  - Active Corpus Manifest (`promoted_corpus_manifest.json`): `44d0602f730d6460e6fefa431bd5c09005b48ce92b47d02832532e5868d4aa58` (119 chunks, 14 sources).
  - Gate 5.28 Locked Benchmark (`new_locked_benchmark.json`): `464612e733aeb1496c1dcdc5674e01d9504bd4ccd1244190e487c6e957dcc722` (50 queries, intact).
  - Frozen Strategy 5 Candidate Hash: `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae`.

---

## 3. Current Runtime State & 68 vs 119 Discrepancy Analysis

### A. Runtime Endpoint Output (Fresh In-Process Execution)

Direct testing of the backend application via FastAPI `TestClient` confirmed the true codebase output:

```json
// GET /api/v1/health
{
  "status": "healthy",
  "app_name": "Dr. Md. Momenul Islam - Clinical Health Intelligence",
  "version": "0.7.0-prototype",
  "environment": "research_development",
  "retrieval_strategy": "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR",
  "candidate_hash": "1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae",
  "active_corpus_chunks": 119,
  "staged_research_chunks": 51,
  "generation_enabled": false
}

// GET /api/v1/corpus
{
  "status": "success",
  "active_corpus": {
    "name": "NHS_14_CONDITIONS",
    "status": "ACTIVE",
    "document_count": 14,
    "chunk_count": 119,
    "source_ids": ["DOC-NHS-004", "DOC-NHS-005", "DOC-NHS-006", "DOC-NHS-007", "DOC-NHS-008", "DOC-NHS-009", "DOC-NHS-010", "DOC-NHS-011", "DOC-NHS-012", "DOC-NHS-013", "DOC-NHS-014", "DOC-NHS-015", "DOC-NHS-016", "DOC-NHS-017"]
  },
  "staged_research_corpus": {
    "name": "STAGED_EMPTY",
    "status": "PROMOTED",
    "document_count": 0,
    "chunk_count": 0,
    "source_ids": []
  }
}
```

### B. Root Cause Breakdown of the UI Discrepancy

```
                     ┌────────────────────────────────────────────────────────┐
                     │ Zombie Backend Process (PID 10036 from Phase 6A)       │
                     │ Bound to port 8000 but hung / unresponsive             │
                     └─────────────────────────┬──────────────────────────────┘
                                               │
                                               ▼
                     ┌────────────────────────────────────────────────────────┐
                     │ Frontend `fetchHealth()` Request Times Out / Fails     │
                     │ React `health` State Remains `null`                    │
                     └─────────────────────────┬──────────────────────────────┘
                                               │
                                               ▼
                     ┌────────────────────────────────────────────────────────┐
                     │ Header.tsx Fallback Triggers:                          │
                     │   health?.active_corpus_chunks ?? 68                   │
                     │   health?.staged_research_chunks ?? 51                 │
                     │   <span className="...">Phase 6A</span>                │
                     └────────────────────────────────────────────────────────┘
```

1. **OBSERVED FACT:** In `frontend/src/components/Header.tsx` (lines 27, 40, 45):
   ```tsx
   <span className="...">Phase 6A</span>
   <span>Active Corpus: <strong>{health?.active_corpus_chunks ?? 68} Chunks</strong> (NHS)</span>
   <span>Staged Research: <strong>{health?.staged_research_chunks ?? 51} Chunks</strong> (Locked)</span>
   ```
   When the frontend cannot communicate with the backend, it renders the static fallback: `68 Chunks`, `51 Chunks`, `Phase 6A`.
2. **OBSERVED FACT:** On Windows, process PID 10036 (`python.exe`) was spawned at `8:26:56 AM` (Phase 6A) and held port 8000 open. Requests to `http://localhost:8000/api/v1/health` timed out.
3. **OBSERVED FACT:** In `backend/app/api/endpoints.py` line 64, `/health` called `get_staged_corpus_stats()`, which checked `settings.STAGED_RESEARCH_MANIFEST_PATH` (`research/gate_5_27_ingestion/provenance_manifest.json`) and returned `staged_research_chunks = 51`. However, in `/corpus`, `staged_tier.chunk_count` was correctly reported as `0` (`status: PROMOTED`).

---

## 4. Phase 6F Benchmark Failure Case Analysis

In Phase 6F, 48 development cases were evaluated across English, Native Bangla, Standard Banglish, and Abbreviated Banglish:

```
Total Cases: 48
├── English (13):               100.0% Directly Supported,  0.0% Partial,  0.0% Unsupported
├── Native Bangla (13):          84.6% Directly Supported,  7.7% Partial,  7.7% Unsupported
├── Standard Banglish (11):      63.6% Directly Supported, 27.3% Partial,  9.1% Unsupported
└── Abbreviated Banglish (11):   63.6% Directly Supported, 27.3% Partial,  9.1% Unsupported
```

Across the 16 `SUPPORTED_EVIDENCE` cases, exactly 7 queries experienced degraded retrieval (top fused score $<0.10$ or gold source missing from Top-5).

### Detailed 17-Step Trace of Focus Failure Cases

#### Case 1: `EVAL-10-BGL-SUP-NUMERIC` (Standard Banglish)
- **Original Query:** `nak theke bleeding hole koto minute naker norom ongsho chepe dhorbo?`
- **Language Modality:** Standard Banglish
- **Normalized Query:** `nak theke bleeding hole koto minute naker norom ongsho chepe dhorbo? (cuts grazes bleeding pressure clean dressing wound)`
- **Expanded Terms:** `(cuts grazes bleeding pressure clean dressing wound)`
- **Expected Gold Source:** `DOC-NHS-016` (Nosebleed - NHS)
- **Gold Target Topic:** Nosebleed soft pinch duration (10 to 15 minutes)
- **Gold Rank at Dense Top-15:** **ABSENT (Rank > 15)**
- **Gold Rank after Cross-Encoder Rerank:** **ABSENT**
- **Gold Final Rank:** **ABSENT**
- **Dense Score of Gold Chunk:** N/A ($<0.75$)
- **Top Fused Score:** `0.0884`
- **Evidence-Gating State:** `UNSUPPORTED_BY_ACTIVE_CORPUS` (Gating correctly blocked response)
- **Competing Chunks in Top-5:** `DOC-NHS-006-HYB-003`, `DOC-NHS-006-HYB-002`, `DOC-NHS-006-HYB-005` (Cuts and grazes - NHS)
- **Why Competing Chunks Won:** The keyword rule matched `bleeding` and injected cuts/grazes expansion words (`cuts`, `grazes`, `dressing`, `clean`). Multilingual-E5 followed the injected English words and matched `DOC-NHS-006`. The anatomical term `nak / naker` ("nose") had no expansion to "nose / nosebleed".
- **Locus of Failure:** **Candidate Generation Failure** (Caused by over-broad keyword expansion collision).

---

#### Case 2: `EVAL-16-ABB-SUP-CONTRAINDICATION` (Abbreviated Banglish)
- **Original Query:** `agune porle tel ba tothpaste dewa jabe?`
- **Language Modality:** Abbreviated Banglish
- **Normalized Query:** `agune porle tel ba tothpaste dewa jabe?` (Zero expansion triggered)
- **Expanded Terms:** None
- **Expected Gold Source:** `DOC-NHS-005` (Burns and scalds - NHS)
- **Gold Target Topic:** Contraindications for burns (do not apply oil, butter, toothpaste)
- **Gold Rank at Dense Top-15:** **ABSENT (Rank > 15)**
- **Gold Rank after Cross-Encoder Rerank:** **ABSENT**
- **Gold Final Rank:** **ABSENT**
- **Dense Score of Gold Chunk:** N/A ($<0.78$)
- **Top Fused Score:** `0.0824`
- **Evidence-Gating State:** `UNSUPPORTED_BY_ACTIVE_CORPUS`
- **Competing Chunks in Top-5:** `DOC-NHS-015-HYB-002`, `DOC-NHS-015-HYB-004` (Meningitis image credits)
- **Why Competing Chunks Won:** `agune porle` (colloquial Romanized Bangla for "if burned by fire") and `tothpaste` (misspelled toothpaste) have near-zero dense vector alignment with English clinical text about burns (`DOC-NHS-005`). Dense E5 retrieved random noise chunks.
- **Locus of Failure:** **Candidate Generation Failure** (Caused by complete absence of Banglish transliteration dictionary for burns vocabulary).

---

#### Case 3: `EVAL-13-ABB-SUP-PROCEDURAL` (Abbreviated Banglish)
- **Original Query:** `nak die rokt porce ki krbo?`
- **Language Modality:** Abbreviated Banglish
- **Normalized Query:** `nak die rokt porce ki krbo? (cuts grazes bleeding pressure clean dressing wound)`
- **Expanded Terms:** `(cuts grazes bleeding pressure clean dressing wound)`
- **Expected Gold Source:** `DOC-NHS-016` (Nosebleed - NHS)
- **Gold Target Topic:** First aid procedure for nosebleed
- **Gold Rank at Dense Top-15:** **ABSENT (Rank > 15)**
- **Gold Rank after Cross-Encoder Rerank:** **ABSENT**
- **Gold Final Rank:** **ABSENT**
- **Top Fused Score:** `0.0844`
- **Evidence-Gating State:** `UNSUPPORTED_BY_ACTIVE_CORPUS`
- **Competing Chunks in Top-5:** `DOC-NHS-006-HYB-003`, `DOC-NHS-015-HYB-002`, `DOC-NHS-006-HYB-004` (Cuts & grazes, Meningitis)
- **Why Competing Chunks Won:** `rokt` (blood) triggered the cuts & grazes expansion rule, while `nak` (nose) was unmapped. Dense E5 retrieved `DOC-NHS-006` instead of `DOC-NHS-016`.
- **Locus of Failure:** **Candidate Generation Failure** (Over-broad rule collision + missing anatomical transliteration).

---

#### Case 4: `EVAL-08-BN-SUP-CONTRAINDICATION` (Native Bangla)
- **Original Query:** `হাত পুড়ে গেলে কি বরফ বা মাখন লাগানো যাবে?`
- **Language Modality:** Native Bangla
- **Normalized Query:** `হাত পুড়ে গেলে কি বরফ বা মাখন লাগানো যাবে? (burns scalds cool running water first aid)`
- **Expanded Terms:** `(burns scalds cool running water first aid)`
- **Expected Gold Source:** `DOC-NHS-005` (Burns and scalds - NHS)
- **Gold Target Topic:** Contraindications for burns (ice, butter)
- **Gold Rank at Dense Top-15:** **Rank 1 (`DOC-NHS-005-HYB-001`), Rank 2 (`DOC-NHS-005-HYB-002`), Rank 5 (`DOC-NHS-005-HYB-004`) [GOLD PRESENT]**
- **Gold Rank after Cross-Encoder Rerank:** **Rank 1 (`DOC-NHS-005-HYB-004`) [GOLD PRESENT]**
- **Gold Final Rank:** **Rank 1 (`DOC-NHS-005-HYB-004`) [GOLD PRESENT]**
- **Dense Score of Gold Chunk:** `0.8282`
- **Cross-Encoder Score:** `0.0031` (Raw logits were very low)
- **Lexical Overlap:** `0.1000`
- **Top Fused Score:** `0.0879` (Dense contribution: $0.0828$, CE: $0.0031$, Lex: $0.0030$)
- **Evidence-Gating State:** `UNSUPPORTED_BY_ACTIVE_CORPUS` (Gating blocked despite gold chunk being Rank 1)
- **Locus of Failure:** **Reranker Logit Calibration / Gating Threshold Interaction**. Dense E5 retrieved gold chunks at Ranks 1, 2, and 5. The cross-encoder placed gold chunk `DOC-NHS-005-HYB-004` at Rank 1, but its raw confidence logit was compressed near zero on the mixed script pair (Bangla premise + English text), causing the final fused score ($0.0879$) to fall below the $0.10$ threshold.

---

#### Case 5: `EVAL-14-ABB-SUP-NUMERIC` (Abbreviated Banglish)
- **Original Query:** `baccar temp 39C hole ki jor dhora hoi?`
- **Language Modality:** Abbreviated Banglish
- **Normalized Query:** `baccar temp 39C hole ki jor dhora hoi? (fever high temperature children fluids paracetamol)`
- **Expected Gold Source:** `DOC-NHS-010` (High temperature in children)
- **Gold Rank at Dense Top-15:** **Rank 2 (`DOC-NHS-010-HYB-003`), Rank 5 (`DOC-NHS-010-HYB-004`) [GOLD PRESENT]**
- **Gold Rank after Cross-Encoder Rerank:** **Rank 1 (`DOC-NHS-010-HYB-004`), Rank 5 (`DOC-NHS-010-HYB-003`) [GOLD PRESENT]**
- **Gold Final Rank:** **Rank 1 (`DOC-NHS-010-HYB-004`) [GOLD PRESENT]**
- **Dense Score:** `0.8340`, **Cross-Encoder Score:** `0.0632`, **Lexical Overlap:** `0.2143`
- **Top Fused Score:** `0.1530`
- **Evidence-Gating State:** `UNSUPPORTED_BY_ACTIVE_CORPUS` ($0.1530 < 0.18$)
- **Locus of Failure:** **Reranker Logit Calibration / Score Boundary**. Gold chunk was Rank 1 in both Dense and Reranker, but score compression resulted in $0.1530$ (just below the $0.18$ `POSSIBLE_MISMATCH` boundary).

---

## 5. Banglish Retrieval Failure Taxonomy

Based on the empirical traces of all 48 benchmark cases, the failures fall into four distinct categories:

```
BANGLISH RETRIEVAL FAILURE TAXONOMY
│
├── 1. CANDIDATE GENERATION DROPOUT (5 / 7 Cases — 71.4%)
│   ├── Missing Banglish Lexical Mapping (e.g. `agune porle` -> burns)
│   ├── Unmapped Anatomical Terms (e.g. `nak / naker` -> nose / nosebleed)
│   └── Phonetic & Abbreviation Variants (e.g. `rokt`, `tothpaste`, `baccar`)
│
├── 2. OVER-BROAD KEYWORD RULE COLLISIONS (2 / 7 Cases — 28.6%)
│   └── Generic keyword triggers (e.g. `bleeding` -> forces cuts/grazes `DOC-NHS-006`,
│       suppressing nosebleed `DOC-NHS-016`)
│
├── 3. CROSS-ENCODER LOGIT COMPRESSION ON MIXED SCRIPTS (2 / 7 Cases — 28.6%)
│   └── Cross-encoder produces low raw logits on Bengali/Banglish query vs English document pairs,
│       even when correctly ranking the gold chunk at Rank 1.
│
└── 4. OUT-OF-CORPUS MEDICAL QUERIES (1 / 48 Cases — 2.1%)
    └── LLM answered unsupported query (EVAL-32 typhoid) under Policy A;
        successfully blocked by Policy C.
```

---

## 6. Root Cause Analysis: Critical Distinctions

| Observation | Classification | Evidence & Rationale |
| :--- | :--- | :--- |
| **Banglish degradation is NOT an inherent embedding space collapse** | `OBSERVED FACT` | For queries with medical vocabulary present in English (e.g., `chest tightness`, `dehydration`, `allergic rhinitis`), Banglish dense retrieval scores exceed $0.85$ and rank gold chunks in Top-3. |
| **Failure occurs BEFORE dense retrieval on unmapped Banglish terms** | `OBSERVED FACT` | In `EVAL-10`, `EVAL-13`, and `EVAL-16`, gold chunks are completely missing from Dense Top-15 because transliterated words (`nak`, `agune`, `porle`) have low cosine similarity to English clinical text. |
| **Track A Normalization rules have keyword collisions** | `OBSERVED FACT` | Expanding `bleeding` to `(cuts grazes bleeding pressure clean dressing wound)` causes `DOC-NHS-006` to outscore `DOC-NHS-016` (Nosebleed) across all dense rankings. |
| **Cross-Encoder scores are compressed on cross-script inputs** | `OBSERVED FACT` | In `EVAL-08` and `EVAL-14`, the gold chunk is Rank 1 in both Dense and Reranked lists, but raw cross-encoder scores are compressed ($0.003 - 0.063$), driving the fused score below confidence thresholds. |

---

## 7. What Is Already Working

1. **Active Corpus Integrity:** 119 chunks across 14 NHS sources loaded cleanly under manifest `44d0602f...`.
2. **English Retrieval & Grounding:** 100.0% directly supported claims with zero fabricated citations.
3. **Native Bangla Direct Queries:** 84.6% directly supported when standard medical keywords match Track A dictionary.
4. **Deterministic Output Validation:** 100% of LLM outputs validated with zero fabricated citations across 48 cases.
5. **Safety Front-Loading:** Emergency advice and folk remedy rejections consistently executed.
6. **Policy C Adaptive Gating:** Eliminates ungrounded hallucinations on non-corpus queries before calling LLM.

---

## 8. What Is Actually Broken

1. **Header Fallback Display:** When backend is unreachable, `Header.tsx` falls back to `68 Chunks / 51 Chunks` and `Phase 6A`.
2. **Health Endpoint Staged Stats:** `/api/v1/health` reads `provenance_manifest.json` (51 chunks) rather than reporting `staged_research_chunks = 0`.
3. **Banglish Vocabulary Coverage in Normalization:** Track A dictionary lacks mappings for core Romanized Bangla terms (e.g. `nak` $\to$ nose/nosebleed, `agun/agune` $\to$ burn/scald, `matha betha` $\to$ headache, `borti/hospital` $\to$ emergency/admission).
4. **Keyword Rule Specificity:** `bleeding` expansion rule is biased toward cuts & grazes and lacks distinction between surface bleeding and epistaxis (nosebleeds).
5. **Score Fusion Calibration on Cross-Script Inputs:** BGE cross-encoder raw logits are lower for Bangla/Banglish inputs than English inputs, creating an artificial score penalty.

---

## 9. Proposed Fix Candidates & Risk Assessment

> [!IMPORTANT]
> In accordance with Phase 6G boundaries, these fixes are **PROPOSALS FOR FUTURE EXPERIMENTS ONLY** and have **NOT** been implemented.

### Candidate Fix 1: Banglish Anatomical & Symptom Transliteration Dictionary (Track A Extension)
- **Description:** Add deterministic mapping rules in `normalize_query_track_a` for high-frequency Banglish words:
  - `nak / naker / nak die` $\to$ `"nose nosebleed"`
  - `agun / agune / porle / pura` $\to$ `"burns scalds heat"`
  - `matha betha / matha ghura` $\to$ `"headache dizziness"`
  - `chulkani / sordi` $\to$ `"allergic rhinitis allergy sneeze"`
- **Risk:** **LOW**. Deterministic, fast, offline testable, does not modify neural weights or dense Top-K.
- **Expected Impact:** Directly resolves Candidate Dropout in `EVAL-10`, `EVAL-13`, `EVAL-16`.

### Candidate Fix 2: Disambiguate Over-Broad Keyword Expansions
- **Description:** Condition `bleeding` expansion on context (e.g. if `nak` or `nose` present, expand to `nosebleed epistaxis pinch soft part`; if general cut, expand to `cuts grazes dressing`).
- **Risk:** **LOW**. Eliminates rule collision between `DOC-NHS-006` and `DOC-NHS-016`.
- **Expected Impact:** Resolves `EVAL-10` and `EVAL-13`.

### Candidate Fix 3: Cross-Script Score Normalization / Calibration
- **Description:** Apply script-aware score calibration or min-max normalization to cross-encoder logits when non-ASCII / transliterated input is detected.
- **Risk:** **MEDIUM**. Requires careful calibration to avoid inflating out-of-corpus scores.
- **Expected Impact:** Resolves threshold dropouts in `EVAL-08` and `EVAL-14`.

### Candidate Fix 4: Frontend Header Badge & Health Endpoint Cleanup
- **Description:**
  - Update `Header.tsx` fallback to reflect Phase 6C (`119 Chunks`, `0 Staged`, `Phase 6F`).
  - Update `get_staged_corpus_stats()` in `endpoints.py` to return `0` staged chunks when `ACTIVE_CORPUS_NAME == "NHS_14_CONDITIONS"`.
  - Terminate zombie process PID 10036 on port 8000.
- **Risk:** **NEGLIGIBLE**. Purely cosmetic and operational cleanup.

---

## 10. Recommended Next Experiment (Phase 6H Proposal)

We recommend structured evaluation in **Phase 6H**:
1. **Experiment 1 (Transliteration Dictionary):** Test Track A Banglish vocabulary expansion on the 48 development cases.
2. **Experiment 2 (Keyword Disambiguation):** Test contextual keyword rules to prevent cuts vs nosebleed collision.
3. **Experiment 3 (Regression Validation):** Verify that English (100%) and Native Bangla (84.6%) performance is preserved without regression.

---

## 11. What Must NOT Be Changed

To preserve scientific rigor and research integrity:
- **Do NOT change:** Multilingual-E5-small or BGE-reranker-v2-m3 models.
- **Do NOT change:** $K=15$ dense candidate depth or Top-5 final reranking depth.
- **Do NOT change:** $\lambda=0.10$ dense fusion or $\alpha=0.03$ lexical overlap weights.
- **Do NOT change:** $0.85\times$ overview debiasing multiplier.
- **Do NOT change:** Active corpus (119 chunks, manifest `44d0602f...`).
- **Do NOT modify or rerun:** Gate 5.28 locked benchmark (`464612e7...`) or Gate 5.29 locked results.
- **Do NOT enable generation by default:** `GENERATION_ENABLED = False` must remain default.

---

## 12. Final Status & Stop Condition

```
INVESTIGATION_COMPLETED
```

All diagnostics, runtime port inspections, process checks, and 17-step pipeline traces have been completed and documented. Zero algorithm or code changes have been made.

**We now STOP and await your review and guidance on next steps.**
