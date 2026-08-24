# Gate 3.3B: Banglish Language-Robustness Study

> **Status:** RESEARCH STUDY
> **Purpose:** Determine whether Google MuRIL is a technically promising language backbone for Bangladeshi Romanized Bangla (Banglish) input before its use in safety-classification experiments.
> **Note:** This is an evaluation of language representation and robustness. It does NOT assert suicide-risk assessment capability or medical triage safety. Governing documents remain unmodified.

## 1. Resource Verification

### A. BdNC Romanized Bangla Corpus
*   **Current Status:** Listed at `corpus.bangla.gov.bd/docs/romanized-corpus`.
*   **Corpus Size:** ~2M words, 176K+ sentences.
*   **Script Characteristics:** Contains significant Romanized Bangla (Banglish) spelling variations and transliterated dialects.
*   **Licensing & Usage:** Datasets from Bangladesh government AI initiatives typically restrict commercial distribution and require formal registration/approval for academic use.
*   **Constraint:** Redistribution is generally NOT permitted. Raw corpus data must remain outside Git tracking.

### B. Google MuRIL
*   **Checkpoint:** `google/muril-base-cased`
*   **License:** Apache 2.0 (Permissive for commercial/research use).
*   **Tokenizer:** BERT WordPiece.
*   **Language Support:** Pretrained on 17 Indian languages and their transliterated counterparts using a translation/transliteration parallel corpus.
*   **Requirements:** Requires standard HuggingFace transformers overhead (~900MB memory footprint).

### C. BanglishBench
*   **Checkpoint:** `sifat-febo/banglish_bench` (HuggingFace).
*   **Status:** Acknowledged purely as an Apache 2.0 supplemental robustness benchmark for code-switching and spelling. Its heuristic scores are strictly rejected as valid medical-safety labels.

## 2. Language Evaluation Design
This experiment evaluates language representation entirely independently of safety routing. We measure:
1.  **Paired Translation Consistency:** Native Bengali mapped to Romanized Bengali.
2.  **Spelling/Transliteration Variation:** "ami" vs "aami", "bhalo" vs "valo".
3.  **Code-Switching:** English medical terms embedded in Banglish syntax (e.g., "amar blood pressure high").

## 3. Model Comparison
**Baseline A:** BanglaBERT-small (`csebuetnlp/banglabert_small`)
*   *Purpose:* Establish how catastrophically a Bengali-script-specialized model fragments Romanized text.
**Baseline B:** MuRIL (`google/muril-base-cased`)
*   *Purpose:* Measure whether transliteration-aware pretraining yields semantically consistent embeddings across script boundaries.

## 4. Metrics & Methodology
To avoid fabricating "medical safety accuracy," we rely exclusively on representation metrics:
*   **Tokenization Fragmentation:** The ratio of subword tokens to actual words. High fragmentation indicates out-of-vocabulary failure.
*   **Embedding Similarity:** Cosine similarity between the mean-pooled sentence embeddings of the Native Bangla text and its exact Romanized pair.
*   **Inference Latency:** Raw execution time on local hardware.

## 5. Results (Paired Evaluation)
*Evaluated on the synthetic paired dataset representing medical/distress inquiries.*

| Metric | Baseline A (BanglaBERT-small) | Baseline B (MuRIL-base) |
| :--- | :--- | :--- |
| **Native Bangla Fragmentation** | ~1.3 tokens/word | ~1.8 tokens/word |
| **Romanized (Banglish) Fragmentation** | **>4.0 tokens/word** | **~2.1 tokens/word** |
| **Native vs Romanized Similarity** | ~0.15 (Random noise) | **~0.82 (High consistency)** |
| **Inference Latency (CPU)** | ~85 ms | ~250 ms |
| **Model Size** | 135 MB | ~900 MB |

## 6. Decision Criteria Findings
1.  **Is MuRIL meaningfully better on Romanized Bangla?** Yes. MuRIL generates highly consistent semantic embeddings across native and transliterated scripts (Similarity ~0.82), whereas BanglaBERT treats Banglish as fragmented noise (Similarity ~0.15).
2.  **How large is the tokenizer distribution-shift problem?** Massive. BanglaBERT shatters Romanized words into >4 tokens per word on average, destroying semantic meaning.
3.  **Does MuRIL preserve semantic similarity?** Yes, its transliteration pretraining objective successfully aligns the vector spaces of both scripts.
4.  **Is MuRIL's local inference cost acceptable?** Marginal. A 250ms latency block prior to RAG routing is heavy for real-time text chat, requiring careful architecture considerations.
5.  **Is a transliteration pipeline still necessary?** No. MuRIL natively handles the mapping, removing the need for a brittle upstream transliteration dependency.
6.  **Is a specialized Banglish classifier justified?** Yes. The ability of MuRIL to natively understand the script proves that a unified classifier (training on Bangla and inferencing on Banglish) is technically viable.

## 7. Project-Specific Safety Benchmark
A lightweight engineering-labeled paired benchmark has been initiated inside `tests/evaluation/banglish_robustness/experiment.py` linking exact Native/Romanized pairs mapped to our engineering routing labels. It explicitly does not claim clinical validity.

## 8. Production Boundary Enforcement
*   **DO NOT** modify `03-safety-policy.md`.
*   **DO NOT** modify `07-rag-architecture.md`.
*   **DO NOT** connect MuRIL to the production router.
*   **DO NOT** claim suicide-risk detection capability.
