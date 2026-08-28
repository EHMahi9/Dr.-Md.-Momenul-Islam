# Application Architecture: Dr. Md. Momenul Islam Clinical Health Intelligence Prototype

## 1. System Overview

**Dr. Md. Momenul Islam** is an agentic clinical health intelligence system designed to retrieve authoritative, ground-truth medical evidence in response to multi-lingual patient queries (English, Native Bangla, and Banglish).

In **Phase 6A**, the application is structured as a **strictly decoupled local prototype** where:
- **Retrieval is live and grounded** on 68 indexed NHS UK clinical passages under Open Government Licence v3.0 (OGL v3.0).
- **LLM generation is strictly disabled** by protocol. Responses return verbatim retrieved passages and structured provenance metadata to guarantee zero hallucination risk during retrieval validation.

```text
                    Dr. Md. Momenul Islam Architecture
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
[Frontend: React 18 + TS + Tailwind]               [Backend: Python + FastAPI]
  • Multi-lingual Chat Input                         • CORS Middleware
  • Research Mode Disclaimer                         • REST API Routes (/api/v1)
  • Top-5 Evidence Viewer                            • Service Layer (Abstracted)
  • Provenance & Score Badges                        • SQLAlchemy Schema / PostgreSQL
    │                                                               │
    └─────────────────────── HTTP REST API ─────────────────────────┘
                                    │
                                    ▼
                     [Abstracted Retrieval Service]
                                    │
     ┌──────────────────────────────┴──────────────────────────────┐
     │                                                             │
     ▼                                                             ▼
[Deterministic Unicode Normalizer]               [Neural Bi-Encoder: E5-Small]
  • 9 Concept Expansion Dictionaries                • Dense Top-15 Candidate Depth
     │                                                             │
     └──────────────────────────────┬──────────────────────────────┘
                                    │
                                    ▼
                   [Cross-Encoder: BGE-Reranker-v2-m3]
                                    │
                                    ▼
                [Dual-Anchor Topical-Lexical Fusion Reranker]
                • 0.85x Overview Debiasing (-HYB-000)
                • Score = Rerank + 0.10*Dense + 0.03*Overlap
                                    │
                                    ▼
                   [Final Top-5 Grounding Evidence Context]
```

---

## 2. Component Boundaries & Isolation Rules

### A. Frontend Layer (`frontend/`)
- Built with **React 18**, **TypeScript 5**, **Vite 5**, and **Tailwind CSS 3**.
- Communicates with the backend strictly via JSON REST API calls.
- Enforces user-facing disclaimers: *"Research Prototype — Not for Medical Decision-Making. LLM generation is disabled."*
- Displays rich provenance data: Chunk ID, Source Title, Canonical NHS URL, Rerank Score, Dense Cosine Score, and Lexical Overlap.

### B. Backend API Layer (`backend/app/api/`)
- Built with **FastAPI** and **Pydantic v2**.
- Exposes three core endpoints:
  - `GET /api/v1/health` — System status, active retrieval strategy, indexed chunk count.
  - `POST /api/v1/retrieve` — Direct evidence retrieval for research and benchmarking.
  - `POST /api/v1/chat` — Research prototype chat endpoint returning grounded evidence context.

### C. Service Abstraction Layer (`backend/app/services/`)
- **`BaseRetrievalService` (Abstract Interface)**:
  ```python
  class BaseRetrievalService(ABC):
      @abstractmethod
      def retrieve(self, query: str, top_k: int = 5) -> Tuple[str, List[RetrievedEvidenceChunk]]: ...
  ```
  - Allows swapping the retrieval engine without touching API contracts, database, or frontend code.
- **`FrozenDualAnchorRetrievalService` (Active Strategy 5 Implementation)**:
  - Executes Track A Normalization $\to$ E5-small Top-15 $\to$ BGE Cross-Encoder $\to$ 0.85x Overview Debiasing $\to$ Dual-Anchor Fusion ($\lambda=0.10, \alpha=0.03$).
- **`BaseGenerationService` (Abstract Interface)**:
  - `DisabledGenerationService` explicitly enforces `generation_enabled = False`.

### D. Data & Storage Layer (`backend/app/models/`)
- **SQLAlchemy 2.0 Schema**:
  - `sources`: NHS document metadata (ID, title, canonical URL, OGL licence, attribution).
  - `chunks`: Chunk text, char length, overview flag, foreign key to sources.
  - `query_logs`: User query logs, normalized text, top chunk ID, latency in ms, strategy used.
- Designed for PostgreSQL with pgvector, fully functional with SQLite for local standalone prototyping.

---

## 3. Setup & Execution Instructions

### A. Backend Execution
```bash
# From repository root
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### B. Frontend Execution
```bash
# In a separate terminal
cd frontend
npm run dev
```
- Local UI: `http://localhost:5173`

### C. Running Automated Backend Tests
```bash
cd backend
python -m pytest tests/test_api.py -v -o pythonpath=.
```
