# Gate 3 Final Review: Safety Research Consolidation

> **Status:** DECISION PACKAGE (PENDING REVIEW)
> **Purpose:** Consolidate all Gate 3 research into a final engineering evaluation.
> **Critical Constraint:** No finding in this document constitutes clinical validation. Experimental benchmark scores represent text-classification performance on isolated research datasets, NOT clinical safety, suicide-risk diagnosis, or medical triage capability.

## 1. Evidence Summary
*   **Gate 3 (Clinical Safety Evidence):** Established strict boundaries requiring explicit evidence backing for routing rules; rejected inventing clinical thresholds or broad symptom-to-urgency mappings without authoritative guidelines.
*   **Gate 3.1 (Routing Architecture):** Identified that LLM-based triage is insufficiently deterministic. Proposed a separated path architecture distinguishing clear emergencies, self-harm, and standard queries.
*   **Gate 3.2 (Failure Analysis):** Refined the architecture into strict routing states (e.g., `EXPLICIT_CRISIS_OR_OVERDOSE`, `POTENTIAL_SELF_HARM`), removing unsafe numeric hierarchies in favor of deterministic metadata processing.
*   **Gate 3.3A (Bengali Self-Harm Classification):** Validated that lightweight baseline classifiers (TF-IDF) can learn a supervised Bengali text classification task but fail on structural metaphors and negations.
*   **Gate 3.3A.1 (Multi-Seed Validation):** Proved that a transformer (BanglaBERT-small) consistently outperforms baseline models in High-Risk Recall on native text across random splits, but highlighted severe CPU latency hurdles.
*   **Gate 3.3B (Banglish Language Robustness):** Demonstrated that Romanized Bangla (Banglish) completely shatters native-trained Bengali models. Identified MuRIL as highly capable of maintaining cross-script semantic representation natively.
*   **Gate 3.3C (Provisional Zero-Shot Transfer):** Tested MuRIL's zero-shot transfer on provisional Romanized text; MuRIL retained significant capability, whereas BanglaBERT degraded catastrophically.
*   **Gate 3.3D (External Banglish Transfer):** Validated cross-script transfer mechanically using human-annotated external resources (Emotion classification, Transliteration pairs), confirming MuRIL's representational strength and the viability of a transliteration control layer.
*   **Gate 3.3E (Bengali Suicide-Risk → Banglish Transfer):** Demonstrated that MuRIL retains meaningful classification performance on a Romanized counterpart of the suicide-risk dataset, while a transliteration-into-native-script pipeline also performed competitively.

## 2. Evidence Classification
*   **VERIFIED EXTERNAL EVIDENCE:**
    *   Banglish script represents a massive out-of-distribution (OOD) shift for standard Bengali language models.
    *   MuRIL's transliterated Indian-language pretraining yields measurable cross-script semantic alignment.
    *   Model licenses (MuRIL: Apache 2.0, BanglaBERT: Non-Commercial).
*   **PROJECT EXPERIMENTAL EVIDENCE:**
    *   Native-only transformers collapse to near-random guessing on Banglish.
    *   MuRIL transfers ~75-80% of its native classification capability to Banglish zero-shot.
    *   Transliteration pipelines can recover ~80% of performance when feeding native models.
    *   Transformer inference latency incurs a ~85ms penalty on local CPU.
*   **ENGINEERING INTERPRETATION:**
    *   Categorizing text by crisis/harm intent is feasible as a routing/screening mechanism, provided it defaults to conservative escalation.
*   **UNSUPPORTED / UNKNOWN:**
    *   Real-world clinical safety of the proposed classifiers.
    *   Diagnostic validity of the datasets used.
    *   How actual human users type suicidal idioms in colloquial Banglish (real-world validation).

## 3. Production-Relevant Findings
1.  **Script Challenge:** Banglish cannot be ignored. A native-only approach will fail completely for a significant portion of user inputs.
2.  **MuRIL is a strong candidate:** It handles script shift elegantly at the embedding layer but carries a heavy local latency and memory footprint.
3.  **Transliteration is a viable alternative:** Pushing text through a transliterator into a lightweight native classifier performs competitively with MuRIL and remains a serious architectural option.
4.  **BanglaBERT-small:** is not approved for this project's production architecture under the current CC BY-NC-SA 4.0 checkpoint license. It remains research-only unless licensing is independently resolved.
5.  **No Clinical Assessment Established:** None of the experiments establish clinical suicide-risk assessment. They merely establish engineering text-classification boundaries.

## 4. Safety Router Architecture (Minimum Conservative Proposal)
The evidence supports a **Layered Hybrid Safety Router**:
1.  **Layer 1: Deterministic Keyword/Regex Screen.** Extremely fast, high-recall scanning for explicit crisis/emergency terms. Triggers immediate `EXPLICIT_CRISIS_OR_OVERDOSE` or `EXPLICIT_MEDICAL_EMERGENCY`.
2.  **Layer 2: Semantic/Probabilistic Screen.** Either a transliteration pipeline + lightweight classifier OR a cross-lingual embedding model (e.g., MuRIL) to catch implicit distress (`POTENTIAL_SELF_HARM`, `UNCERTAIN_HIGH_RISK`) based on trained semantic boundaries.
3.  **Fallback Policy:** Ambiguous potentially high-risk inputs must follow the predefined conservative fallback for their routing category. The system must not invent a clinical severity level from uncertainty. The LLM is NEVER responsible for generating medical diagnostic truth or overriding the safety screener.

## 5. Model Selection Status
*   **MuRIL Direct Banglish Path:** *Production Candidate.* (Needs latency/quantization validation).
*   **Transliteration → Bengali Model Path:** *Production Candidate.* (Depends on transliterator availability/license).
*   **Deterministic Safety Rules (Regex/Keywords):** *Mandatory Production Component.*
*   **BanglaBERT-small:** *Rejected for Production / Research-Only.* (License and Banglish constraints).
*   **Unresolved:** Final choice between MuRIL vs. Transliteration pipeline.

## 6. Licensing Implications
*   **MuRIL (google/muril-base-cased):** Apache 2.0. Usable in production/commercial settings.
*   **BanglaBERT-small:** is not approved for this project's production architecture under the current CC BY-NC-SA 4.0 checkpoint license. It remains research-only unless licensing is independently resolved.
*   **BanglaSuicidalTextCorpus & Mendeley Datasets:** CC BY 4.0. Permissive with attribution, but original user data may have privacy implications. Models fine-tuned on this should be restricted from generating text, used strictly for hidden classification.
*   **BdNC Romanized Corpus:** access and licensing terms remain unresolved. Do not use in production until the official usage terms are verified.

## 7. Remaining Unknowns
*   **Real-World Banglish Variation:** Does our provisional evaluation reflect actual chat patterns?
*   **Natural Suicidal-Language Detection:** Can the classifier detect novel, idiom-heavy distress queries not represented in the academic training set?
*   **Safety-Router Reliability:** False negative rate in a live, multi-turn conversational setting.
*   **Latency:** Will a ~250ms MuRIL CPU delay damage the real-time user experience?
*   **Gate 1 LLM Decision:** Which primary LLM provider/model will handle standard RAG routing?
*   **Source Conflict Resolution:** How the system resolves conflicting medical guidance from retrieved sources.

## 8. Final Gate Decision

1.  **Is there enough evidence to close Gate 3?** Yes, the research phase is mature enough to move to implementation design, provided the unknowns are tracked.
2.  **Which safety principles are ready to merge into governance?** The 8 strict routing states (Gate 3.2), the layered separation of deterministic vs probabilistic screening, and the prohibition of LLM-based diagnosis.
3.  **Which parts must remain research-only?** All trained checkpoints from Gate 3.3. They may inform architecture, but cannot be deployed without a production-ready retraining/quantization pipeline.
4.  **Which assumptions remain unresolved?** The final decision between MuRIL vs Transliteration, and the clinical false-negative rate on real-world Banglish.
5.  **What exact production safeguards are mandatory?** A deterministic keyword/regex fallback layer, and UI disclosures explicitly stating the system is not a medical professional.
6.  **What should NOT be implemented?** An LLM-based safety triage prompt, arbitrary numeric risk scores, and BanglaBERT.
