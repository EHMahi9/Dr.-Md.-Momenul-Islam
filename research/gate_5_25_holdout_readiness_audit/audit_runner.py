"""
Gate 5.25 — Fresh Holdout Availability & Evaluation-Readiness Audit
Gathers exact inventory of all consumed and untouched datasets.
"""

import json
import os
import glob
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
AUDIT_OUT_DIR = os.path.join(RESEARCH_DIR, "gate_5_25_holdout_readiness_audit")
os.makedirs(AUDIT_OUT_DIR, exist_ok=True)

# 1. Inventory of Consumed Benchmarks
consumed_benchmarks = [
    {
        "file": "research/gate_4c_ingestion/benchmark.json",
        "name": "Gate 4c Ingestion Feasibility Benchmark",
        "total_queries": 10,
        "purpose": "Early ingestion & translation feasibility",
        "sources": ["DOC-NHS-001", "DOC-NHS-002", "DOC-NHS-003"],
        "status": "CONSUMED_HISTORICAL"
    },
    {
        "file": "research/gate_4c_ingestion/expanded_benchmark.json",
        "name": "Gate 4c Expanded Ingestion Benchmark",
        "total_queries": 21,
        "purpose": "Multilingual vs translation comparison",
        "sources": ["DOC-NHS-001", "DOC-NHS-002", "DOC-NHS-003"],
        "status": "CONSUMED_HISTORICAL"
    },
    {
        "file": "research/gate_5_3_real_retrieval/benchmark_expanded_5_1.json",
        "name": "Gate 5.1 Retrieval Feasibility Benchmark",
        "total_queries": 103,
        "purpose": "Early real-retrieval pipeline exploration",
        "sources": ["DOC-NHS-001", "DOC-NHS-002", "DOC-NHS-003", "DOC-NHS-004", "DOC-NHS-005"],
        "status": "CONSUMED_HISTORICAL"
    },
    {
        "file": "research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json",
        "name": "Gate 5.8 Frozen Benchmark (DEV + TEST + UNSUPPORTED)",
        "total_queries": 100,
        "splits": {
            "DEV (40 queries)": "Optimized against in Gates 5.9, 5.12, 5.14, 5.16, 5.17, 5.18, 5.19, 5.21 (DOC-NHS-004 to 007)",
            "TEST_HOLDOUT (40 queries)": "Evaluated 4 times in Gates 5.11, 5.13, 5.15, 5.20 (DOC-NHS-008 to 011) - CONTAMINATED",
            "UNSUPPORTED (20 queries)": "Evaluated 4 times"
        },
        "status": "CONSUMED_AND_CONTAMINATED"
    },
    {
        "file": "research/gate_5_22_fresh_benchmark/benchmark/fresh_locked_benchmark.json",
        "name": "Gate 5.22 Fresh Locked Benchmark",
        "total_queries": 50,
        "sha256": "a0267355615d9094fd9698ff0bbb5d9aa69311a9c822e1cd47ac12fc08573ef6",
        "sources": ["DOC-NHS-004" ,"DOC-NHS-005", "DOC-NHS-006", "DOC-NHS-007", "DOC-NHS-008", "DOC-NHS-009", "DOC-NHS-010", "DOC-NHS-011"],
        "purpose": "Single-shot evaluation of Gate 5.21 candidate in Gate 5.23",
        "status": "CONSUMED_AND_PERMANENTLY_LOCKED"
    },
    {
        "file": "research/gate_5_24_reranker_development_research/benchmark/dev24_benchmark.json",
        "name": "Gate 5.24 DEV-24 Development Benchmark",
        "total_queries": 40,
        "sha256": "4d28ccfc59be69e2e790fb89ad71fc47479e8d92889c61a069d0af238750e485",
        "sources": ["DOC-NHS-004", "DOC-NHS-005", "DOC-NHS-006", "DOC-NHS-007", "DOC-NHS-008", "DOC-NHS-009", "DOC-NHS-010", "DOC-NHS-011"],
        "purpose": "Reranker diagnostic research and Strategy 5 development selection",
        "status": "CONSUMED_DEVELOPMENT_SET"
    }
]

# 2. Document Exposure Summary
doc_exposure = {
    "DOC-NHS-004": {"title": "Asthma", "chunks": 18, "query_evaluations": 20, "splits_used": ["Gate 5.8 DEV", "Gate 5.22 FRESH", "Gate 5.24 DEV-24"]},
    "DOC-NHS-005": {"title": "Burns and scalds", "chunks": 5, "query_evaluations": 20, "splits_used": ["Gate 5.8 DEV", "Gate 5.22 FRESH", "Gate 5.24 DEV-24"]},
    "DOC-NHS-006": {"title": "Cuts and grazes", "chunks": 7, "query_evaluations": 20, "splits_used": ["Gate 5.8 DEV", "Gate 5.22 FRESH", "Gate 5.24 DEV-24"]},
    "DOC-NHS-007": {"title": "Dehydration", "chunks": 8, "query_evaluations": 20, "splits_used": ["Gate 5.8 DEV", "Gate 5.22 FRESH", "Gate 5.24 DEV-24"]},
    "DOC-NHS-008": {"title": "Diarrhoea and vomiting", "chunks": 8, "query_evaluations": 20, "splits_used": ["Gate 5.8 TEST (4x)", "Gate 5.22 FRESH", "Gate 5.24 DEV-24"]},
    "DOC-NHS-009": {"title": "Headaches", "chunks": 5, "query_evaluations": 20, "splits_used": ["Gate 5.8 TEST (4x)", "Gate 5.22 FRESH", "Gate 5.24 DEV-24"]},
    "DOC-NHS-010": {"title": "High temperature (fever) in children", "chunks": 7, "query_evaluations": 20, "splits_used": ["Gate 5.8 TEST (4x)", "Gate 5.22 FRESH", "Gate 5.24 DEV-24"]},
    "DOC-NHS-011": {"title": "Anaphylaxis", "chunks": 10, "query_evaluations": 20, "splits_used": ["Gate 5.8 TEST (4x)", "Gate 5.22 FRESH", "Gate 5.24 DEV-24"]}
}

audit_data = {
    "gate": "GATE_5.25",
    "audit_type": "HOLDOUT_AVAILABILITY_AND_READINESS_AUDIT",
    "timestamp": "2026-08-28T22:01:00Z",
    "strategy_under_evaluation": {
        "name": "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR",
        "config_file": "research/gate_5_24_reranker_development_research/candidate/strategy_5_dev_candidate_configuration.json",
        "current_status": "DEVELOPMENT_CANDIDATE_UNVALIDATED_ON_HOLDOUT"
    },
    "consumed_benchmarks": consumed_benchmarks,
    "document_exposure": doc_exposure,
    "untouched_holdout_exists": False,
    "findings": {
        "pre_existing_untouched_holdouts_count": 0,
        "source_unseen_status": "All 8 active corpus documents have been exposed to multiple evaluation rounds",
        "holdout_requirement": "A completely new, independent holdout must be constructed. For source-level generalization, fresh unseen NHS clinical documents must be ingested and indexed."
    }
}

out_file = os.path.join(AUDIT_OUT_DIR, "gate_5_25_holdout_readiness_audit.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(audit_data, f, indent=2, ensure_ascii=False)

print(f"Audit data written to: {out_file}")
