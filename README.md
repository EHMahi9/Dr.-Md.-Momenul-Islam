# Dr. Md. Momenul Islam

**A Bangladesh-focused Conversational, Evidence-Grounded Health Assistant (Research & Product Prototype)**

> [!WARNING]
> **Research Prototype & Medical Disclaimer [NOT CLINICALLY VALIDATED]:**  
> This system is an experimental software research and product prototype developed solely for technical, algorithmic, and conversational evaluation. It is **not** an AI doctor, is **not** a diagnostic engine, does **not** provide disease probability scores or clinical labels ("you probably have X"), does **not** prescribe treatments or medications, and is **not** a replacement for qualified clinicians. All emergency routing and clarification mechanisms are software engineering implementations and have **not** undergone clinical trials or regulatory medical validation.

---

## 1. Product Purpose & Evolution

The project has evolved from a controlled information retrieval benchmark into a **conversational, evidence-grounded health assistant prototype** designed for Bangladesh. It aims to bridge the gap between colloquial, multi-lingual, and often underspecified user queries (in English, Native Bengali বাংলা, Standard Banglish, and Abbreviated Banglish) and authoritative, verified clinical guidance from vetted sources.

### Core Design Philosophy:
- **Ask the Smallest Number of Useful Questions:** Rather than executing mechanical multi-turn interrogations, the system uses an **Adaptive Clarification Planner** to ask only high-utility questions needed for safe evidence retrieval.
- **Evidence-Grounded, Non-Diagnostic Assistance:** The system gathers observable symptoms, organizes context, and retrieves trusted passages. It never assumes clinician authority or attempts autonomous diagnosis.
- **Strict Provenance & Auditability:** Every retrieved chunk is cryptographically anchored (SHA-256) to its verified source document and section hierarchy.
- **Honest Abstention & Safety First:** When a user presents out-of-corpus symptoms or critical red flags, the system suppresses irrelevant evidence cards, prioritizes emergency guidance, or abstains transparently.

---

## 2. Project Evolution

| Stage | Focus Area | Description | Status |
| :--- | :--- | :--- | :--- |
| **Stage 1** | **Evidence Ingestion & Retrieval Research** | Controlled ingestion of NHS First Aid/acute topics with Hybrid-600 semantic windowing and SHA-256 provenance tracking. | **COMPLETED / VERIFIED** |
| **Stage 2** | **Multilingual & Banglish Retrieval** | Development of Track A normalizer, keyword anchor mapping, cross-encoder reranking, and debiased dual-anchor scoring (**Candidate B** freeze). | **COMPLETED / VERIFIED** |
| **Stage 3** | **Grounded Generation Architecture** | Implementation of `BaseLLMProvider`, deterministic `OutputValidator`, citation verification, and Policy C adaptive gating. | **COMPLETED / VERIFIED** |
| **Stage 4** | **Evidence Sufficiency & Safety Routing** | Classification into explicit states (`SUPPORTED_BY_ACTIVE_CORPUS`, `POSSIBLE_MISMATCH`, `UNSUPPORTED_BY_ACTIVE_CORPUS`, `POTENTIAL_EMERGENCY`). | **COMPLETED / VERIFIED** |
| **Stage 5** | **Conversational Clarification (Phase 7A/7B)** | Query understanding, ambiguity detection, structured conversation state, quick-select chips, and multi-turn state preservation. | **COMPLETED / VERIFIED** |
| **Stage 6** | **Adaptive Clarification (Phase 7C)** | Mathematical Question-Utility model, 4 early stopping rules, duplicate question suppression, and turn-minimization engine. | **COMPLETED / VERIFIED** |

---

## 3. Current System Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │        User Query (English / বাংলা / Banglish)         │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │             Query Understanding Service                │
                               │  - Intent & Language Detection (Auto / বাংলা / EN)     │
                               │  - Extraction (body part, duration, severity, age)     │
                               │  - Red Flag / Emergency Keyword Detection              │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │           Structured Conversation State                │
                               │  - Multi-Turn State (`ConversationContextState`)       │
                               │  - Dimension Tracking (`asked_questions`)              │
                               │  - Missing High-Value Fields Identification            │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │         Adaptive Clarification Planner (Phase 7C)      │
                               │  - 6-Factor Question-Utility Model:                    │
                               │    Utility = G_ret + G_saf + R_amb + C_corp - P_red - P_unnec│
                               │  - 4 Early Stopping Rules Evaluation                   │
                               └─────────┬──────────────────────┬───────────────────────┘
                                         │                      │
                   [Clarification Needed]│                      │[Direct / Stopped]
                                         ▼                      ▼
               ┌───────────────────────────────┐  ┌─────────────────────────────────────┐
               │    Clarification Response     │  │  Candidate B Retrieval Service      │
               │  - Highest Utility Question   │  │  - Track A Lexical Normalization    │
               │  - Observable Quick Chips     │  │  - Dense: multilingual-e5-small     │
               │  - Context Update & Loop      │  │  - Cross-Encoder: bge-reranker-v2-m3│
               └───────────────────────────────┘  │  - 0.85x Overview Debiasing         │
                                                  │  - Candidate B Dual Fusion          │
                                                  └──────────────────┬──────────────────┘
                                                                     │
                                                                     ▼
                                                  ┌─────────────────────────────────────┐
                                                  │    Evidence Sufficiency Router      │
                                                  │  - Top Rerank Threshold (>= 0.65)   │
                                                  │  - Out-of-Corpus Filter (< 0.40)    │
                                                  └─────────┬─────────┬────────┬────────┘
                                                            │         │        │
                                   ┌────────────────────────┘         │        └────────────────────────┐
                                   ▼                                  ▼                                 ▼
                     ┌───────────────────────────┐      ┌───────────────────────────┐     ┌───────────────────────────┐
                     │ Grounded Answer Response  │      │ Honest Abstention Response│     │ Emergency Response        │
                     │ - Citations & Passages    │      │ - Irrelevant Cards Hidden │     │ - Emergency Protocols     │
                     │ - Policy C Evidence Cards │      │ - Safe Non-Claim Guidance │     │ - Red Flag Escalation     │
                     │ - Medical Disclaimers     │      │ - Clinician Advisory      │     │ - Immediate Help Hotlines │
                     └───────────────────────────┘      └───────────────────────────┘     └───────────────────────────┘
```

---

## 4. Current Active Corpus & Retrieval Foundation

The active application corpus consists of **119 Hybrid-600 semantic chunks** derived from **14 verified NHS clinical evidence sources** (`DOC-NHS-004` through `DOC-NHS-017`):

| Source ID | Condition / Clinical Topic | Chunk Count |
| :--- | :--- | :--- |
| `DOC-NHS-004` | Asthma (First aid and management) | 8 chunks |
| `DOC-NHS-005` | Burns and scalds | 7 chunks |
| `DOC-NHS-006` | Cuts and grazes | 9 chunks |
| `DOC-NHS-007` | Dehydration | 6 chunks |
| `DOC-NHS-008` | Diarrhoea and vomiting | 11 chunks |
| `DOC-NHS-009` | Headaches (Tension, migraine, cluster) | 8 chunks |
| `DOC-NHS-010` | High temperature (fever) in children | 10 chunks |
| `DOC-NHS-011` | Anaphylaxis & insect bites/stings | 9 chunks |
| `DOC-NHS-012` | Chest pain (Cardiac and non-cardiac) | 9 chunks |
| `DOC-NHS-013` | Stroke (FAST recognition) | 7 chunks |
| `DOC-NHS-014` | Sepsis (Red flag indicators) | 8 chunks |
| `DOC-NHS-015` | Meningitis | 16 chunks |
| `DOC-NHS-016` | Nosebleed | 6 chunks |
| `DOC-NHS-017` | Allergic rhinitis | 5 chunks |
| **Total** | **14 Conditions** | **119 Chunks** |

### Verified Retrieval Baseline:
- **Active Strategy:** `CANDIDATE_B_CONTEXT_AWARE_DISAMBIGUATION` (independently validated from Phase 6K).
- **Candidate B Freeze SHA-256:** `92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A`.
- **Parent Strategy 5 SHA-256:** `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae`.
- **Corpus Manifest SHA-256:** `44D0602F730D6460E6FEFA431BD5C09005B48CE92B47D02832532E5868D4AA58`.

> [!NOTE]
> **Banglish Development Status:**  
> Further Banglish vocabulary expansion remains future research work and must be evaluated as a separately versioned candidate. The validated Candidate B configuration remains frozen and untouched.

---

## 5. Canonical User Flow: "amar paye betha, ki korbo?"

To demonstrate the difference between deterministic interrogation and adaptive clarification:

```
[Turn 1]: User sends: "amar paye betha, ki korbo?"
   ├── Query Understanding: Language=Banglish, Body Part="leg", Ambiguity=HIGH (Broad anatomical region).
   ├── Adaptive Planner: Scores candidates (Sub-location=0.75, Mechanism=0.65, Duration=0.35).
   ├── Question Selected: Sub-location ("পায়ের কোন অংশে ব্যথা হচ্ছে?").
   ├── Quick Chips: [পায়ের পাতা] [গোড়ালি] [পিণ্ডলি] [হাঁটু] [উরু] (Observable anatomical regions only).
   └── Context Updated: asked_questions=["sub_location"].

[Turn 2]: User clicks [গোড়ালি] and inputs: "hatar somoy mochkay gechilo"
   ├── Query Understanding: Sub-location="ankle", Mechanism="sprain/twist", Trauma=True.
   ├── Adaptive Planner:
   │    ├── Redundancy Checks: sub_location (-1.00), mechanism (-1.00).
   │    ├── Topic Coverage: Ankle sprains/twists are detected as OUT-OF-CORPUS (NHS-004..017).
   │    └── Early Stopping Rule B: UNSUPPORTED_TOPIC triggers immediately.
   └── Response: Honest abstention explaining that ankle sprains are outside the active corpus,
        suppressing irrelevant NHS burns/cuts cards, and providing general safe advice to rest,
        elevate, and seek clinical evaluation.
   └── Conversation terminates cleanly in 2 turns.
```

---

## 6. Technology Stack

- **Frontend (`frontend/`):**
  - React 18 with TypeScript 5
  - Tailwind CSS 3 for responsive clinical UI
  - Vite 5 for bundling
  - Lucide React icons
  - Deployed static SPA: [https://drmomenul.vercel.app](https://drmomenul.vercel.app)
- **Backend API (`backend/`):**
  - FastAPI (Python 3.10+)
  - Pydantic v2 schemas and validation
  - Uvicorn ASGI server
- **Retrieval & NLP Core:**
  - Dense Bi-Encoder: `intfloat/multilingual-e5-small` (384-dim embeddings)
  - Neural Cross-Encoder Reranker: `BAAI/bge-reranker-v2-m3`
  - Normalization: Dual-track token normalizer, Bangla stemmer, and Banglish transliteration map
- **Conversational & Generation Engine:**
  - Query Understanding Service (rule-based slot filling and multilingual regex)
  - Conversation State Service (Question-Utility planner, stopping rules, context tracking)
  - `BaseLLMProvider` interface (OpenAI-compatible local/remote endpoints)
  - `OutputValidator` for deterministic citation and evidence boundary verification

---

## 7. Safety, Limitations & Known Open Issues

### Engineering Validation vs. Clinical Validation:
- **Engineering Validation [VERIFIED]:** The algorithmic accuracy of retrieval (Candidate B Recall@5: 100%, MRR: 0.7862), Question-Utility scoring, duplicate question elimination (0.00%), unnecessary clarification prevention (0.00%), and schema integrity are verified via automated pytest and locked benchmark suites.
- **Clinical Validation [NOT CLINICALLY VALIDATED]:** The application has **not** been evaluated in clinical trials, has not received medical board approval, and is not certified for patient diagnosis, clinical triage, or therapy selection.

### Known Open Product/UX Issue:
- **Irrelevant Evidence Exposure on Out-of-Corpus / Boundary Queries:** Phase 7C reduced irrelevant evidence exposure from 40.0% to 16.0% on its development benchmark, but did not eliminate the issue completely. This remains a **KNOWN OPEN PRODUCT/UX ISSUE** under active algorithmic refinement.

### Key Operational Limitations:
1. **No Autonomous Diagnosis:** Clarification questions gather observable context; they do not compute diagnostic probabilities or label medical conditions.
2. **Limited Corpus Scope:** The active corpus is strictly limited to 14 NHS acute conditions. Symptoms outside these 14 conditions trigger explicit abstentions.
3. **Retrieval Evidence Non-Equivalence:** High retrieval confidence indicates textual relevance to indexed NHS passages, not medical diagnosis.
4. **Emergency Escalation:** Red flag detection is an automated software heuristic; users experiencing severe symptoms must seek emergency medical care immediately.

---

## 8. Deployment & Environment Status

| Environment | Host / URL | Role | Status |
| :--- | :--- | :--- | :--- |
| **Frontend Web App** | `https://drmomenul.vercel.app` | Interactive UI with quick chips, citations, and language selector | **DEPLOYED (Vercel SPA)** |
| **Backend API** | `http://localhost:8000` | FastAPI server with Candidate B retrieval and Adaptive Planner | **DEVELOPMENT / LOCAL RUNTIME** |
| **Production Backend** | *Pending Cloud Deployment* | Containerized microservice (e.g. Render) with cloud health checks | **NEXT (Phase 8A/8B)** |

> [!IMPORTANT]
> The backend is currently a **local/research runtime** unless independently verified otherwise. The complete end-to-end system is not yet fully production cloud-deployed.

---

## 9. Development Roadmap

### COMPLETED [VERIFIED]:
- **Phase 1–5:** Foundation, document ingestion, baseline retrieval, cross-encoder reranking, and safety routing.
- **Phase 6A–6K:** Corpus expansion (119 chunks), retrieval validation, Candidate B selection, and independent validation.
- **Phase 7A:** Query understanding, ambiguity detection, evidence sufficiency routing, and response language preference.
- **Phase 7B:** Multi-turn clarification and structured conversation state.
- **Phase 7C:** Adaptive clarification and question-utility planning.

### NEXT:
- **Phase 8A: Production Backend Deployment Preparation:**
  - Linux / cloud environment compatibility audit
  - Render deployment package configuration (Dockerfile, entrypoints)
  - Runtime model loading & corpus packaging
  - CORS, environment variables, and production health checks
  - Frontend API client configuration for remote endpoints
- **Phase 8B: Backend Deployment + Vercel ↔ Render Integration:**
  - Deployment of FastAPI backend to Render
  - Full end-to-end integration and smoke testing between `drmomenul.vercel.app` and Render backend
- **Phase 8C: Cloud Runtime & Performance Optimization:**
  - Cold-start mitigation, model caching, and latency profiling

### FUTURE:
- **Phase 8D: LLM-Assisted Conversational Generation:**
  - LLM-assisted conversational phrasing within strictly bounded evidence contexts
- **Phase 8E: Multi-Turn Grounded Generation Evaluation:**
  - End-to-end grounded generation evaluation across multi-turn dialogs
- **Later Horizons:**
  - Broader trusted-source coverage & Bangladesh-specific health guidance (DGHS, IEDCR)
  - Privacy, telemetry, audit monitoring, and formal clinical governance
  - External clinical review with qualified medical professionals

---

## 10. Quickstart & Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ (with npm)

### 1. Backend Server Setup
```bash
# Navigate to project root
cd "Dr. Md. Momenul Islam"

# Create and activate virtual environment
python -m venv .venv
.venv\Scriptsctivate       # Windows PowerShell
# source .venv/bin/activate  # Linux / macOS

# Install backend dependencies
pip install -r backend/requirements.txt

# Run FastAPI backend with Uvicorn
$env:PYTHONPATH="backend"    # Windows PowerShell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
```
The backend API is accessible at `http://localhost:8000`. Interactive OpenAPI documentation is at `http://localhost:8000/docs`.

### 2. Frontend Setup
```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```
The frontend UI is accessible at `http://localhost:5173`.

### 3. Running Automated Tests
```bash
# Run complete Phase 7C pytest test suite
$env:PYTHONPATH="backend"
pytest backend/tests/test_phase_7c_adaptive_clarification.py -v
```

---

## 11. License & Attribution

Developed for software engineering and clinical informatics research. Evidence passages are ingested from NHS.uk under the Open Government Licence v3.0 (OGL v3.0).
