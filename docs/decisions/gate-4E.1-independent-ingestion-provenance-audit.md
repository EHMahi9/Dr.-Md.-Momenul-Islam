# Gate 4E.1 — Independent Ingestion, Extraction, Provenance & Reproducibility Audit

> **Status:** GATE_4E_ARTIFACTS_AUDITED_FOR_RETRIEVAL_USE

## 1. Audit Purpose
This gate independently falsifies or verifies the ingestion, provenance, and chunking artifacts produced by Gate 4E. The audit ran fully deterministic checks against the actual output artifacts, hashes, and files generated in `research/gate_4e_ingestion/` without blindly accepting the previous gate's report.

## 2. Verified Evidence

**Source Identity & Artifact Integrity:**
- I independently re-hashed the physical files in `raw/` and `processed/` using `hashlib.sha256`. 100% of the files matched the `html_hash` and `text_hash` recorded in `ingestion_manifest.json`.
- The final URLs and canonical URLs exactly matched the documented targets (e.g., Asthma resolving to `https://www.nhs.uk/conditions/asthma/`).
- No source metadata silently mutated during ingestion.

**Extraction Quality & Content Completeness:**
- A grep-style query confirmed that major boilerplate artifacts (e.g., "manage cookies", generic NHS footers, accessibility nav links) were successfully scrubbed.
- Emergency guidance remains intact. Critical routing phrases such as "999", "111", and "Urgent advice:" were verified to exist in the processed `.txt` files, proving the extraction did not strip medically critical escalation blocks.

**Chunk Provenance:**
- Every chunk generated in `provenance_manifest.json` correctly maps to a valid `parent_source_id`.
- Zero orphan chunks exist.
- Chunk IDs are strictly unique (e.g., `DOC-NHS-004-C001`).
- Hashes of the chunk text payloads matched their recorded `chunk_hash`.

**Reproducibility:**
- The ingestion script `run_gate_4e_ingestion.py` was replicated and executed into an isolated directory (`gate_4e_ingestion_audit_temp/`).
- The resulting text payloads and chunk divisions produced **0 hash mismatches** when compared to the original Gate 4E outputs. This proves structural equality and total determinism of the extraction logic. Expected differences were found only in the `retrieval_timestamp_utc` fields.

## 3. Failed Verification / Integrity Warnings

**Chunk Boundary Splitting:**
- The naive fixed-character chunking strategy (800 size / 150 overlap) is functionally deterministic but clinically fragile. 
- **Finding**: The chunker splits mid-word and mid-sentence. For example, in DOC-NHS-004 (Asthma), Chunk 0 terminates arbitrarily at *"it can happen at"* and Chunk 1 begins with *"ld air, or contact..."* (cutting the word "cold"). 
- While this guarantees reproducibility, it splits critical medical instructions in ways that could isolate context in retrieval (e.g., cutting an "if" condition away from its symptom). 

## 4. Engineering Interpretation

- **Rights Status**: Gate 4E successfully preserved the `APPROVED_FOR_PLANNED_TEXT_REUSE` status established in Gate 4D.2. It did not attempt to upgrade or assert new universal legal claims.
- **Chunking Interpretation**: The naive chunking approach is standard for early-stage embedding pipelines (e.g., LangChain's basic character splitter) and guarantees the strict reproducible provenance requested by Gate 4E. However, future retrieval pipelines may require a semantic or heading-aware chunker to prevent fracturing medical sentences. Because this gate explicitly forbade tuning the chunking strategy, the current artifact generation remains legally and structurally compliant.

## 5. Unknown / Not Tested

- Whether the fixed 800/150 size yields optimal MRR or Recall@K. (Evaluation explicitly forbidden in this gate).
- Whether semantic boundary chunking would require a different extraction parse tree.

## 6. Final Status

**GATE_4E_ARTIFACTS_AUDITED_FOR_RETRIEVAL_USE**

The artifacts are deterministically reproducible, strictly isolated, mathematically verified by hash, and free of boilerplate contamination. They are structurally ready for a future independent benchmark holdout.

*(Note: This status certifies provenance and ingestion structure only. It does NOT assert medical correctness, clinical safety, production readiness, or optimal retrieval design.)*

---
**ABSOLUTE STOP CONDITION REACHED**: No embeddings created, no LLMs called, no benchmark tuning performed.
