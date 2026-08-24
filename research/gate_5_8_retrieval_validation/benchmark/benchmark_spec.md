# Gate 5.8 — Benchmark Specification Document

> **Benchmark Version:** 1.0 (Frozen)
> **Total Queries:** 100
> **SHA-256 Hash:** `7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81`

## 1. Composition
- **Development Sources (40 queries)**: Asthma (10), Burns (10), Cuts (10), Dehydration (10)
- **Held-Out Test Sources (40 queries)**: Diarrhoea (10), Headaches (10), Child Fever (10), Anaphylaxis (10)
- **Hard Negatives (12 queries)**: Semantically aligned but unsupported in the corpus
- **Out-of-Corpus (8 queries)**: Unrelated clinical topics (Malaria, Rabies, Dental, Fracture, Glaucoma)

## 2. Linguistic Breakdown
- English: 25 queries
- Native Bangla: 25 queries
- Standard Banglish: 25 queries
- Abbreviated / Colloquial Banglish: 25 queries

## 3. Partitioning
- **DEV Set**: 40 queries (Targeting DOC-NHS-004 to DOC-NHS-007)
- **TEST_HOLDOUT Set**: 40 queries (Targeting DOC-NHS-008 to DOC-NHS-011)
- **HARD_NEGATIVE Set**: 12 queries
- **OUT_OF_CORPUS Set**: 8 queries
