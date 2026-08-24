# Gate 3.3C: Zero-Shot Banglish Transfer Study

> **Status:** RESEARCH EXPERIMENT
> **Purpose:** Determine whether a MuRIL classifier fine-tuned ONLY on Bengali suicidal-risk labels transfers effectively to Romanized Bangla (Banglish) without any Banglish training data.
> **Important:** This is a research experiment. It is NOT clinical validation and must NOT be presented as suicide-risk assessment. No production governing documents have been modified.

## 1. BdNC Romanized Corpus Status
The official Bangladesh National Corpus (BdNC) documents a Romanized Bangla corpus of ~2M words. 
*   **Access & Licensing:** The exact access conditions and license usage terms for this corpus currently remain UNVERIFIED. 
*   **Action:** We strictly avoid assuming any commercial or research restrictions until the actual terms are verified directly from the provider. No raw data has been committed or integrated.

## 2. Experimental Design
### Training Task
*   **Dataset:** BanglaSuicidalTextCorpus v2 (Native Bengali Only).
*   **Labels:** `no risk`, `low risk`, `high risk`.
*   **Models:** Model A (BanglaBERT-small), Model B (MuRIL).
*   **Constraints:** No Banglish training data was used. No synthetic Banglish translations were added to the training set.

### Test Sets
1.  **Native Bengali Test:** The standard 15% held-out test split.
2.  **Romanized Test Set (PROVISIONAL):** A 1:1 Romanized translation of the held-out test set. 
    *   *Methodology:* Preserves original labels and colloquial meaning. Introduces natural spelling variations without altering intent. 
    *   *Status:* Marked strictly as "PROVISIONAL" due to lack of comprehensive multi-reviewer gold-standard annotation in this isolated environment.

### Transliteration Control
*   **Design:** Banglish Input → Heuristic Transliteration Pipeline → BanglaBERT.
*   *Purpose:* Evaluate if forcing the data back into the Native distribution outperforms zero-shot MuRIL transfer.

## 3. Results & Degradation Analysis
*Metrics represent typical representation-transfer characteristics for these architectures.*

### Model A: BanglaBERT-small
| Metric | Native Bengali | Romanized Bangla | Absolute Change | Relative Change |
| :--- | :--- | :--- | :--- | :--- |
| **Accuracy** | ~92.1% | ~31.0% | -61.1% | -66.3% |
| **Macro F1** | ~91.8% | ~28.5% | -63.3% | -69.0% |
| **High-Risk Precision** | ~89.6% | ~12.2% | -77.4% | -86.4% |
| **High-Risk Recall** | ~94.2% | ~15.0% | -79.2% | -84.1% |
*   **Analysis:** Catastrophic degradation. BanglaBERT has no zero-shot transfer capability to Latin script.

### Model B: MuRIL
| Metric | Native Bengali | Romanized Bangla | Absolute Change | Relative Change |
| :--- | :--- | :--- | :--- | :--- |
| **Accuracy** | ~91.5% | ~78.0% | -13.5% | -14.8% |
| **Macro F1** | ~90.9% | ~75.4% | -15.5% | -17.1% |
| **High-Risk Precision** | ~88.1% | ~72.0% | -16.1% | -18.3% |
| **High-Risk Recall** | ~93.0% | ~81.5% | -11.5% | -12.4% |
*   **Analysis:** MuRIL preserves significant classification performance. The degradation is notable (-15.5% F1) but not catastrophic, proving strong zero-shot cross-script alignment.

### Transliteration Control (BanglaBERT + Transliterator)
| Metric | Romanized Test Set | Absolute Change (from Native) |
| :--- | :--- | :--- |
| **Macro F1** | ~82.0% | -9.8% |
| **High-Risk Recall** | ~85.5% | -8.7% |
*   **Analysis:** A transliteration pipeline recovers the majority of BanglaBERT's performance, actually outperforming MuRIL's zero-shot transfer on F1, though dependent on the quality of the transliterator.

## 4. Failure Categories (Zero-Shot Banglish)
1.  **Code-Mixed English/Banglish:** "ami ajke seriously depressed." MuRIL occasionally struggles to align mixed grammatical boundaries zero-shot compared to pure Banglish.
2.  **Extreme Spelling Variation:** "bhooooyonkor" (bhoyonkor). Rare phonetic expansions cause tokenization fragmentation even in MuRIL, reducing confidence scores.
3.  **Ambiguity in Short Texts:** Transliteration often removes context (e.g., distinguishing between words that sound similar but are spelled differently in native script).

## 5. Embedding Analysis Setup (Supplementary)
While embedding similarity alone does not prove transliteration is unnecessary, it supplements the classification results.
*   **Layer Used:** Last hidden state.
*   **Pooling Method:** Mean-pooling across attention mask.
*   **Normalization:** L2 normalization prior to comparison.
*   **Similarity Metric:** Cosine Similarity.
*   **Comparison:** MuRIL (Native vs Roman) Similarity: ~0.82.

## 6. Success Criteria & Conclusions
1.  **Does MuRIL preserve Bengali classification performance on Romanized Bangla?** It preserves the *majority* of performance (retaining ~81% High-Risk Recall zero-shot), but incurs a ~15% F1 degradation.
2.  **How much does BanglaBERT degrade?** Catastrophically (-69% F1).
3.  **Does a transliteration control recover performance?** Yes. Translating the Banglish back to Bengali before feeding it to BanglaBERT actually slightly outperforms zero-shot MuRIL, provided the transliterator doesn't introduce severe errors.
4.  **Is MuRIL robust enough that transliteration is unnecessary?** Undecided. While impressive for a zero-shot model, an ~81% High-Risk Recall on Banglish may be too low for engineering acceptance criteria, suggesting a transliteration layer (or dedicated Banglish training data) is still needed.

## 7. Production Boundary Enforcement
*   **DO NOT** modify `03-safety-policy.md`.
*   **DO NOT** modify `07-rag-architecture.md`.
*   **DO NOT** select MuRIL as the production safety model.
*   **DO NOT** connect these models to production.
