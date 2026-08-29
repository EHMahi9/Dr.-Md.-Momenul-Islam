# Phase 6C Decision Record — Controlled Corpus Promotion

**Date:** 2026-08-29
**Decision ID:** DECISION-6C-001
**Status:** CORPUS_PROMOTION_VALIDATED

## Context

Six NHS clinical documents (DOC-NHS-012 through DOC-NHS-017) were:
1. Ingested and provenance-validated in Gate 5.27 (51 chunks)
2. Independently benchmarked in Gate 5.28 (50 queries across 4 language variants)
3. Single-shot validated in Gate 5.29 under frozen Strategy 5

Gate 5.29 results:
- Chunk Recall@5: 40/40 (100%)
- Chunk Recall@3: 38/40 (95.0%)
- Chunk Recall@1: 25/40 (62.5%)
- MRR: 0.7862
- Source Recall@1: 39/40 (97.5%)
- Dense Recall@15: 40/40 (100%)
- Classification: `NEW_CORPUS_GENERALIZATION_SUPPORTED`

## Decision

Promote all 6 validated sources from `STAGED_RESEARCH` to `ACTIVE` corpus.

## Pre-Promotion State

| Attribute | Value |
|-----------|-------|
| Active Corpus | `BASELINE_NHS_8_CONDITIONS` |
| Active Chunks | 68 |
| Active Sources | DOC-NHS-004 through DOC-NHS-011 |
| Staged Corpus | `EXPANDED_NHS_6_CONDITIONS` |
| Staged Chunks | 51 |
| Staged Sources | DOC-NHS-012 through DOC-NHS-017 |
| Version | 0.6.0-prototype |

## Post-Promotion State

| Attribute | Value |
|-----------|-------|
| Active Corpus | `NHS_14_CONDITIONS` |
| Active Chunks | 119 |
| Active Sources | DOC-NHS-004 through DOC-NHS-017 |
| Staged Corpus | `STAGED_EMPTY` |
| Staged Chunks | 0 |
| Version | 0.7.0-prototype |

## Corpus Promotion Checksums

| Artifact | SHA-256 |
|----------|---------|
| Pre-promotion active manifest | `b0fc6cb86192dd53957e873c347359bcdc6630882e3f642bc520544e57a5a803` |
| Promoted manifest (119 chunks) | `44d0602f730d6460e6fefa431bd5c09005b48ce92b47d02832532e5868d4aa58` |
| Strategy 5 config (frozen) | `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae` |
| Gate 5.28 benchmark (locked) | `464612e733aeb1496c1dcdc5674e01d9504bd4ccd1244190e487c6e957dcc722` |

## Invariants Preserved

- [x] Strategy 5 configuration untouched (same SHA-256 hash)
- [x] All 68 original active chunks preserved byte-for-byte
- [x] All 51 staged chunks included byte-for-byte
- [x] No duplicate chunk IDs across merged corpus
- [x] All provenance fields present on every chunk
- [x] LLM generation remains disabled
- [x] Rollback backup created and verified
- [x] Gate 5.29 and Gate 5.28 benchmark NOT rerun or modified
- [x] No retrieval algorithm changes

## Rollback Procedure

1. Restore `backend/app/core/config.py` to point `ACTIVE_CORPUS_MANIFEST_PATH` to `research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json`
2. Change `ACTIVE_CORPUS_NAME` back to `BASELINE_NHS_8_CONDITIONS`
3. Pre-promotion backup available at: `research/phase_6C/backups/pre_promotion_active_manifest.json`

## Validation Summary

| Step | Check | Result |
|------|-------|--------|
| 01 | Preflight audit (7 checks) | ✅ PREFLIGHT_PASSED |
| 02 | Deterministic merge | ✅ MERGE_VALIDATED |
| 03 | Regression validation (11 checks) | ✅ REGRESSION_VALIDATED |
| 04 | Pytest test suite (14 tests) | ✅ 14/14 PASSED |
| 05 | Frontend TypeScript build | ✅ 0 errors |
| 06 | Frontend Vite production build | ✅ Success |

## Score-State Language Notice

> The retrieval confidence tiers (0.65 / 0.35 / 0.18 / 0.10) used in the
> application are **engineering heuristics** derived from observed Strategy 5
> score distributions. They are NOT medically validated thresholds or safety
> boundaries. UI language explicitly avoids implying clinical certainty from
> a retrieval score.

## Final Status

```
CORPUS_PROMOTION_VALIDATED
```
