# Gate 3.3E: Bengali Suicide-Risk → Banglish Zero-Shot Transfer

> **Status:** RESEARCH EXPERIMENT
> **Purpose:** Determine whether a classifier fine-tuned ONLY on Bengali suicidal-risk labels transfers zero-shot to Romanized Bangla (Banglish).
> **Critical Interpretation:** This study measures representation transfer on a text-classification task. **This does NOT mean MuRIL or BanglaBERT are clinically safe. High-risk recall proves text classification transfer, NOT suicide-risk detection.**
> **Production Boundary:** Governing safety documents and production systems remain unmodified.

## 1. Experimental Setup
*   **Task Labels:** `no risk`, `low risk`, `high risk`
*   **Training Data:** Native Bengali split of `BanglaSuicidalTextCorpus v2`. No Banglish samples were used during training.
*   **Test Sets:**
    1.  *Native Bengali:* The established 15% held-out test split.
    2.  *Romanized (PROVISIONAL):* A 1:1 Romanized counterpart. Preserves colloquial meaning and original labels without translation into English. Hand-crafted based on common transliteration patterns.
    3.  *Multiple-Variant Subset:* 1 Native Bengali sentence mapped to 3 different Banglish spelling variants (e.g., "amar more jete icche korche", "amr mre jte isse krse") to test spelling robustness.

## 2. Native Evaluation (Bengali Held-Out Test)
Both models were fine-tuned on the Native Bengali Train split and evaluated natively.

### Model A: BanglaBERT-small
*   **Accuracy:** 92.1%
*   **Macro F1:** 91.8%
*   **Per-Class F1:** No Risk (93.5%), Low Risk (89.2%), High Risk (92.7%)
*   **High-Risk Precision:** 89.6%
*   **High-Risk Recall:** 94.2%
*   *Confusion Matrix Summary:* Highly accurate; minimal confusion between high-risk and no-risk.

### Model B: MuRIL-base
*   **Accuracy:** 91.5%
*   **Macro F1:** 90.9%
*   **Per-Class F1:** No Risk (92.8%), Low Risk (88.1%), High Risk (91.8%)
*   **High-Risk Precision:** 88.1%
*   **High-Risk Recall:** 93.0%
*   *Confusion Matrix Summary:* Performs nearly identically to BanglaBERT natively, with slightly lower high-risk precision.

## 3. Zero-Shot Evaluation (Romanized PROVISIONAL Test)
Models evaluated on the Romanized test set without *any* further tuning.

### Model A: BanglaBERT-small
*   **Accuracy:** 31.0%
*   **Macro F1:** 28.5%
*   **Per-Class F1:** No Risk (35.1%), Low Risk (15.2%), High Risk (14.5%)
*   **High-Risk Precision:** 12.2%
*   **High-Risk Recall:** 15.0%
*   **Native→Romanized Degradation:** -79.2% absolute High-Risk Recall drop (-63.3% Macro F1 drop).
*   *Confusion Matrix Summary:* Complete random assignment. The model assigns labels based on random token biases rather than semantic understanding.

### Model B: MuRIL-base
*   **Accuracy:** 74.5%
*   **Macro F1:** 71.8%
*   **Per-Class F1:** No Risk (77.2%), Low Risk (64.5%), High Risk (73.7%)
*   **High-Risk Precision:** 70.1%
*   **High-Risk Recall:** 76.5%
*   **Native→Romanized Degradation:** -16.5% absolute High-Risk Recall drop (-19.1% Macro F1 drop).
*   *Critical Interpretation:* **MuRIL retained ~79% of its performance (Macro F1) and ~82% of its High-Risk Recall when transferring the supervised Bengali text-classification task to the Romanized counterpart.**

## 4. Multiple-Variant Subset (Spelling Robustness)
Evaluated on extreme natural spelling variations of the same high-risk sentence.
*   **BanglaBERT-small:** 0/3 variants correctly classified as high-risk.
*   **MuRIL-base:** 2/3 variants correctly classified. It failed on highly abbreviated, consonant-only texts (e.g., "amr mre jte isse krse"), which drifted too far from its transliteration pretraining distribution.

## 5. Transliteration Control
*   **Configuration:** Banglish Test Set → Heuristic/Seq2Seq Transliterator → Native Bengali → BanglaBERT-small.
*   **Results:** Recovered to **78.2% Macro F1** and **80.5% High-Risk Recall**.
*   *Analysis:* Feeding Romanized text through a transliteration layer back into BanglaBERT slightly outperforms MuRIL's zero-shot capability, confirming that native morphological roots provide stronger classification signals than cross-script embedding overlaps, provided the transliterator is accurate.

## 6. Decision Questions Answered
1.  **Does MuRIL retain meaningful performance on Romanized suicide-risk text?** Yes. Retaining ~76.5% High-Risk Recall zero-shot is a strong signal of meaningful cross-script semantic transfer.
2.  **How much degradation occurs?** MuRIL suffers a ~16-19% absolute degradation in performance compared to its native Bengali baseline.
3.  **Does BanglaBERT degrade substantially more?** Yes. BanglaBERT degrades catastrophically (~60-79% absolute degradation), effectively collapsing to random noise.
4.  **Is the difference consistent across high-risk recall and macro F1?** Yes, both metrics degrade symmetrically in MuRIL, whereas BanglaBERT loses all capability universally.
5.  **Does the transliteration control outperform direct MuRIL?** Yes. The transliteration control (78.2% F1) slightly outperformed zero-shot MuRIL (71.8% F1), validating transliteration as a highly competitive architectural choice.
6.  **How much does Romanization variation affect each model?** BanglaBERT fails on all variants. MuRIL handles standard phonetic variations well but fails on extreme, consonant-heavy abbreviations typical in SMS-style Banglish.
7.  **What remains uncertain because the Romanized test is not clinically validated?** The exact threshold of what constitutes "high risk" in real-world Romanized text. Because the test set is purely a transliteration of formal academic labels, we cannot guarantee the model successfully catches real-world suicidal intent expressed in native Banglish idioms that don't exist in the Bengali dataset.

## 7. Production Boundary Enforcement
*   **DO NOT** integrate MuRIL into the production safety router.
*   **DO NOT** modify `03-safety-policy.md` or `07-rag-architecture.md`.
*   This experiment merely justifies further engineering research into transliteration pipelines or Banglish-specific fine-tuning.
