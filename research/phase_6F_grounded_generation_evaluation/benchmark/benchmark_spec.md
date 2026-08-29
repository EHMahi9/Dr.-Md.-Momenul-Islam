# Phase 6F Development Grounding Evaluation Benchmark Specification

**Benchmark ID:** `DEVELOPMENT_GROUNDING_EVAL_SET_48`  
**SHA-256 Hash:** `c4603199028cb649617b59d2523bb1a64b92876ffcc899285a946e940257ee61`  
**Total Queries:** 48  
**Human-Authored:** Yes (Zero LLM generation utilized in dataset creation)  
**Creation Date:** 2026-08-29  

---

## 1. Composition & Category Distribution

| Category | Cases | English | Native Bangla | Standard Banglish | Abbreviated Banglish |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SUPPORTED_EVIDENCE** | 16 | 4 | 4 | 4 | 4 |
| **EVIDENCE_PARTIAL_AMBIGUOUS** | 10 | 3 | 3 | 2 | 2 |
| **UNSUPPORTED** | 12 | 3 | 3 | 3 | 3 |
| **SAFETY_SENSITIVE** | 10 | 3 | 3 | 2 | 2 |
| **TOTAL** | **48** | **12** | **12** | **12** | **12** |

---

## 2. Evaluation Intent & Gating Boundaries

1. **SUPPORTED_EVIDENCE (16 items):**  
   Evaluates direct factual retrieval, procedural first aid steps, numeric thresholds (e.g. 38°C fever, 15-30 min cooling), contraindication avoidance (no head tilting in nosebleed), and when-to-seek-help triggers.
2. **EVIDENCE_PARTIAL_AMBIGUOUS (10 items):**  
   Evaluates multi-chunk synthesis, differential ambiguity (asthma vs chest pain), and appropriate handling of missing clinical specifics (recovery duration, post-ICU nutrition).
3. **UNSUPPORTED (12 items):**  
   Evaluates system abstention on hard medical negatives (dengue, malaria, typhoid), non-corpus surgical procedures, and non-medical out-of-domain queries.
4. **SAFETY_SENSITIVE (10 items):**  
   Evaluates immediate emergency front-loading (acute chest pain, stroke FAST signs), refusal to prescribe medication or calculate pediatric antibiotic doses, and explicit warnings against toxic home remedies (cow dung, kerosene, soil).
