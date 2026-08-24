# Gate 3: Clinical Safety Evidence

> **Status:** LIVE RESEARCH DOCUMENT
> **Purpose:** To formally catalogue and analyze authoritative medical evidence for clinical safety rules, distinguishing explicitly between official clinical guidance and system engineering interpretations.
> **Note:** This gate is NOT yet finalized. Do not implement these rules in production until Gate 3 is formally approved.

## 1. Urgency and Emergency Guidance Boundaries

| Field | Content |
|---|---|
| **Policy question** | What constitutes a life-threatening medical emergency requiring immediate redirection to 999/A&E? |
| **Candidate system behavior** | Bypass RAG and output a Level A (Emergency) warning if the user mentions specific red-flag symptoms. |
| **Exact authoritative source** | National Health Service (NHS), UK |
| **Exact document title** | "When to call 999" |
| **URL** | https://www.nhs.uk/nhs-services/urgent-and-emergency-care-services/when-to-call-999/ |
| **Relevant section/page** | "When to call 999" (list of life-threatening emergencies) |
| **Jurisdiction** | United Kingdom (Global applicability for general physiological emergencies) |
| **Publication/update date** | Ongoing / Current |
| **What the source actually supports** | Explicit symptom list for 999: Chest pain, difficulty breathing, loss of consciousness, severe bleeding, severe allergic reactions, suspected stroke, seizures not stopping. |
| **What it does NOT support** | It does not define "mild" vs "severe" for all symptoms mathematically. It does not provide an exhaustive list of every possible emergency. |
| **Proposed implementation interpretation** | NLP triggers matching the explicit NHS list (e.g., "chest pain", "can't breathe", "passed out") will trigger Level A. All other symptoms rely on source-document explicit triage logic. |
| **Evidence strength** | High (National Health Authority) |
| **Production approval status** | PROPOSED |
| **Remaining uncertainty** | How the system reliably distinguishes "chest pain" (cardiac) from "chest hurts when I cough" (mild respiratory) without diagnostic capability. |

## 2. Self-Harm / Crisis Classification

| Field | Content |
|---|---|
| **Policy question** | How should the system distinguish between general emotional distress and acute suicidal crisis? |
| **Candidate system behavior** | Trigger Kaan Pete Roi (Bangladesh) and 999 for imminent self-harm, while offering general coping resources for standard distress. |
| **Exact authoritative source** | World Health Organization (WHO) |
| **Exact document title** | mhGAP Intervention Guide (mhGAP-IG) Version 2.0 |
| **URL** | https://iris.who.int/handle/10665/250239 |
| **Relevant section/page** | Module: Self-Harm / Suicide (Assessment algorithms) |
| **Jurisdiction** | Global |
| **Publication/update date** | 2016 (Current V2) |
| **What the source actually supports** | Differentiates risk based on "current intent" and "specific plan." Recommends ensuring safety and immediate referral for imminent risk. |
| **What it does NOT support** | Does not provide a script for an AI chatbot to automatically diagnose intent via text alone. |
| **Proposed implementation interpretation** | Any explicit mention of intent, plan, or recent act of self-harm triggers the immediate crisis bypass (999/Kaan Pete Roi). General mentions of sadness/stress without harm indicators fall to standard RAG processing. |
| **Evidence strength** | High (Global standard for non-specialist care) |
| **Production approval status** | RESEARCH REQUIRED |
| **Remaining uncertainty** | Validating NLP boundaries for intent vs. ideation in conversational text without false positives blocking legitimate mental health queries. |

## 3. Medication-Information Safety Boundaries

| Field | Content |
|---|---|
| **Policy question** | When is it clinically safe to provide medication information, and what is the boundary between OTC self-care and prescription management? |
| **Candidate system behavior** | Refuse prescription dosage questions. Provide OTC self-care info only if the source explicitly recommends it, with a disclaimer. |
| **Exact authoritative source** | World Health Organization (WHO) |
| **Exact document title** | WHO guideline on self-care interventions for health and well-being |
| **URL** | https://www.who.int/publications/i/item/9789240052192 |
| **Relevant section/page** | Chapters on Responsible Self-Medication |
| **Jurisdiction** | Global |
| **Publication/update date** | 2022 |
| **What the source actually supports** | Supports "responsible self-medication" for self-limiting conditions using non-prescription medicines. Stresses the need for clear boundaries and professional guidance for non-OTC drugs. |
| **What it does NOT support** | Does not provide a universal list of which drugs are OTC vs Prescription, as this varies by national jurisdiction (e.g., Bangladesh BDNF). |
| **Proposed implementation interpretation** | The system will refuse any query asking "how much [Drug] should I take" unless [Drug] is a basic OTC (e.g., Paracetamol) explicitly covered by an approved ingested document (like NHS A-Z) for the exact symptom, appending a "consult pharmacy/16263" disclaimer. |
| **Evidence strength** | Moderate (Relies on local jurisdiction mappings) |
| **Production approval status** | RESEARCH REQUIRED |
| **Remaining uncertainty** | We currently lack the explicit Bangladesh National Formulary (BDNF) OTC vs Prescription classifications to strictly enforce this locally. |

## 4. Source Conflict-Resolution Policy

| Field | Content |
|---|---|
| **Policy question** | How should the system determine which medical fact to present if approved sources contradict each other? |
| **Candidate system behavior** | Prefer DGHS > WHO > NHS based on a multi-factor Source Authority Framework. |
| **Exact authoritative source** | World Health Organization (WHO) / GRADE Working Group |
| **Exact document title** | WHO Handbook for Guideline Development (GRADE methodology) |
| **URL** | https://www.who.int/publications/i/item/9789241548960 |
| **Relevant section/page** | Chapters on Evidence to Decision (EtD) frameworks |
| **Jurisdiction** | Global |
| **Publication/update date** | 2014 |
| **What the source actually supports** | Evidence quality is based on trial design, consistency, and directness. Recommendations are adjusted for local values, resources, and epidemiological context. |
| **What it does NOT support** | Does not state that a local health authority is mathematically "more correct" than a global one on biological facts, only on policy/implementation. |
| **Proposed implementation interpretation** | If facts conflict, the system evaluates: 1. Jurisdiction (DGHS overrules for BD policy). 2. Specificity (A document specifically about a disease overrules a general overview). The LLM will present both if uncertainty remains. |
| **Evidence strength** | High (Methodological standard) |
| **Production approval status** | PROPOSED |
| **Remaining uncertainty** | How to reliably prompt an LLM to perform this complex EtD evaluation algorithmically without hallucinating the confidence weight. |

---

## Evidence-to-Implementation Boundary

This section explicitly distinguishes between clinical reality and our engineering approximations.

### 1. What the sources say
*   **NHS:** Lists 10+ explicit scenarios requiring a 999 call (chest pain, breathing loss, etc.).
*   **WHO mhGAP:** Distinguishes suicide risk by assessing active intent and specific plans.
*   **WHO Self-Care:** Endorses responsible self-medication for minor ailments but defers OTC definitions to local jurisdictions.
*   **GRADE:** Resolves clinical conflicts via rigorous human-led "Evidence to Decision" frameworks, weighing local context and evidence strength.

### 2. What engineering interpretation is being proposed
*   **Urgency:** We map the exact NHS text strings to a hardcoded NLP blocklist. If matched, the system forcefully outputs a Level A classification and stops normal generation.
*   **Self-Harm:** We map words related to "intent/plan" to a secondary blocklist, triggering a hardcoded crisis response.
*   **Medication:** We restrict dosage generation to an explicit whitelist of OTC drugs (e.g., Paracetamol) backed by a specific RAG chunk, blanket-refusing all other dosage queries.
*   **Conflict:** We instruct the LLM in the system prompt to prefer DGHS chunks over NHS chunks if they appear in the same context window.

### 3. Does this interpretation introduce assumptions?
**YES.**
*   *Assumption 1:* We assume NLP can accurately detect the clinical difference between "My chest hurts from coughing" and "I have crushing chest pain" without a human clinician's clarifying questions.
*   *Assumption 2:* We assume users in suicidal crisis will use standard vocabulary to express intent/plan.
*   *Assumption 3:* We assume the LLM can consistently apply a complex Evidence-to-Decision framework dynamically in its context window.

### 4. Are these assumptions acceptable for a non-diagnostic health-information system?
**Partially.**
*   *Acceptable:* The urgency and self-harm keyword mappings are acceptable *if* they fail conservatively (i.e., it is better to over-trigger the 999 warning than to miss a heart attack).
*   *Not Acceptable (Yet):* Expecting the LLM to dynamically resolve source conflicts using GRADE methodology is likely too complex and prone to hallucination. We must simplify the conflict-resolution system prompt before production.
