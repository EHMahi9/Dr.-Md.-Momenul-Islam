# Decision Record: Phase 6H.1 — Banglish Development Benchmark Target-Source Integrity Audit

**Date:** 2026-08-29  
**Status:** Audit Completed (`PHASE_6H_RESULT_VALID_AFTER_TARGET_CORRECTION`)  
**Corpus State:** 119 Active Chunks across 14 NHS Sources (`DOC-NHS-004` through `DOC-NHS-017`), 0 Staged Chunks  
**Authoritative Manifest:** `research/phase_6C/promoted_corpus_manifest.json` (SHA-256: `44d0602f730d6460e6fefa431bd5c09005b48ce92b47d02832532e5868d4aa58`)

---

## 1. Verified Fact

### Authoritative Active Corpus Provenance
The active production corpus consists strictly of 14 NHS condition sources and 119 chunks loaded via `promoted_corpus_manifest.json`:

| Source ID | Authoritative Document Title | Chunk Count | Valid Clinical Coverage Scope |
| :--- | :--- | :---: | :--- |
| `DOC-NHS-004` | **Asthma** | 18 | Wheezing, inhalers, asthma attack triggers |
| `DOC-NHS-005` | **Burns and scalds** | 5 | Thermal burns, hot water scalds, cooling, cling film |
| `DOC-NHS-006` | **Cuts and grazes** | 7 | Bleeding wounds, cuts, grazes, pressure dressing |
| `DOC-NHS-007` | **Dehydration** | 8 | Fluid loss, oral rehydration salts (ORS), sunken eyes |
| `DOC-NHS-008` | **Diarrhoea and vomiting** | 8 | Loose stools, norovirus, hydration management |
| `DOC-NHS-009` | **Headaches** | 5 | Tension headaches, migraines, pain relief |
| `DOC-NHS-010` | **High temperature (fever) in children** | 7 | Pediatric fever, paracetamol dosage, warning signs |
| `DOC-NHS-011` | **Anaphylaxis** | 10 | Severe allergic reaction, wasp/bee stings, EpiPen |
| `DOC-NHS-012` | **Chest pain** | 4 | Heart attacks, chest pain, **heartburn/indigestion differential** (`HYB-002`) |
| `DOC-NHS-013` | **Symptoms of a stroke** | 3 | FAST protocol, facial drooping, speech weakness |
| `DOC-NHS-014` | **Sepsis** | 15 | Severe infection, blotchy skin, confusion |
| `DOC-NHS-015` | **Meningitis** | 16 | Stiff neck, light sensitivity, purpuric rash |
| `DOC-NHS-016` | **Nosebleed** | 6 | Epistaxis, pinch soft part of nose, lean forward |
| `DOC-NHS-017` | **Allergic rhinitis** | 7 | Hay fever, sneezing, itchy runny nose |

---

## 2. Dataset Error (Audit Findings)

### A. Phase 6G.2 Challenge Dataset Mismatches (`banglish_challenge_dataset.json`)
The audit identified that 8 out of 12 test cases in `research/phase_6G_2_runtime_and_banglish/banglish_challenge_dataset.json` contained target document ID mismatches or referenced out-of-corpus conditions:

1. **`DEV-CHALLENGE-001` (Nosebleed):** Assigned `DOC-NHS-012` (Chest pain) instead of **`DOC-NHS-016` (Nosebleed)**.
2. **`DEV-CHALLENGE-003` (Post-prandial burning chest / heartburn):** Assigned `DOC-NHS-009` (Headaches). The actual corpus text covering post-eating heartburn/indigestion is located in **`DOC-NHS-012-HYB-002` (Chest pain)**.
3. **`DEV-CHALLENGE-005` (Diarrhoea / ORS):** Labeled as "Diarrhoea and vomiting" but mapped to `DOC-NHS-007` (Dehydration). Both `DOC-NHS-007` (ORS) and `DOC-NHS-008` (Diarrhoea) are clinically valid.
4. **`DEV-CHALLENGE-007` (Chickenpox):** Mapped to `DOC-NHS-008` (Diarrhoea and vomiting). Chickenpox does not exist in the 14-condition corpus.
5. **`DEV-CHALLENGE-009` (Conjunctivitis):** Mapped to `DOC-NHS-016` (Nosebleed). Conjunctivitis does not exist in the 14-condition corpus.
6. **`DEV-CHALLENGE-010` (Mouth ulcers):** Mapped to `DOC-NHS-014` (Sepsis). Mouth ulcers does not exist in the 14-condition corpus.
7. **`DEV-CHALLENGE-011` (Insect bites):** Labeled "Insect bites and stings" but mapped to `DOC-NHS-011` (Anaphylaxis). Anaphylaxis covers severe wasp/bee stings.
8. **`DEV-CHALLENGE-012` (Migraine):** Mapped to `DOC-NHS-017` (Allergic rhinitis) instead of **`DOC-NHS-009` (Headaches)**.

### B. Regression Suite Mismatches in `run_banglish_experiment.py`
1. **`REG-EN-006` & `REG-BN-006` (Nosebleed):** Script expected `DOC-NHS-012` (Chest pain) instead of `DOC-NHS-016` (Nosebleed).
2. **`REG-EN-003` & `REG-BN-004` (Measles):** Script expected `DOC-NHS-013` (Stroke), but Measles does not exist in the 14-condition corpus.

---

## 3. Observation

1. **Candidate C's Real Retrieval Behavior Was Underestimated:**
   - In Phase 6H, `DEV-CHALLENGE-001` (`nak diye rokt porle`) correctly retrieved `DOC-NHS-016-HYB-002` (Nosebleed) as Top-1, but was marked as a failure because the script expected `DOC-NHS-012`.
   - In Phase 6H, `DEV-CHALLENGE-003` (`khabar por buk jala pora`) correctly retrieved `DOC-NHS-012-HYB-002` (Chest pain / Heartburn) as Top-1, but was marked as a failure because the script expected `DOC-NHS-009`.
2. **True In-Corpus Accuracy for Candidate C is 77.78% (7/9 Top-1 Hits):**
   - Out of the 9 in-corpus challenge conditions, Candidate C retrieved the correct NHS document at Top-1 for 7 conditions:
     - `DEV-001` (Nosebleed $\rightarrow$ `DOC-NHS-016` Top-1)
     - `DEV-002` (Cuts $\rightarrow$ `DOC-NHS-006` Top-1)
     - `DEV-003` (Chest heartburn $\rightarrow$ `DOC-NHS-012` Top-1)
     - `DEV-004` (Burns $\rightarrow$ `DOC-NHS-005` Top-1)
     - `DEV-005` (Diarrhoea/ORS $\rightarrow$ `DOC-NHS-007` Top-1)
     - `DEV-006` (Pediatric fever $\rightarrow$ `DOC-NHS-010` Top-1)
     - `DEV-008` (Asthma $\rightarrow$ `DOC-NHS-004` Top-1)
   - Only 2 in-corpus cases were not Top-1: `DEV-011` (Anaphylaxis Rank 4) and `DEV-012` (Headache missed due to 'bomi' token routing).

---

## 4. Recalculated Metric Comparison (Ground-Truth In-Corpus N=9)

| Candidate Configuration | Dense Recall@15 | Final Recall@5 | Final Recall@3 | Top-1 Accuracy | MRR |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **CONTROL** (Frozen Track A) | 0.00% | 55.56% (5/9) | 55.56% (5/9) | 44.44% (4/9) | 0.5000 |
| **Candidate A** (Targeted Transliteration) | 0.00% | 66.67% (6/9) | 55.56% (5/9) | 44.44% (4/9) | 0.5278 |
| **Candidate B** (Context Disambiguation) | 0.00% | **88.89% (8/9)** | **88.89% (8/9)** | **77.78% (7/9)** | **0.8148** |
| **Candidate C** (Integrated Hybrid A+B) | 0.00% | **88.89% (8/9)** | **77.78% (7/9)** | **77.78% (7/9)** | **0.8056** |

---

## 5. Hypothesis

The original benchmark author likely created `banglish_challenge_dataset.json` from memory or a draft taxonomy rather than inspecting the authoritative `promoted_corpus_manifest.json`. This introduced systematic doc ID shifts (`DOC-NHS-012` for nosebleed, `DOC-NHS-009` for heartburn, `DOC-NHS-016` for conjunctivitis) and out-of-corpus clinical queries.

---

## 6. Impact

1. **Winner Status Remains Firm:** Candidate C (and Candidate B) remain overwhelmingly superior to CONTROL (Top-1 Accuracy: **77.78% vs 44.44%**, MRR: **0.8056 vs 0.5000**).
2. **Benchmark Integrity Restored:** The corrected dataset is saved at `research/phase_6H_1_benchmark_integrity/corrected_banglish_challenge_dataset.json`.
3. **No Algorithm or Corpus Contamination:** Neither Strategy 5 nor locked holdout gates (Gate 5.28 / Gate 5.29) were touched or modified.

---

## 7. Recommendation & Final Classification

### Classification Decision:
**`B. PHASE_6H_RESULT_VALID_AFTER_TARGET_CORRECTION`**

### Explanation:
The Phase 6H experiment results are empirically valid and Candidate C is genuinely effective. The lower numbers initially reported (50% Top-1) were an artifact of mislabeled test targets. Under true corpus provenance, Candidate C achieves **77.78% Top-1 Accuracy and 88.89% Final Recall@5** on in-corpus Banglish challenge queries with 0% regression on valid control benchmarks.
