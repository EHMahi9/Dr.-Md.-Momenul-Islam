# User Stories: Dr. Md. Momenul Islam

> **Governing Documents:** This document is derived from the approved [Project Charter](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/docs/00-project-charter.md), [Problem Statement](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/docs/01-problem-statement.md), [Requirements Specification](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/docs/02-requirements.md), [Safety Policy](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/docs/03-safety-policy.md), and [User Personas](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/docs/04-user-personas.md).
>
> **Purpose:** Translate user personas and approved requirements into testable user stories with stable identifiers and traceability.
>
> **Rule:** No capabilities have been added that are not already justified by the governing documents.

---

## User Story Format

> As a **[persona]**, I want **[goal]**, so that **[benefit]**.

**Story ID Prefixes:**

| Prefix | Persona Group |
|---|---|
| `US-GEN` | General Health Information Seeker |
| `US-BNG` | Bangla-First User |
| `US-BIL` | English-First / Bilingual User |
| `US-CAR` | Caregiver / Family Member |
| `US-RES` | Student / Research User |
| `US-HCP` | Healthcare Professional Reviewer |
| `US-DEV` | Project Developer / Maintainer |
| `US-SAF` | Cross-Cutting Safety Stories |

---

## 1. General Health Information Seeker

---

### US-GEN-01 — Ask a Health Question

> As a **general user**, I want to **submit a health-related question in natural language**, so that **I can obtain understandable health information**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-01, FR-05 |
| **Safety Considerations** | Response must remain within the project's health-information scope and must not claim diagnostic authority (SR-01, SR-02). |

**Acceptance Criteria:**
- [ ] User can enter a health-related question through the web interface.
- [ ] The system accepts natural-language input.
- [ ] The system does not require medical terminology from the user.
- [ ] The response remains within the project's defined health-information scope.

---

### US-GEN-02 — Describe Symptoms

> As a **general user**, I want to **describe symptoms in my own words**, so that **the system can provide relevant general health information**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-02, FR-05 |
| **Safety Considerations** | The system must not claim a definitive diagnosis from a symptom description (SR-02). |

**Acceptance Criteria:**
- [ ] User can describe one or more symptoms in natural language.
- [ ] The user does not need to structure the information in a specific medical format.
- [ ] The system does not claim a definitive diagnosis from the description.

---

### US-GEN-03 — Understand Uncertainty

> As a **general user**, I want **the system to communicate uncertainty clearly**, so that **I do not mistake general information for a confirmed diagnosis**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-06, SR-02, SR-06 |
| **Safety Considerations** | Uncertainty communication is mandatory per Safety Policy SP-03. |

**Acceptance Criteria:**
- [ ] When evidence is incomplete, conflicting, or insufficient, the response explicitly communicates uncertainty.
- [ ] The system does not present unsupported certainty as fact.

---

### US-GEN-04 — See Relevant Warning Signs

> As a **general user**, I want to **understand relevant warning signs**, so that **I can recognize when professional evaluation may be appropriate**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-07, FR-08, SR-07 |
| **Safety Considerations** | Warning signs must be grounded in retrieved evidence or established safety rules (SP-06, SP-07). |

**Acceptance Criteria:**
- [ ] Warning signs are displayed when supported by retrieved evidence or safety rules.
- [ ] Warning signs are visually distinguishable from general information (UI-04).

---

### US-GEN-05 — Understand General Urgency

> As a **general user**, I want **clear general urgency guidance**, so that **I can understand whether I may need general information, professional consultation, or more urgent evaluation**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-08, SR-07 |
| **Safety Considerations** | Urgency guidance must **not** be described as a medical diagnosis (SR-02). Urgency classification criteria are **RESEARCH REQUIRED** (Safety Policy §4). |

**Acceptance Criteria:**
- [ ] The system provides a general urgency indication when justified.
- [ ] Urgency guidance is clearly distinguished from diagnosis.
- [ ] Professional care is recommended when the situation warrants it.

---

### US-GEN-06 — Inspect Sources

> As a **general user**, I want to **see the sources supporting an answer**, so that **I can verify the information myself**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-09, SRC-01, SRC-02 |
| **Safety Considerations** | The system must not fabricate citations (SRC-03, SP-08). |

**Acceptance Criteria:**
- [ ] Sources displayed correspond to actual retrieved material.
- [ ] The system does not fabricate citations.
- [ ] Source metadata (title, publisher, reference) is retained and displayed.

---

## 2. Bangla-First User

---

### US-BNG-01 — Ask in Bangla

> As a **Bangla-first user**, I want to **ask health questions in Bangla**, so that **I can communicate naturally without translating my question into English**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-03, UI-05 |
| **Safety Considerations** | Language processing must not distort the medical intent of the user's question. |

**Acceptance Criteria:**
- [ ] The system accepts health questions written in Bangla.
- [ ] The system processes the question without requiring the user to translate to English.

---

### US-BNG-02 — Understand the Response in Bangla

> As a **Bangla-first user**, I want **health information explained clearly in Bangla**, so that **medical information is easier to understand**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-03, FR-05, UI-05 |
| **Safety Considerations** | Important warning signs and uncertainty must retain their intended medical meaning across language processing (SP-03, SP-06). |

**Acceptance Criteria:**
- [ ] The response is presented in clear Bangla when the user communicates in Bangla.
- [ ] Safety-critical information (warning signs, uncertainty, urgency) retains its intended meaning.

---

### US-BNG-03 — Preserve Safety Meaning During Language Processing

> As a **Bangla-first user**, I want **safety instructions and warning signs to retain their meaning across language processing**, so that **translation does not create unsafe misunderstanding**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-03, SR-02, SR-06 |
| **Safety Considerations** | This is a core safety story. Translation errors in urgency or warning-sign communication could lead to harm (SP-07). |

**Acceptance Criteria:**
- [ ] Safety-critical terms (warning signs, urgency levels, uncertainty language) are not distorted by language processing.
- [ ] The system's safety behavior is testable for Bangla input (Safety Policy §16).

---

## 3. English-First / Bilingual User

---

### US-BIL-01 — Ask in English

> As an **English-first user**, I want to **ask health questions in English**, so that **I can use familiar medical terminology when appropriate**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-01, FR-03 |

**Acceptance Criteria:**
- [ ] The system accepts health questions written in English.
- [ ] The user can use medical terminology without the system requiring simplification.

---

### US-BIL-02 — Switch Between Bangla and English

> As a **bilingual user**, I want to **use Bangla and English naturally**, so that **I can communicate in whichever language is most comfortable**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-03 |
| **Note** | The exact language-processing architecture remains **TO BE DECIDED**. |

**Acceptance Criteria:**
- [ ] The system handles input that contains both Bangla and English.
- [ ] The system does not require the user to select a language mode before asking a question.

---

## 4. Caregiver / Family Member

---

### US-CAR-01 — Ask on Behalf of Another Person

> As a **caregiver**, I want to **ask a health question about another person**, so that **I can understand general health information relevant to that person**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-02, FR-05 |
| **Safety Considerations** | The system must not assume the questioner is the patient. The response must not imply the person was examined (SP-02). |

**Acceptance Criteria:**
- [ ] The system accepts questions phrased on behalf of another person.
- [ ] The response does not assume the questioner is the patient.
- [ ] The response does not imply that the AI has examined the person in question.

---

### US-CAR-02 — Recognize Warning Signs for Another Person

> As a **caregiver**, I want to **understand relevant warning signs for another person**, so that **I can recognize when professional care may be appropriate for them**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-07, FR-08, SR-07 |
| **Safety Considerations** | Urgency guidance is particularly important for caregivers making time-sensitive decisions about seeking professional care (SP-06). |

**Acceptance Criteria:**
- [ ] Warning signs are presented when supported by evidence or safety rules.
- [ ] The system recommends professional care when the situation warrants it.

---

## 5. Student / Research User

---

### US-RES-01 — Inspect Evidence

> As a **student or researcher**, I want to **inspect the evidence and sources used by the system**, so that **I can evaluate how the response was grounded**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-09, AI-03, SRC-01, SRC-02 |

**Acceptance Criteria:**
- [ ] Sources are visible and correspond to retrieved material.
- [ ] The user can identify which sources contributed to the response.

---

### US-RES-02 — Understand System Limitations

> As a **student or researcher**, I want to **understand the system's limitations**, so that **I can evaluate its behavior responsibly**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-06, NFR-08 |

**Acceptance Criteria:**
- [ ] The system communicates its limitations (e.g., via disclaimers, uncertainty language).
- [ ] The user can understand that retrieval does not guarantee correctness (AI-03).

---

### US-RES-03 — Evaluate Safety Behavior

> As a **researcher**, I want to **evaluate safety behavior using documented test cases**, so that **I can compare different implementations consistently**.

| Field | Detail |
|---|---|
| **Related Requirements** | NFR-09, Safety Policy §16 |

**Acceptance Criteria:**
- [ ] Documented safety test cases exist and can be executed repeatably.
- [ ] Results are comparable across the two project tracks (Track A and Track B).

---

## 6. Healthcare Professional Reviewer

---

### US-HCP-01 — Review Medical Sources

> As a **healthcare professional reviewer**, I want to **inspect the approved medical sources**, so that **I can evaluate whether the knowledge base uses appropriate evidence**.

| Field | Detail |
|---|---|
| **Related Requirements** | KB-01, KB-02, KB-03, KB-04, KB-05, KB-06 |

**Acceptance Criteria:**
- [ ] The approved source list is documented and accessible for review.
- [ ] Source metadata is preserved and inspectable.

**Important Boundary:**
Do not claim professional validation has occurred unless it actually has.

---

### US-HCP-02 — Review Safety Behavior

> As a **healthcare professional reviewer**, I want to **review safety policies and system behavior**, so that **unsafe patterns can be identified**.

| Field | Detail |
|---|---|
| **Related Requirements** | SR-01 through SR-10 |

**Acceptance Criteria:**
- [ ] The Safety Policy document is accessible.
- [ ] System behavior can be evaluated against documented safety rules.
- [ ] Safety test results are available for review.

---

## 7. Developer / Maintainer

---

### US-DEV-01 — Maintain the Knowledge Base

> As a **developer**, I want to **add or update approved medical sources without rewriting the entire application**, so that **knowledge maintenance remains manageable**.

| Field | Detail |
|---|---|
| **Related Requirements** | KB-05, NFR-05 |

**Acceptance Criteria:**
- [ ] New approved sources can be added to the knowledge base through a defined process.
- [ ] Adding sources does not require changes to application logic.

---

### US-DEV-02 — Protect Secrets

> As a **developer**, I want **API keys and credentials to remain outside source code and version control**, so that **secrets are not exposed**.

| Field | Detail |
|---|---|
| **Related Requirements** | NFR-06, PR-03 |

**Acceptance Criteria:**
- [ ] No API keys or secrets exist in committed source code.
- [ ] A `.env.example` file documents required environment variables without containing actual values.

---

### US-DEV-03 — Maintain Source Metadata

> As a **developer**, I want **source metadata to remain attached to retrieved content**, so that **answers can be correctly attributed**.

| Field | Detail |
|---|---|
| **Related Requirements** | KB-02, KB-04, SRC-04 |

**Acceptance Criteria:**
- [ ] Source metadata (title, publisher, reference, document ID) is preserved through ingestion, chunking, retrieval, and response generation.
- [ ] The response can trace back to the specific source/chunk used.

---

### US-DEV-04 — Run Repeatable Tests

> As a **developer**, I want **repeatable functional and safety tests**, so that **changes can be evaluated before release**.

| Field | Detail |
|---|---|
| **Related Requirements** | NFR-09 |

**Acceptance Criteria:**
- [ ] Functional tests can be executed repeatably.
- [ ] Safety tests can be executed repeatably.
- [ ] Test results are documented.

---

### US-DEV-05 — Protect Safety Requirements

> As a **developer**, I want **safety-sensitive changes to require explicit review**, so that **safety rules are not accidentally weakened**.

| Field | Detail |
|---|---|
| **Related Requirements** | Safety Policy §19 |

**Acceptance Criteria:**
- [ ] Changes to safety-related code or policy are identifiable in the codebase.
- [ ] The governance rule (Safety Policy §19) is followed before merging safety-affecting changes.

---

## 8. Cross-Cutting Safety Stories

These stories apply across all user personas and enforce mandatory safety behaviors.

---

### US-SAF-01 — No Definitive Diagnosis

> As a **user**, I want **the system to avoid definitive diagnosis claims**, so that **I do not mistake the assistant for a medical professional**.

| Field | Detail |
|---|---|
| **Related Requirements** | SR-01, SR-02 |
| **Safety Policy** | SP-01, SP-02 |

**Acceptance Criteria:**
- [ ] The system never states "You have [disease]" based solely on a symptom description.
- [ ] The system never claims to be a doctor or medical professional.

---

### US-SAF-02 — Safe Medication Handling

> As a **user**, I want **medication-related questions to be handled conservatively**, so that **the system does not provide unsafe prescriptions or dosing**.

| Field | Detail |
|---|---|
| **Related Requirements** | SR-03, SR-04 |
| **Safety Policy** | SP-05 |

**Acceptance Criteria:**
- [ ] The system does not independently prescribe prescription medication.
- [ ] The system does not provide unsafe individualized dosing.
- [ ] Medication information, if provided as general education, is grounded in approved sources.

---

### US-SAF-03 — Safe Handling of Urgent Situations

> As a **user**, I want **potentially urgent situations to receive appropriate safety guidance**, so that **important warning signs are not treated as ordinary questions**.

| Field | Detail |
|---|---|
| **Related Requirements** | SR-05, SR-07 |
| **Safety Policy** | SP-06, Safety Policy §3, §4 |
| **Note** | Exact urgency classification criteria are **RESEARCH REQUIRED**. |

**Acceptance Criteria:**
- [ ] Potentially urgent situations trigger the safety assessment path.
- [ ] The system recommends professional or urgent care when warranted.
- [ ] The system does not provide false reassurance for potentially serious situations (SP-07).

---

### US-SAF-04 — Safe Handling of Harmful Requests

> As a **user**, I want **unsafe medical requests to be refused or redirected safely**, so that **the system does not provide dangerous instructions**.

| Field | Detail |
|---|---|
| **Related Requirements** | FR-10 |
| **Safety Policy** | Safety Policy §6 |

**Acceptance Criteria:**
- [ ] Requests for dangerous medical instructions are refused or redirected.
- [ ] The refusal response does not itself provide harmful information.

---

### US-SAF-05 — Safe Failure

> As a **user**, I want **the system to fail safely when retrieval, the knowledge base, the LLM, or safety processing is unavailable**, so that **I am not misled into believing an answer is evidence-grounded when it is not**.

| Field | Detail |
|---|---|
| **Related Requirements** | NFR-04, AI-03 |
| **Safety Policy** | RS-04, RS-06, Safety Policy §13 |

**Acceptance Criteria:**
- [ ] When retrieval fails, the system does not present an ungrounded response as evidence-based.
- [ ] When the LLM is unavailable, the system fails gracefully with an informative message.
- [ ] When the knowledge base is unavailable, the system does not silently fall back to ungrounded generation.

---

### US-SAF-06 — No Fabricated Sources

> As a **user**, I want **citations to correspond to actual retrieved sources**, so that **I can trust the source attribution**.

| Field | Detail |
|---|---|
| **Related Requirements** | SRC-01, SRC-02, SRC-03 |
| **Safety Policy** | SP-08 |

**Acceptance Criteria:**
- [ ] Every cited source corresponds to a document actually retrieved from the knowledge base.
- [ ] No citations are fabricated or hallucinated.
- [ ] Source metadata shown to the user matches the original source material.

---

## 9. User Story Acceptance Principles

Every user story in this document must:

1. **Trace** to one or more approved requirements from [`02-requirements.md`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/docs/02-requirements.md).
2. **Not silently introduce** new functionality beyond the approved scope.
3. **Respect** the [Safety Policy](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/docs/03-safety-policy.md).
4. **Not imply** clinical authority.
5. **Be testable** where practical.
6. **Clearly distinguish** current requirements from future ideas.

---

## 10. Traceability Matrix

| Story ID | Persona | Related Requirements | Safety Requirements |
|---|---|---|---|
| US-GEN-01 | General Health Information Seeker | FR-01, FR-05 | SR-01, SR-02 |
| US-GEN-02 | General Health Information Seeker | FR-02, FR-05 | SR-02 |
| US-GEN-03 | General Health Information Seeker | FR-06 | SR-02, SR-06 |
| US-GEN-04 | General Health Information Seeker | FR-07, FR-08 | SR-07 |
| US-GEN-05 | General Health Information Seeker | FR-08 | SR-02, SR-07 |
| US-GEN-06 | General Health Information Seeker | FR-09, SRC-01, SRC-02 | SRC-03 |
| US-BNG-01 | Bangla-First User | FR-03, UI-05 | — |
| US-BNG-02 | Bangla-First User | FR-03, FR-05, UI-05 | SR-02, SR-06 |
| US-BNG-03 | Bangla-First User | FR-03 | SR-02, SR-06 |
| US-BIL-01 | English-First / Bilingual User | FR-01, FR-03 | — |
| US-BIL-02 | English-First / Bilingual User | FR-03 | — |
| US-CAR-01 | Caregiver / Family Member | FR-02, FR-05 | SR-02 |
| US-CAR-02 | Caregiver / Family Member | FR-07, FR-08 | SR-07 |
| US-RES-01 | Student / Research User | FR-09, AI-03, SRC-01, SRC-02 | — |
| US-RES-02 | Student / Research User | FR-06, NFR-08 | — |
| US-RES-03 | Student / Research User | NFR-09 | Safety Policy §16 |
| US-HCP-01 | Healthcare Professional Reviewer | KB-01–KB-06 | — |
| US-HCP-02 | Healthcare Professional Reviewer | SR-01–SR-10 | SR-01–SR-10 |
| US-DEV-01 | Developer / Maintainer | KB-05, NFR-05 | — |
| US-DEV-02 | Developer / Maintainer | NFR-06, PR-03 | — |
| US-DEV-03 | Developer / Maintainer | KB-02, KB-04, SRC-04 | — |
| US-DEV-04 | Developer / Maintainer | NFR-09 | — |
| US-DEV-05 | Developer / Maintainer | Safety Policy §19 | Safety Policy §19 |
| US-SAF-01 | All Users | — | SR-01, SR-02 |
| US-SAF-02 | All Users | — | SR-03, SR-04 |
| US-SAF-03 | All Users | — | SR-05, SR-07 |
| US-SAF-04 | All Users | FR-10 | Safety Policy §6 |
| US-SAF-05 | All Users | NFR-04, AI-03 | RS-04, RS-06 |
| US-SAF-06 | All Users | SRC-01, SRC-02, SRC-03 | SP-08 |

**Traceability Chain:**
```
Persona → User Story → Requirement → Architecture Component → Implementation → Test Case
```

---

## 11. Future / Out-of-Scope Ideas

The following ideas are **not** active user stories and must **not** influence the current architecture. They are recorded here only for potential future consideration.

| Idea | Status |
|---|---|
| Voice-based health question input | FUTURE / OUT OF CURRENT SCOPE |
| Image-based symptom description (e.g., photos of skin conditions) | FUTURE / OUT OF CURRENT SCOPE |
| User accounts and personalized health history | FUTURE / OUT OF CURRENT SCOPE |
| Integration with hospital appointment systems | FUTURE / OUT OF CURRENT SCOPE |
| Multi-user collaborative health queries | FUTURE / OUT OF CURRENT SCOPE |
| Offline / low-connectivity mode | FUTURE / OUT OF CURRENT SCOPE |
| Integration with wearable health devices | FUTURE / OUT OF CURRENT SCOPE |

> These items require formal requirements analysis, safety evaluation, and charter amendment before they may be added to the project scope.
