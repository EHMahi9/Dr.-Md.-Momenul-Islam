# Decision Record: Gate 5.26 — NHS Source Discovery, Rights Verification & Corpus Expansion

**Gate Reference:** GATE 5.26  
**Date:** 2026-08-28  
**Status:** `SOURCE_EXPANSION_APPROVED`  
**Classification:** SOURCE DISCOVERY, RIGHTS VERIFICATION & DIVERSITY COMPLETE  

---

## 1. Executive Summary & Objective

In accordance with Gate 5.25 findings that all 8 existing corpus documents have been exposed to previous query evaluations, Gate 5.26 performed the **discovery, HTTP status verification, rights auditing, and clinical diversity analysis** for **6 new NHS clinical condition documents** (`DOC-NHS-012` through `DOC-NHS-017`).

> [!IMPORTANT]
> **Boundary Enforcement in Gate 5.26:**
> This gate conducted **source discovery and rights verification only**. No document ingestion, chunking, embedding, retrieval, reranking, or query benchmarking was performed.

---

## 2. Verified Active Candidate Sources (Primary Expansion Set)

| Proposed ID | Clinical Condition | Canonical NHS URL | HTTP Status | Clinical Domain |
|---|---|---|---|---|
| **`DOC-NHS-012`** | Chest pain | `https://www.nhs.uk/symptoms/chest-pain/` | ✅ `200 OK` | Cardiovascular Emergency & Triage |
| **`DOC-NHS-013`** | Stroke | `https://www.nhs.uk/conditions/stroke/` | ✅ `200 OK` | Cerebrovascular Emergency (FAST) |
| **`DOC-NHS-014`** | Sepsis | `https://www.nhs.uk/conditions/sepsis/` | ✅ `200 OK` | Critical Care / Systemic Infection |
| **`DOC-NHS-015`** | Meningitis | `https://www.nhs.uk/conditions/meningitis/` | ✅ `200 OK` | Infectious & Neurological Emergency |
| **`DOC-NHS-016`** | Nosebleed | `https://www.nhs.uk/conditions/nosebleed/` | ✅ `200 OK` | ENT First Aid & Epistaxis Protocol |
| **`DOC-NHS-017`** | Allergic rhinitis | `https://www.nhs.uk/conditions/allergic-rhinitis/` | ✅ `200 OK` | Chronic Immunology / Hay Fever |

*Reserve Candidates Documented:*
- `DOC-NHS-018`: *Head injury and concussion* (`https://www.nhs.uk/conditions/head-injury-and-concussion/`, HTTP 200)
- `DOC-NHS-019`: *Insect bites and stings* (`https://www.nhs.uk/conditions/insect-bites-and-stings/`, HTTP 200)

---

## 3. Reuse & Rights Verification (OGL v3.0)

All 6 primary candidate documents reside under the official `www.nhs.uk` domain managed by **NHS England** and are licensed under the **Open Government Licence v3.0 (OGL v3.0)**.

- **Permitted Reuse:** Textual extraction, informational public benefit reuse, research and academic indexing, and derivative hybrid chunking.
- **Mandatory Attribution Clause:**  
  *"Contains information from NHS England, licensed under the current version of the Open Government Licence."*
- **Strict Ingestion Exclusions:**
  1. All NHS official logos, trademarks, and crests must be stripped during HTML parsing.
  2. All third-party copyrighted photography, illustrations, and embedded multimedia must be excluded.
- **Rights Classification for all 6 sources:** `APPROVED_FOR_PLANNED_TEXT_REUSE`.

---

## 4. Clinical Diversity & Domain Disjointness

| Source ID | Condition | Novel Clinical Concepts Introduced | Overlap Risk vs. Existing Corpus (`004`–`011`) |
|---|---|---|---|
| `DOC-NHS-012` | Chest pain | Crushing chest pressure, radiating arm/jaw pain, angina, heart attack emergency triage. | Low — cleanly distinct from respiratory asthma (`004`) and indigestion (`008`). |
| `DOC-NHS-013` | Stroke | FAST protocol (Face drooping, Arm weakness, Speech difficulty, Time to call 999). | Low — distinguishes from general headache pain in `009`. |
| `DOC-NHS-014` | Sepsis | Systemic organ failure signs, mottled/blotchy skin, uncontrollable shivering. | Low — contrasts with isolated paediatric fever in `010` and dehydration in `007`. |
| `DOC-NHS-015` | Meningitis | Stiff neck, non-blanching purpuric rash, tumbler/glass pressure test. | Low — establishes clear distinction from viral fever rashes in `010`. |
| `DOC-NHS-016` | Nosebleed | Forward-leaning posture, soft nasal pinch for 10-15 minutes, ice pack on nose. | Low — distinct from limb wound pressure/dressings in `006`. |
| `DOC-NHS-017` | Allergic rhinitis | Sneezing, itchy watery eyes, non-emergency antihistamines, nasal steroid sprays. | Moderate (Controlled) — tests boundary against critical anaphylaxis in `011`. |

---

## 5. Decision & Recommendation for Next Gates

1. **Gate 5.26 Final Status:** **`SOURCE_EXPANSION_APPROVED`**.
2. **Recommendation for Gate 5.27:**
   - Ingest `DOC-NHS-012` through `DOC-NHS-017` into structured HTML/Markdown provenance manifests using the established hybrid chunking pipeline.
   - Index the new chunks into an expanded corpus.
3. **Recommendation for Gate 5.28:**
   - Construct a pristine, locked multi-lingual generalization benchmark spanning both the new and existing documents.
   - Execute single-shot evaluation of `STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR`.
