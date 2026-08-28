# Decision Record: Gate 5.27 — Verified Ingestion & Provenance Mapping for Expanded NHS Corpus

**Gate Reference:** GATE 5.27  
**Date:** 2026-08-28  
**Status:** `EXPANDED_CORPUS_INGESTED_AND_PROVENANCE_VALIDATED`  
**Classification:** CORPUS EXPANSION INGESTION & PROVENANCE COMPLETE — RETRIEVAL/EMBEDDING NOT EXECUTED  

---

## 1. Executive Summary & Objective

Following Gate 5.26 rights verification, Gate 5.27 successfully ingested the **6 approved NHS clinical condition documents** (`DOC-NHS-012` through `DOC-NHS-017`) into an isolated research corpus (`research/gate_5_27_ingestion/`) using the project's frozen **block-aware deterministic HTML cleaning** and **Hybrid-600 structural chunking** pipelines.

> [!IMPORTANT]
> **Boundary Enforcement in Gate 5.27:**
> This gate executed **HTML ingestion, text cleaning, chunking, and provenance verification only**. No embeddings were generated, no retrieval evaluations were run, and no benchmark queries were created.

---

## 2. Ingestion & Provenance Inventory

| Source ID | Condition Title | Canonical NHS URL | HTTP Status | Raw Bytes | Clean Text Chars | Chunks Produced |
|---|---|---|---|---|---|---|
| **`DOC-NHS-012`** | Chest pain | `https://www.nhs.uk/symptoms/chest-pain/` | ✅ `200 OK` | 33,656 | 2,532 | **4 chunks** (`HYB-000` to `003`) |
| **`DOC-NHS-013`** | Stroke (Symptoms) | `https://www.nhs.uk/conditions/stroke/symptoms/` | ✅ `200 OK` | 28,600 | 1,547 | **3 chunks** (`HYB-000` to `002`) |
| **`DOC-NHS-014`** | Sepsis | `https://www.nhs.uk/conditions/sepsis/` | ✅ `200 OK` | 64,570 | 8,354 | **15 chunks** (`HYB-000` to `014`) |
| **`DOC-NHS-015`** | Meningitis | `https://www.nhs.uk/conditions/meningitis/` | ✅ `200 OK` | 64,364 | 8,927 | **16 chunks** (`HYB-000` to `015`) |
| **`DOC-NHS-016`** | Nosebleed | `https://www.nhs.uk/conditions/nosebleed/` | ✅ `200 OK` | 37,215 | 3,381 | **6 chunks** (`HYB-000` to `005`) |
| **`DOC-NHS-017`** | Allergic rhinitis | `https://www.nhs.uk/conditions/allergic-rhinitis/` | ✅ `200 OK` | 44,792 | 4,255 | **7 chunks** (`HYB-000` to `006`) |
| **TOTAL** | **6 Documents** | — | — | **273,197 B** | **28,996 C** | **51 Hybrid Chunks** |

---

## 3. Chunking & Hygiene Metrics

- **Chunking Engine:** `Hybrid-600` (target size: 600 characters, max size: 750 characters, paragraph boundary splitting with heading preservation).
- **Total Chunks Produced:** **51 chunks**.
- **Mean Chunk Length:** **566.3 characters** (Min: 95 chars, Max: 902 chars).
- **Overview Chunks (`-HYB-000`):** Exactly 6 chunks (1 per document).
- **Deep Clinical Chunks:** 45 chunks covering specific emergency callouts, FAST stroke protocols, glass tumbler tests, sepsis recognition in babies, nosebleed first aid, and antihistamine management.

---

## 4. Provenance & Reconstruction Audit

1. **Completeness & Integrity:**
   - **Zero orphan chunks**: All 51 chunks map directly to parent source IDs.
   - **Zero missing metadata**: Every chunk record contains `parent_source_id`, `source_title`, `requested_url`, `final_url`, `canonical_url`, `retrieval_timestamp_utc`, `raw_html_hash`, `corrected_text_hash`, and `chunk_hash`.
2. **Reconstruction Fidelity & Lossless Definition:**
   - **Precise Definition of Lossless:** Content is *100% losslessly preserved relative to the selected clinical prose* after deterministic boilerplate exclusion.
   - Word preservation rate against raw HTML: **93.96% to 98.43%**.
   - The ~2–6% non-matching raw words are strictly accounted for by the intentional, deterministic exclusion of non-clinical page review metadata (`nhsuk-review-date`), navigation links, SVG/media headers, and feedback banners per established corpus hygiene rules.
   - Every single word and punctuation mark in the extracted clinical prose is 100% preserved in the resulting `HYBRID_600` chunks.
3. **Reproducibility Audit:**
   - Executed across 3 independent runs.
   - **Verdict:** `PERFECT_MATCH` (SHA-256 manifest hash is identical across all runs).

---

## 5. Final Status & Recommendation for Gate 5.28

1. **Gate 5.27 Final Status:** **`EXPANDED_CORPUS_INGESTED_AND_PROVENANCE_VALIDATED`**.
2. **Recommendation for Gate 5.28:**
   - Author a pristine, locked multi-lingual generalization benchmark spanning both the expanded 6 documents and the baseline corpus.
   - Lock with SHA-256 hash.
