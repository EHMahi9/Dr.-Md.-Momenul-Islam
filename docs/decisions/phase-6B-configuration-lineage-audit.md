# Decision Record: Phase 6B — Non-Evaluative Configuration Lineage Audit

**Phase Reference:** PHASE 6B (STEP 0)  
**Date:** 2026-08-29  
**Status:** `CONFIGURATION_LINEAGE_VERIFIED_AND_RECONCILED`  
**Classification:** NON-EVALUATIVE ARTIFACT & HASH PROVENANCE AUDIT  

---

## 1. Executive Summary & Problem Statement

Prior to Gate 5.29, documentation and backend config referenced the SHA-256 hash:
$$\text{Hash A: } \mathbf{07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736}$$
During Gate 5.29 pre-run integrity verification, the direct cryptographic hash of the candidate artifact (`strategy_5_dev_candidate_configuration.json`) was recorded as:
$$\text{Hash B: } \mathbf{1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae}$$

This non-evaluative audit investigated the exact provenance, artifact source, and semantic differences between these two hashes without executing any benchmark evaluations.

---

## 2. Lineage Investigation & Findings

### Finding 1: Origin of Hash `07f031da...`
- **Candidate:** `STRATEGY_2_TRACK_A_NORM_ONLY` (Frozen in Gate 5.21).
- **Architecture:** Track A Normalization + Multilingual E5-Small ($K=15$) + BGE-Reranker-v2-m3 + $0.85\times$ Overview Debiasing.
- **Fusion:** $\lambda = 0.0, \alpha = 0.0$ (No dense or lexical score fusion).
- **History:** This was the baseline candidate evaluated in Gate 5.22, Gate 5.23, and retained as the control baseline in Gate 5.24.

### Finding 2: Origin of Hash `1cc216db...`
- **Candidate:** `STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR` (Selected in Gate 5.24.1).
- **Architecture:** Track A Normalization + Multilingual E5-Small ($K=15$) + BGE-Reranker-v2-m3 + $0.85\times$ Overview Debiasing + **Dual-Anchor Score Fusion** ($\lambda = 0.10, \alpha = 0.03$).
- **Artifact File:** `research/gate_5_24_reranker_development_research/candidate/strategy_5_dev_candidate_configuration.json`.
- **Direct SHA-256:** `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae`.

### Finding 3: Runtime Application Alignment
- In Phase 6A, the backend code implemented Strategy 5's dual-anchor fusion formula ($\text{final\_score} = \text{rerank} + 0.10 \times \text{dense} + 0.03 \times \text{overlap}$), but the config constant `FROZEN_CANDIDATE_SHA256` had retained the legacy string `07f031da...` from the earlier Gate 5.21 template.
- Gate 5.29 dynamically hashed the actual `strategy_5_dev_candidate_configuration.json` file, revealing the true SHA-256 digest `1cc216db...`.
- **Verdict:** The runtime application and Gate 5.29 evaluation are **100% semantically and numerically aligned** with `STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR`.

---

## 3. Parameter Comparison Matrix

| Component | Baseline Hash (`07f031da...`) | Authoritative Strategy 5 Hash (`1cc216db...`) | Backend Runtime Implementation | Parity Status |
|---|---|---|---|---|
| **Strategy Name** | `STRATEGY_2_TRACK_A_NORM_ONLY` | `STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR` | `STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR` | ✅ **MATCH** |
| **Dense Model** | `intfloat/multilingual-e5-small` | `intfloat/multilingual-e5-small` | `intfloat/multilingual-e5-small` | ✅ **MATCH** |
| **Candidate Depth ($K$)** | `15` | `15` | `15` | ✅ **MATCH** |
| **Cross-Encoder Model** | `BAAI/bge-reranker-v2-m3` | `BAAI/bge-reranker-v2-m3` | `BAAI/bge-reranker-v2-m3` | ✅ **MATCH** |
| **Overview Multiplier** | `0.85x` (on `-HYB-000`) | `0.85x` (on `-HYB-000`) | `0.85x` (on `-HYB-000`) | ✅ **MATCH** |
| **Dense Fusion ($\lambda$)** | `0.0` | `0.10` | `0.10` | ✅ **MATCH** |
| **Lexical Overlap ($\alpha$)** | `0.0` | `0.03` | `0.03` | ✅ **MATCH** |
| **Concept Dictionaries** | 9 Rules | 9 Rules | 9 Rules | ✅ **MATCH** |
| **Final Context Top-$K$** | 5 | 5 | 5 | ✅ **MATCH** |

---

## 4. Decision & Reconciliation Action

1. **Reconciliation:** The authoritative frozen SHA-256 hash for `STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR` is formally established as **`1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae`**.
2. **Configuration Update:** `backend/app/core/config.py` and backend test assertions are updated to reference `1cc216db...` to eliminate legacy ambiguity.
3. **Artifact Integrity:** `strategy_5_dev_candidate_configuration.json` remains permanently immutable.
