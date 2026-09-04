# Requirements Specification: Dr. Md. Momenul Islam

> **Governing Documents:** This requirements specification is derived from the approved [Project Charter](./00-project-charter.md) and [Problem Statement](./01-problem-statement.md). No requirements have been added that are not justified by those documents. For current system state, see [Current Implementation State](./13-current-implementation-state.md).

> **Requirement Classification Key:**
> | Label | Meaning |
> |---|---|
> | **REQUIRED** | Explicitly part of the current project scope |
> | **RESEARCH REQUIRED** | Needs external evidence before finalizing |
> | **TO BE DECIDED** | Architectural or product decision not yet finalized |
> | **OUT OF SCOPE** | Deliberately excluded from the current project |

---

## 1. Functional Requirements

| ID | Requirement | Classification |
|---|---|---|
| **FR-01** | **Health Question Input** — The system shall allow a user to submit a health-related question in Bangla or English through the web interface. | REQUIRED |
| **FR-02** | **Symptom Description** — The system shall allow a user to describe symptoms or a health concern in natural language. | REQUIRED |
| **FR-03** | **Language Handling** — The system shall support both Bangla and English user interaction. The exact translation and language-processing architecture is *To Be Decided*. | REQUIRED / TO BE DECIDED (architecture) |
| **FR-04** | **Evidence Retrieval** — The system shall retrieve relevant information from the approved medical knowledge base before generating a grounded response. | REQUIRED |
| **FR-05** | **Grounded Response** — The system shall generate a health-information response using relevant retrieved evidence where appropriate. | REQUIRED |
| **FR-06** | **Uncertainty Communication** — The system shall clearly communicate uncertainty when the available evidence or user information does not justify certainty. | REQUIRED |
| **FR-07** | **Warning Signs** — The system shall identify and communicate relevant warning signs when supported by the retrieved evidence and system safety rules. | REQUIRED |
| **FR-08** | **General Urgency Guidance** — When appropriate, the system shall communicate whether the situation appears to warrant: (a) general self-information, (b) professional medical consultation, or (c) more urgent evaluation. This must not be described as a medical diagnosis. | REQUIRED |
| **FR-09** | **Source Attribution** — The system shall show the sources used to support the generated response. | REQUIRED |
| **FR-10** | **Unsafe Request Handling** — The system shall refuse, redirect, or provide a safer response to requests that fall outside the system's safety boundaries. | REQUIRED |
| **FR-11** | **Conversation Context** — The system may maintain relevant conversation context where needed for coherent interaction. The exact conversation-memory design is *To Be Decided*. | REQUIRED / TO BE DECIDED (design) |

---

## 2. Safety Requirements

> Safety requirements are **mandatory** and must not be weakened to ease implementation or improve user satisfaction.

| ID | Requirement | Classification |
|---|---|---|
| **SR-01** | **No Doctor Impersonation** — The system must never represent itself as a licensed doctor or medical professional. | REQUIRED |
| **SR-02** | **No Certain Diagnosis** — The system must not claim a definitive diagnosis solely from user-described symptoms. | REQUIRED |
| **SR-03** | **No Unsafe Prescription** — The system must not independently prescribe prescription medication. | REQUIRED |
| **SR-04** | **No Unsafe Individualized Dosing** — The system must not provide dangerous individualized medication dosing without a clinically appropriate basis. | REQUIRED |
| **SR-05** | **Emergency Handling** — Potentially urgent or emergency situations must be handled conservatively according to the approved safety policy (defined in `03-safety-policy.md`). | REQUIRED |
| **SR-06** | **Uncertainty** — The system must communicate uncertainty where appropriate rather than presenting unsupported certainty. | REQUIRED |
| **SR-07** | **Human Care Escalation** — The system should encourage appropriate professional medical evaluation when the situation warrants it. | REQUIRED |
| **SR-08** | **Safety Before Convenience** — Safety rules must take precedence over producing a more satisfying or more direct answer. | REQUIRED |
| **SR-09** | **Source Grounding** — When medical claims are based on the knowledge base, the system should prioritize retrieved evidence over unsupported model-generated claims. | REQUIRED |
| **SR-10** | **Safety Logging for Evaluation** — Where appropriate and privacy-safe, safety decisions should be observable enough to support testing and evaluation. | REQUIRED |

---

## 3. Non-Functional Requirements

| ID | Requirement | Classification |
|---|---|---|
| **NFR-01** | **Usability** — The interface should be understandable to a general user with basic digital literacy. | REQUIRED |
| **NFR-02** | **Accessibility** — The interface should support readable text, clear hierarchy, keyboard-friendly interaction where practical, and responsive layouts. | REQUIRED |
| **NFR-03** | **Performance** — Normal user requests should receive a response within a reasonable time based on the chosen AI provider and retrieval architecture. The exact measurable performance target is *To Be Decided* after the initial prototype. | REQUIRED / TO BE DECIDED (target) |
| **NFR-04** | **Reliability** — The system should fail safely when the LLM, retrieval system, or external services are unavailable. | REQUIRED |
| **NFR-05** | **Maintainability** — Frontend, backend, retrieval, safety logic, and knowledge-base processing should be separated into understandable modules. | REQUIRED |
| **NFR-06** | **Security** — API keys and secrets must never be committed to source control. | REQUIRED |
| **NFR-07** | **Privacy** — User health-related input must be treated as sensitive information. The project should collect only data necessary for the defined functionality. | REQUIRED |
| **NFR-08** | **Explainability** — The system should make it understandable which sources contributed to an answer where practical. | REQUIRED |
| **NFR-09** | **Testability** — The major functional and safety behaviors must be testable independently. | REQUIRED |

---

## 4. Knowledge-Base Requirements

| ID | Requirement | Classification |
|---|---|---|
| **KB-01** | The knowledge base must contain only approved sources. | REQUIRED |
| **KB-02** | Each document should preserve source metadata: title, publisher/organization, publication/update information where available, source URL or reference, and document identifier. | REQUIRED |
| **KB-03** | Documents should be processed into retrievable chunks without losing meaningful source context. | REQUIRED |
| **KB-04** | The system should be able to identify which source/chunk contributed to a response. | REQUIRED |
| **KB-05** | The knowledge base should be updateable without rewriting the application logic. | REQUIRED |
| **KB-06** | Unverified or arbitrary internet content must not automatically enter the trusted knowledge base. | REQUIRED |
| — | The exact initial approved source list. | TO BE DECIDED (after research) |

---

## 5. AI / RAG Requirements

| ID | Requirement | Classification |
|---|---|---|
| **AI-01** | The LLM should receive the user's question and relevant retrieved context. | REQUIRED |
| **AI-02** | The system should instruct the LLM to prioritize retrieved evidence. | REQUIRED |
| **AI-03** | The system must not treat retrieval as a guarantee of correctness. | REQUIRED |
| **AI-04** | The system should have a defined behavior when retrieval returns insufficient or conflicting evidence. | REQUIRED |
| **AI-05** | The system should avoid unsupported medical claims. | REQUIRED |
| **AI-06** | The system architecture should allow the LLM provider/model to be changed without rewriting the entire application. The exact model/provider is *To Be Decided*. | REQUIRED / TO BE DECIDED (provider) |
| **AI-07** | The retrieval mechanism should eventually support semantic search, but the first implementation should be simple enough for the developer to understand. | REQUIRED |

---

## 6. Frontend Requirements

| ID | Requirement | Classification |
|---|---|---|
| **UI-01** | The frontend shall provide a clear landing page. | REQUIRED |
| **UI-02** | The frontend shall provide a health-question / chat interface. | REQUIRED |
| **UI-03** | The frontend shall display visible safety and disclaimer information. | REQUIRED |
| **UI-04** | The frontend shall clearly separate: user question, AI response, warning signs, urgency guidance, and sources. | REQUIRED |
| **UI-05** | The frontend shall support Bangla and English text display. | REQUIRED |
| **UI-06** | The frontend shall use responsive design for desktop and mobile. | REQUIRED |
| — | The exact visual design specification. | Defined separately in `10-ui-specification.md` |

---

## 7. Backend Requirements

| ID | Requirement | Classification |
|---|---|---|
| **BE-01** | The backend shall expose API endpoints for frontend communication. | REQUIRED |
| **BE-02** | The backend shall accept user questions securely. | REQUIRED |
| **BE-03** | The backend shall validate incoming requests. | REQUIRED |
| **BE-04** | The backend shall perform the safety-processing step. | REQUIRED |
| **BE-05** | The backend shall perform knowledge retrieval. | REQUIRED |
| **BE-06** | The backend shall construct the AI request (prompt + retrieved context). | REQUIRED |
| **BE-07** | The backend shall return a structured response to the frontend. | REQUIRED |
| **BE-08** | The backend shall handle failures safely. | REQUIRED |
| **BE-09** | The backend shall keep secrets outside source code. | REQUIRED |
| — | The exact API contracts. | Defined separately in `08-api-specification.md` |

---

## 8. Source / Citation Requirements

| ID | Requirement | Classification |
|---|---|---|
| **SRC-01** | Medical answers should include source attribution where the response is knowledge-grounded. | REQUIRED |
| **SRC-02** | The source shown to the user must correspond to the actual retrieved source material. | REQUIRED |
| **SRC-03** | The system must not fabricate citations. | REQUIRED |
| **SRC-04** | The system should preserve source metadata through the retrieval pipeline. | REQUIRED |

---

## 9. Privacy Requirements

> The project handles health-related information. Privacy is a first-class concern.

| ID | Requirement | Classification |
|---|---|---|
| **PR-01** | The system shall not collect unnecessary personal information. | REQUIRED |
| **PR-02** | The system shall not require users to enter identifying information simply to ask a general health question, unless later justified by a documented requirement. | REQUIRED |
| **PR-03** | API keys and credentials must remain private and must never be exposed to the frontend or committed to source control. | REQUIRED |
| **PR-04** | Logs must avoid exposing sensitive user information unnecessarily. | REQUIRED |
| **PR-05** | Any stored conversation data must have a documented purpose and retention strategy. The exact data-retention policy is *To Be Decided*. | REQUIRED / TO BE DECIDED (policy) |

---

## 10. Explicit Non-Requirements

The following capabilities are **OUT OF SCOPE** for the initial project:

| Capability | Classification |
|---|---|
| Guaranteed medical diagnosis | OUT OF SCOPE |
| Medical prescription | OUT OF SCOPE |
| Emergency dispatch | OUT OF SCOPE |
| Doctor replacement | OUT OF SCOPE |
| Clinical decision authority | OUT OF SCOPE |
| Hospital management | OUT OF SCOPE |
| Electronic medical records | OUT OF SCOPE |
| Autonomous medical treatment | OUT OF SCOPE |
| Foundation-model training | OUT OF SCOPE |
| Medical certification | OUT OF SCOPE |
| Clinical deployment without appropriate validation | OUT OF SCOPE |

---

## Traceability

All requirement identifiers (FR-xx, SR-xx, NFR-xx, KB-xx, AI-xx, UI-xx, BE-xx, SRC-xx, PR-xx) are stable and will be referenced by subsequent architecture, API specification, and testing documents to maintain traceability across the project documentation.

---

## Pending Decisions Summary

| Item | Current Status |
|---|---|
| Language-processing / translation architecture (FR-03) | TO BE DECIDED |
| Conversation-memory design (FR-11) | TO BE DECIDED |
| Measurable performance target (NFR-03) | TO BE DECIDED (after prototype) |
| Approved medical source list (KB) | TO BE DECIDED (after research) |
| LLM provider / model (AI-06) | TO BE DECIDED |
| Data-retention policy (PR-05) | TO BE DECIDED |
