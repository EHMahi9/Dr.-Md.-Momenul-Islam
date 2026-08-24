# Gate 4C: Controlled NHS Knowledge Ingestion Prototype

> **Status:** INGESTION PROTOTYPE COMPLETE (STOPPED)
> **Purpose:** Build and validate the document ingestion, extraction, and chunking layer using legally cleared NHS content. No LLMs, Vector DBs, or non-approved datasets were used.

## 1. Acquisition Mechanism
A custom Python ingestion script was built using `requests` and `beautifulsoup4`. 
*   It retrieves the canonical URLs with a timeout and records a UTC timestamp upon success.
*   The raw HTML is saved exactly as received into a `raw/` provenance directory.
*   It handles failures safely: if a source returns an error (e.g., 404), it logs the error, marks the document status as `FAILED`, and continues without crashing or substituting an unapproved alternative.

## 2. Extracted Document Representation
Documents were parsed from the HTML `<main>` block into a structured, hierarchical JSON format.
*   **Semantic Preservation:** The script extracts `<h2>` (Main Section), `<h3>` (Sub-section), `<p>` (Paragraphs), and `<ul>/<ol>` (Lists) sequentially. 
*   Rather than flattening the document into a blob, the parsed document remains an array of Section objects, ensuring the semantic relationships between headings and text are preserved.

## 3. Provenance Metadata
A strict provenance chain was established (`Source -> Document -> Section -> Chunk`). Every generated chunk contains a `provenance` dictionary with:
*   `source_id`, `url`, `title`, `publisher`
*   `retrieval_timestamp`
*   `licence` (Open Government Licence v3.0)
*   `attribution_required` ("Contains information from NHS England...")
*   `adaptation_status` (Adapted - HTML parsed and chunked)

## 4. Cleaning Rules
The extraction script aggressively pruned non-content elements without altering medical wording:
*   Decomposed `<nav>`, `<header>`, `<footer>`, `<script>`, and `<style>` tags.
*   Decomposed `<svg>` and `<img>` tags to ensure excluded NHS logos and trademarks were strictly removed.
*   Used regex class targeting to remove standard NHS boilerplate like "feedback", "breadcrumb", and "share" banners.
*   Did NOT paraphrase, translate, or summarize the text.

## 5. Chunking Strategies Evaluated
Three chunking mechanisms were experimentally implemented:
*   **Strategy A (Section-Based):** One chunk per `<h2>` boundary. Preserves maximum context but results in highly variable chunk sizes.
*   **Strategy B (Paragraph Groupings):** Splits sections into groups of 3 block elements. Retains the section header for each group. Provides consistent sizes while avoiding arbitrary mid-sentence cuts.
*   **Strategy C (Bounded Character/Token Limits):** Splits strictly near a character limit (500 chars), carrying over the section heading.

## 6. Chunk Statistics

| Document | Strategy | Count | Avg Size (chars) | Min Size | Max Size |
|---|---|---|---|---|---|
| DOC-NHS-001 (Heatstroke) | A (Section) | 6 | 650 | 203 | 1035 |
| DOC-NHS-001 | B (Paragraph) | 22 | 209 | 107 | 459 |
| DOC-NHS-001 | C (Bounded) | 10 | 407 | 129 | 550 |
| DOC-NHS-002 (Paracetamol) | A (Section) | 7 | 1015 | 214 | 3200 |
| DOC-NHS-002 | B (Paragraph) | 33 | 253 | 116 | 470 |
| DOC-NHS-002 | C (Bounded) | 17 | 447 | 60 | 560 |

*   **Observation:** Strategy A occasionally creates chunks too large for ideal dense vector retrieval (3,200 chars). Strategy B provides the best balance of semantic safety and size consistency.

## 7. Preserved Semantic Sections (Example)
The extraction accurately preserved hierarchical context and warnings. For example, in DOC-NHS-001, the chunk successfully links the H2 to both H3 conditions without scrambling:
```text
## Symptoms of heat exhaustion and heatstroke
### Symptoms of heat exhaustion
The symptoms of heat exhaustion include:
- tiredness
- dizziness
...
### Symptoms of heatstroke
The symptoms of heatstroke include:
- a very high temperature
...
Heatstroke is a medical emergency. Get immediate medical help if someone has the symptoms of heatstroke.
```

## 8. Rights & Attribution Handling
The mandatory OGL attribution string is carried natively inside the JSON of *every single chunk*. This guarantees that when the RAG retriever retrieves a chunk, the presentation layer has immediate access to the exact attribution string required for compliance.

## 9. Failures Encountered
*   **DOC-NHS-003 (Choking):** The URL `https://www.nhs.uk/conditions/first-aid/choking/` returned a `404 Not Found`. The NHS has likely refactored this URL.
*   **Resolution:** The acquisition mechanism failed safely, marked the document as `FAILED: 404`, skipped extraction, and proceeded without crashing the pipeline.

## 10. Recommendation for Next Technical Gate
**Gate 5 — Embedding and Vector Retrieval Strategy.**
The document ingestion, cleaning, and chunking layers are working flawlessly and map perfectly to the data model. The chunking output (especially Strategy B) is ready to be embedded. We recommend proceeding to select the embedding model, the vector database, and implementing the semantic search layer using this cleared NHS dataset.

---
**STOP CONDITION VERIFIED:** No embeddings added. No Vector DB selected. No LLM connected. No unapproved documents processed.
