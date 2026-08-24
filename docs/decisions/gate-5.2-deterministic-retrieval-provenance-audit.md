# Gate 5.2 — Deterministic Retrieval, Provenance & Reproducibility Audit

> **Status:** AUDIT COMPLETE (NON-LLM VALIDATION ONLY)

## 1. Current Deterministic Architecture
The existing retrieval prototype codebase (`research/gate_5_retrieval/`) outlines an architectural flow mapping query → translation → embedding → search → threshold → `NO_RELEVANT_SOURCE`. However, the current execution environment is entirely a static simulation.

## 2. Source/Provenance Audit
**Status: PASSED.**
An inspection of the ingestion output from Gate 4C (`DOC-NHS-001_chunks_A.json`, etc.) confirms that strict chunk-level provenance is implemented. Every chunk contains:
- `chunk_id` and `source_id`
- `url` (valid NHS links)
- `attribution_required` (Open Government Licence mapping)
- `retrieval_timestamp`
There are no orphaned chunks, missing metadata fields, or silent URL losses.

## 3. Chunk Reproducibility Audit
**Status: PASSED.**
The static chunk JSONs generated during Gate 4C are perfectly reproducible and deterministic. The chunk text distribution strictly honors the NHS HTML section headers, meaning the ingestion pipeline itself reliably parses identical inputs to identical JSON chunk arrays.

## 4. Embedding Configuration Audit
**Status: METHODOLOGICALLY COMPROMISED / INVALID.**
Gate 5 claimed to evaluate `BAAI/bge-small-en-v1.5`. The audit reveals that the `EmbeddingModule` implemented in `main.py` explicitly sets `self.use_mock = True` and computes similarity using a naive keyword overlap algorithm (`set(re.findall(r'\w+', t.lower()))`). No embedding model was loaded, no vectors were generated, and no real distance calculations were performed.

## 5. Translation Adapter Audit
**Status: SIMULATED / COMPROMISED.**
The `TranslationAdapter` preserves the architectural data structures (preserving original, normalized, and translated queries). However, the translation logic relies entirely on a hardcoded Python dictionary (`mock_dict` with 15 predefined strings). It cannot empirically handle malformed Banglish or meaning drift in an organic context, invalidating all previous translation performance claims.

## 6. Multilingual-E5 Methodology Audit
**Status: METHODOLOGICALLY COMPROMISED / INVALID.**
Gate 5.1 compared Candidate A (`intfloat/multilingual-e5-small`) to Candidate B (`BAAI/bge-small-en-v1.5`). The audit reveals that `evaluate_5_1.py` strictly simulated both candidates by hardcoding base scores (e.g., `base_score = 0.35` for Banglish queries). 
Crucially, the required prefixing protocol for E5 (`query:` and `passage:`) was entirely omitted in the source implementation. All previous benchmark results comparing these models must be struck from the research record as invalid.

## 7. Threshold Audit
**Status: INVALIDATED.**
Previous research claimed a threshold of `0.65` was optimal for rejecting hard negatives. This conclusion was entirely fabricated by the mock script `evaluate_5_1.py`, which manually assigned `base_score = 0.58` to hard negatives to ensure they would cleanly fail at `0.65`. The threshold has zero empirical grounding in true cosine similarity vector space.

## 8. Retrieval Determinism Results
Because the pipeline consists of static dictionary mapping and hardcoded if-statements, the retrieval pipeline is 100% deterministic (yielding identically perfect Top-1 and Top-3 stability). However, this determinism is meaningless for evaluating actual RAG vector search stability.

## 9. Failure Taxonomy
The conceptual taxonomy established in the architecture is structurally sound but was evaluated synthetically:
- `TRANSLATION_MEANING_DRIFT`
- `FALSE_RETRIEVAL`
- `FALSE_NO_RELEVANT_SOURCE`
- `OUT_OF_CORPUS_MISROUTING`
These classifications represent the correct boundaries, but their frequency (e.g., "12.5% Translation Drift") must be entirely discarded as they were derived from a 15-key mock dictionary.

## 10. Benchmark Integrity Findings
**Status: PASSED.**
The benchmark queries (`benchmark_data.json` and `benchmark_expanded_5_1.json`) themselves are structurally sound. The English, Bangla, and Banglish test cases represent real user inputs. The gold labels (`RETRIEVABLE` vs `NONE`) accurately reflect the NHS corpus boundaries. The benchmark data artifact is preserved for future true evaluation.

## 11. Corrections to Previous Retrieval Conclusions
All quantitative conclusions from Gate 5 and Gate 5.1 are formally struck down:
- The `94.7%` Recall metric for BGE-small is invalid.
- The `100%` No-Result Accuracy for Hard Negatives is invalid.
- The `0.65` Cosine Threshold calibration is invalid.
- The claim that BGE-small outperforms E5 is unproven.

## 12. Remaining Deterministic Risks
The entire pipeline (Translation → Embedding → Search) remains essentially unbuilt. Without a true embedding model and translation API, the system cannot realistically route user queries to chunks or reject hard negatives.

## 13. Recommendation for the Next NON-LLM Step
**DO NOT proceed to generation.** 
The immediate next step must be to replace the mock pipeline with actual execution code:
1. Implement a genuine Python `SentenceTransformer` implementation.
2. Integrate a true translation module (either a local lightweight translation model or an authorized API).
3. Execute the preserved 103-query benchmark empirically to capture real vector cosine similarities.
4. Establish an authentic, evidence-based similarity threshold before integrating generation.

---
**STOP CONDITION VERIFIED.** 
No LLM was called. No medical sources were added. Governing documents were unedited. Execution stopped. Awaiting independent review.
