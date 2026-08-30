# Dr. Md. Momenul Islam

**A multilingual, evidence-grounded health information system designed for Bangladesh.**

> [!WARNING]
> **Research Prototype Disclaimer:**  
> This system is an experimental software research prototype developed solely for technical and algorithmic evaluation. It is **not** a certified medical device, does **not** provide clinical diagnosis or treatment planning, and must **not** be used for medical emergencies or real-world clinical decision-making.

---

## What the System Does

The Dr. Md. Momenul Islam platform investigates trustworthy, citation-grounded clinical evidence retrieval and synthesis across multilingual queries in the Bangladesh context.

- **Multilingual Input Processing:** Accepts health queries in English, Native Bengali (বাংলা), Standard Banglish (Romanized Bengali), and Abbreviated Banglish.
- **Evidence Retrieval & Reranking:** Implements frozen Strategy 5 (`STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR`), combining dense multilingual vector retrieval (`intfloat/multilingual-e5-small`) with cross-encoder reranking (`BAAI/bge-reranker-v2-m3`).
- **Strict Provenance & Auditability:** Every retrieved chunk is cryptographically linked to its parent source document with SHA-256 checksums, URL identifiers, and section hierarchy.
- **Citation Mapping:** Generated answers map claims directly to specific retrieved chunks with section headings and verification checks.
- **Grounded Generation Architecture:** Modular LLM abstraction layer (`BaseLLMProvider`) designed for deterministic grounding, strict evidence boundary enforcement, and anti-hallucination validation.
- **Structured Retrieval & Safety States:** Classifies query-evidence relationships into explicit outcome states:
  - `SUPPORTED_BY_ACTIVE_CORPUS` (Evidence passes confidence thresholds)
  - `POSSIBLE_MISMATCH` (Borderline confidence; evidence presented with mismatch warnings)
  - `UNSUPPORTED_BY_ACTIVE_CORPUS` (Low confidence or non-corpus query; generation gated/blocked)
  - `POTENTIAL_EMERGENCY` (Emergency symptoms detected; emergency guidance prioritized)

---

## Architecture Overview

```
                          ┌───────────────────────────────────────┐
                          │   User Query (EN / বাংলা / Banglish)   │
                          └───────────────────┬───────────────────┘
                                              │
                                              ▼
                          ┌───────────────────────────────────────┐
                          │ Track A Normalization & Lexical Anchor │
                          │ (Transliteration / Token Normalizer)  │
                          └───────────────────┬───────────────────┘
                                              │
                                              ▼
                          ┌───────────────────────────────────────┐
                          │  Dense Vector Retrieval (Top-15)      │
                          │  Model: intfloat/multilingual-e5-small│
                          └───────────────────┬───────────────────┘
                                              │ Top-15 Candidate Chunks
                                              ▼
                          ┌───────────────────────────────────────┐
                          │   Cross-Encoder Reranking             │
                          │   Model: BAAI/bge-reranker-v2-m3      │
                          └───────────────────┬───────────────────┘
                                              │
                                              ▼
                          ┌───────────────────────────────────────┐
                          │   Strategy 5 Score Fusion & Debias    │
                          │   CE_deb + (λ × Dense) + (α × Lexical)│
                          └───────────────────┬───────────────────┘
                                              │ Final Top-5 Evidence
                                              ▼
                          ┌───────────────────────────────────────┐
                          │   Evidence Gating Policy (Policy C)   │
                          │   Score & Emergency Status Evaluation │
                          └─────────┬───────────────────┬─────────┘
                                    │                   │
                        Gated / Low Confidence    Sufficient Evidence
                                    │                   │
                                    ▼                   ▼
                         ┌────────────────────┐ ┌────────────────────┐
                         │ Explicit Non-Claim │ │ Grounded LLM Layer │
                         │ Gated Response     │ │ (Qwen / Local LLM) │
                         └────────────────────┘ └─────────┬──────────┘
                                                          │
                                                          ▼
                                                ┌────────────────────┐
                                                │  OutputValidator   │
                                                │ Citation & Ground- │
                                                │ ing Verification   │
                                                └─────────┬──────────┘
                                                          │
                                                          ▼
                                                ┌────────────────────┐
                                                │ React + Vite UI    │
                                                │ Citation Drawers & │
                                                │ Provenance Display │
                                                └────────────────────┘
```

---

## Technology Stack

- **Frontend:**
  - React 18 with TypeScript
  - Tailwind CSS for clinical UI layout
  - Vite for development and bundling
  - Lucide React icons
- **Backend:**
  - FastAPI (Python 3.10+)
  - Pydantic v2 schemas and validation
  - Uvicorn ASGI server
- **Retrieval & NLP Models:**
  - Dense Retriever: `intfloat/multilingual-e5-small` (384-dimensional embeddings)
  - Cross-Encoder: `BAAI/bge-reranker-v2-m3`
  - Normalization: Dual-track token normalizer and keyword anchor mapper
- **LLM Abstraction Layer:**
  - `BaseLLMProvider` interface (OpenAI-compatible API endpoints)
  - Local inference provider support (e.g., Qwen 2.5 7B Instruct via local endpoint)
  - Deterministic `OutputValidator` and citation verification pipeline

---

## Current Active Corpus

The active application corpus consists of **119 Hybrid-600 semantic chunks** derived from **14 NHS clinical evidence sources** (`DOC-NHS-004` through `DOC-NHS-017`):

| Source ID | Condition / Topic | Chunk Count |
| :--- | :--- | :--- |
| `DOC-NHS-004` | Asthma | 8 chunks |
| `DOC-NHS-005` | Burns and scalds | 7 chunks |
| `DOC-NHS-006` | Cuts and grazes | 9 chunks |
| `DOC-NHS-007` | Dehydration | 6 chunks |
| `DOC-NHS-008` | Diarrhoea and vomiting | 11 chunks |
| `DOC-NHS-009` | Headaches | 8 chunks |
| `DOC-NHS-010` | High temperature (fever) in children | 10 chunks |
| `DOC-NHS-011` | Anaphylaxis | 9 chunks |
| `DOC-NHS-012` | Chest pain | 9 chunks |
| `DOC-NHS-013` | Stroke | 7 chunks |
| `DOC-NHS-014` | Sepsis | 8 chunks |
| `DOC-NHS-015` | Meningitis | 16 chunks |
| `DOC-NHS-016` | Nosebleed | 6 chunks |
| `DOC-NHS-017` | Allergic rhinitis | 5 chunks |
| **Total** | **14 Conditions** | **119 Chunks** |

---

## Research & Development Status

- **Retrieval Pipeline:** Strategy 5 validation completed and frozen (`1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae`).
- **Gate 5.29 Holdout Validation:** Passed single-shot evaluation on 6 new NHS conditions (Recall@5: 100%, Recall@3: 95%, MRR: 0.7862).
- **Corpus Promotion (Phase 6C):** Controlled promotion of 51 research chunks into the active 119-chunk corpus completed.
- **Grounded Generation (Phase 6E/6F):** Architecture designed and evaluated across 48 multi-category development test cases (100% citation validity, 0 fabricated citations, Policy C adaptive gating selected).
- **Safety & Clinical Verification:** Incomplete. Requires formal clinical review and expanded evaluation on Bangladesh-specific clinical data.

---

## Application & Generation State

- **Corpus Lifecycle Management:** Active corpus (119 chunks) and staged research corpus tiers are isolated.
- **Generation State:** `GENERATION_ENABLED = false` by default in configuration.
- **Evidence UI:** Displays source documents, confidence scores, snippet views, and emergency warnings.

---

## Local Setup & Quickstart

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher (with npm)

### 1. Backend Setup

```bash
# Clone the repository
git clone <repo-url>
cd "Dr. Md. Momenul Islam"

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
```

The backend API will be available at `http://localhost:8000`. Interactive OpenAPI documentation is accessible at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
# In a separate terminal, navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```

The frontend application will be available at `http://localhost:5173`.

---

## Repository Structure

```
Dr. Md. Momenul Islam/
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── api/              # REST endpoint routes (/health, /corpus, /retrieval, /generation)
│   │   ├── core/             # Configuration settings, logging, and constants
│   │   ├── models/           # Domain schemas and outcome state enums
│   │   ├── schemas/          # API request and response models
│   │   ├── services/         # Retrieval, reranking, and generation services
│   │   └── templates/        # Grounded generation prompt templates
│   └── tests/                # Automated backend test suite (32 unit & integration tests)
├── frontend/                 # React + TypeScript + Vite web interface
│   ├── src/
│   │   ├── components/       # UI components (Header, Chat, EvidenceCard, ProvenanceModal)
│   │   ├── services/         # API client and streaming handler
│   │   └── types/            # TypeScript data models and API types
│   └── public/               # Static assets
├── research/                 # Phase-by-phase experimental records and evaluations
│   ├── gate_5_27_ingestion/  # Raw document ingestion & provenance manifests
│   ├── gate_5_28_benchmark/  # Locked evaluation benchmark dataset
│   ├── gate_5_29_validation/ # Single-shot holdout validation records
│   ├── phase_6C/             # Controlled corpus promotion manifests
│   ├── phase_6F_grounded_generation_evaluation/ # 48-case grounding eval suite
│   └── phase_6G_multilingual_retrieval_investigation/ # Failure analysis & traces
├── docs/                     # Architectural specifications and design records
│   └── architecture/         # System design and phase investigation reports
├── scripts/                  # Corpus verification and maintenance utilities
├── tests/                    # End-to-end and integration test harnesses
└── knowledge-base/           # Ingested clinical evidence source files
```

---

## Research Methodology

This project adheres to strict experimental hygiene principles:
1. **Cryptographic Provenance:** Every ingested document and chunk is verified with SHA-256 hashing.
2. **Deterministic Ingestion:** Fixed chunk boundaries (Hybrid-600 semantic windowing) with source attribution.
3. **Chunk-Level Evaluation:** Retrieval accuracy is evaluated against precise gold chunk targets rather than vague document matches.
4. **Frozen Benchmarks:** Validation datasets (e.g. Gate 5.28 benchmark `464612e7...`) are permanently frozen before evaluation.
5. **Holdout Separation:** New evidence sources are evaluated on unseen queries before corpus promotion.
6. **Single-Shot Validations:** Test runs are executed exactly once without post-hoc hyperparameter tuning on test sets.

---

## Current Limitations

- **Not Clinically Validated:** The system has not undergone clinical trials or formal medical board verification.
- **Not a Diagnostic Tool:** Designed for health information retrieval, not patient diagnosis or triage.
- **Incomplete Safety Layer:** Emergency symptom detection and contraindication filtering require additional clinical review.
- **Banglish Vocabulary Coverage:** Colloquial and abbreviated Romanized Bengali queries exhibit lower retrieval recall due to unmapped vocabulary in Track A normalization.
- **Corpus Breadth:** The active corpus is currently limited to 14 NHS first-aid and common acute conditions.

---

## Roadmap

1. **Multilingual Retrieval Refinement (Phase 6H):** Expand Banglish transliteration mappings and disambiguate keyword collisions.
2. **Clinical Safety & Grounding Audit:** Formalize clinical evaluation protocols with medical professionals.
3. **Bangladesh-Specific Sources:** Ingest trusted national health guidance (DGHS, IEDCR, national clinical protocols).
4. **Production Hardening:** Asynchronous batch inference, streaming optimization, and robust error recovery.
5. **Model Adaptation:** Explore targeted domain adaptation and fine-tuning on localized multilingual clinical corpora.

---

## License & Attribution

This project is developed for research and educational purposes. Clinical evidence sources are referenced from NHS.uk under Open Government Licence (OGL) guidelines for public health information.
