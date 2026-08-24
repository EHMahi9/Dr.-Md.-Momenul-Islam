# Project Charter: Dr. Md. Momenul Islam

## 1. Project Purpose
This project is a long-term software engineering and AI project aiming to build a Bangladesh-focused health information and guidance assistant. The system will allow users to ask health-related questions in Bangla or English and receive evidence-grounded health information based on trusted medical sources.

The system is **NOT** intended to replace doctors and must not present itself as a doctor. It should not claim a certain diagnosis from symptoms alone, independently prescribe dangerous treatments, or provide unsafe medication dosing.

The primary goal is to help users:
* Understand health information.
* Recognize potentially important warning signs.
* Understand when professional medical care may be appropriate.
* Access trustworthy health information in a simple interface.

## 2. Target Users
**Primary Users:**
* General people in Bangladesh.
* Bangla-speaking users who may find existing medical information difficult to understand.
* English-speaking users who want accessible health information.

**Secondary Stakeholders:**
* Students and researchers studying healthcare technology.
* Future medical professionals who may review or evaluate the system.
* Project developers and maintainers.

## 3. Core Value Proposition
The project combines:
1. A conversational AI interface.
2. A trusted medical knowledge base.
3. Retrieval-Augmented Generation (RAG).
4. Strong safety and uncertainty handling.
5. Bangla and English support.
6. Source attribution.

The system prioritizes trustworthy information and transparent limitations over pretending to provide a definitive medical diagnosis.

## 4. Initial Core Capabilities
The planned system will be able to:
* Accept health questions in Bangla or English.
* Accept symptom descriptions.
* Retrieve relevant information from an approved medical knowledge base.
* Generate a response using retrieved information.
* Explain uncertainty.
* Highlight relevant warning signs when appropriate.
* Provide a general urgency indication when justified.
* Encourage appropriate professional medical care.
* Show the sources used to construct the response.
* Refuse or redirect unsafe requests where necessary.

## 5. Explicit Non-Goals
The project must **NOT** initially attempt to:
* Replace a licensed doctor.
* Guarantee diagnosis.
* Independently prescribe prescription medicines.
* Determine exact medication dosage for an individual.
* Act as an autonomous emergency medical service.
* Train a foundation model from scratch.
* Build a hospital information system.
* Build a complete electronic medical record system.
* Claim clinical validation without actual evidence.
* Pretend that retrieved information guarantees a correct answer.

## 6. Learning Objective
This project serves as a personal learning project. The developer possesses basic knowledge of Python, JavaScript, HTML, CSS, TypeScript, Java, and Java OOP, but lacks deep machine-learning expertise. 

The project is designed to be built without training an AI model from scratch, focusing on understanding underlying software engineering and AI application concepts rather than copying generated code.

**Progressive Learning Path:**
API → LLM basics → FastAPI → basic AI application → document retrieval → embeddings → vector search → RAG → safety architecture → evaluation.

*Note: Complex frameworks will not be introduced before underlying concepts are understood.*

## 7. Initial Technology Direction
* **Frontend:** HTML, CSS, Vanilla JavaScript
* **Backend:** Python, FastAPI
* **AI:** Existing LLM API or an appropriate existing/open model
* **Knowledge Retrieval:** 
  * Manual basic retrieval process → Embeddings → Vector database (ChromaDB is a possible option, but *To Be Decided* as mandatory).
* **Data:** 
  * SQLite for persistent application data (initially).
  * Medical knowledge base kept strictly separate from application/user data.

*Important Constraint: Frameworks like LangChain, LlamaIndex, React, Next.js, etc., must NOT be introduced unless project documentation identifies a clear reason.*

## 8. Medical Knowledge Sources
The knowledge base will prioritize authoritative sources (e.g., WHO, government health authorities, public-health agencies, peer-reviewed literature, established clinical guidelines). 

It will **NOT** be populated with arbitrary blogs, random web pages, or unverified datasets. The exact approved source list is *To Be Decided* and will be defined in subsequent requirements and knowledge-base documentation.

## 9. Safety Requirements
Safety is a core architectural requirement. The system should:
* Clearly state it is not a doctor.
* Avoid claiming certainty when uncertainty exists.
* Detect or handle potentially urgent situations conservatively.
* Avoid unsafe prescription or dosage recommendations.
* Encourage professional medical care when appropriate.
* Distinguish general information from medical diagnosis.
* Provide citations/sources.
* Maintain a clear audit trail for evaluation.

Explicit safety tests and evaluation criteria will be included.

## 10. Two-Implementation Experiment
The project will have two concurrent implementations following the identical specification:
* **Track A — Agent Build:** Built with the help of an AI coding agent (Antigravity).
* **Track B — Manual Build:** Built manually by the developer with step-by-step teaching.

**Comparison Goals:**
Metrics for comparison include development time, feature completeness, bugs, test coverage, code quality, architecture, security, maintainability, documentation, performance, developer understanding, ease of debugging, and ease of extension. (Precise definitions are *To Be Decided* in testing/evaluation documentation).

## 11. Hard Constraints
1. Do not train a foundation model from scratch.
2. Do not make medical claims unsupported by approved sources.
3. Do not silently expand the scope.
4. Do not introduce unnecessary frameworks.
5. Keep the first implementation beginner-understandable.
6. Keep frontend and backend separated.
7. Keep medical knowledge sources separated from application/user data.
8. Never place API keys or secrets in source control.
9. Safety requirements must not be weakened to ease implementation.
10. The same core specification must be used for both agent and manual implementations.

## 12. Initial Success Criteria
The project is successful when it can:
* Accept a Bangla or English health question.
* Process the question through the backend.
* Retrieve relevant approved medical information.
* Generate a response grounded in retrieved context.
* Identify and communicate important uncertainty.
* Provide source attribution.
* Handle clearly unsafe/urgent scenarios conservatively.
* Return a usable response through the web interface.
* Pass defined safety and functional tests.

*No medical equivalence to a doctor will be claimed without independent, rigorous evaluation.*

## 13. Time / Budget
This is a student-led long-term portfolio project. The priority is learning, not speed. Development will use low-cost or free options where practical. Expensive infrastructure or GPU requirements will not be mandatory unless technically necessary.
