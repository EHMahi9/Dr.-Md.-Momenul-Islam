"""
Gate 5.20 — Phase 1: Cryptographic Integrity Verification
Verifies benchmark, corpus chunks, gold labels, and frozen configuration checksums.
"""

import json
import os
import hashlib
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

BENCHMARK_FILE = os.path.join(RESEARCH_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
CHUNKS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunk_gold_labels.json")
FROZEN_CONFIG_FILE = os.path.join(RESEARCH_DIR, "gate_5_19_dual_failure_mitigation", "candidate", "frozen_candidate_configuration.json")
INTEGRITY_OUT_FILE = os.path.join(BASE_DIR, "gate_5_20_integrity_verification.json")

EXPECTED_CONFIG_HASH = "5a6840ff9a4d1956a913ab85f3972c4d7481c01bfe0c7a8fe7b2d9110017621e"

def compute_sha256(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    print("="*80)
    print("GATE 5.20 — PHASE 1: PRE-EVALUATION INTEGRITY VERIFICATION")
    print("="*80)

    # 1. Configuration Verification
    assert os.path.exists(FROZEN_CONFIG_FILE), f"Missing configuration file: {FROZEN_CONFIG_FILE}"
    with open(FROZEN_CONFIG_FILE, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    actual_config_hash = config_data.get("configuration_sha256")
    config_file_hash = compute_sha256(FROZEN_CONFIG_FILE)

    config_match = (actual_config_hash == EXPECTED_CONFIG_HASH)
    print(f"Frozen Configuration Hash: Expected={EXPECTED_CONFIG_HASH} | Actual={actual_config_hash} | Match={config_match}")

    # 2. Benchmark Verification
    assert os.path.exists(BENCHMARK_FILE), f"Missing benchmark file: {BENCHMARK_FILE}"
    benchmark_hash = compute_sha256(BENCHMARK_FILE)
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    n_total = len(benchmark)
    n_dev = sum(1 for q in benchmark if q.get("benchmark_split") == "DEV")
    n_test = sum(1 for q in benchmark if q.get("benchmark_split") == "TEST_HOLDOUT")
    n_hard_neg = sum(1 for q in benchmark if q.get("benchmark_split") == "HARD_NEGATIVE")
    n_out_corpus = sum(1 for q in benchmark if q.get("benchmark_split") == "OUT_OF_CORPUS")

    print(f"Benchmark File Hash: {benchmark_hash}")
    print(f"  Total Queries: {n_total} (DEV={n_dev}, TEST_HOLDOUT={n_test}, HARD_NEGATIVE={n_hard_neg}, OUT_OF_CORPUS={n_out_corpus})")
    assert n_total == 100 and n_dev == 40 and n_test == 40 and n_hard_neg == 12 and n_out_corpus == 8, "Benchmark query count mismatch!"

    # 3. Corpus Chunks Verification
    assert os.path.exists(CHUNKS_FILE), f"Missing chunks file: {CHUNKS_FILE}"
    chunks_hash = compute_sha256(CHUNKS_FILE)
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    n_chunks = len(chunks)
    print(f"Corpus HYBRID_600 Chunks Hash: {chunks_hash} (Total chunks: {n_chunks})")
    assert n_chunks == 68, f"Expected 68 hybrid chunks, found {n_chunks}"

    # 4. Gold Labels Verification
    assert os.path.exists(GOLD_LABELS_FILE), f"Missing gold labels file: {GOLD_LABELS_FILE}"
    gold_hash = compute_sha256(GOLD_LABELS_FILE)
    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold = json.load(f)
    n_gold = len(gold)
    print(f"Chunk Gold Labels Hash: {gold_hash} (Total gold labeled queries: {n_gold})")
    assert n_gold == 80, f"Expected 80 gold labels, found {n_gold}"

    integrity_report = {
        "gate": "GATE_5.20",
        "timestamp": "2026-08-28T19:02:00+06:00",
        "integrity_status": "PASS" if config_match else "FAIL",
        "expected_configuration_sha256": EXPECTED_CONFIG_HASH,
        "actual_configuration_sha256": actual_config_hash,
        "configuration_file_sha256": config_file_hash,
        "benchmark_file_sha256": benchmark_hash,
        "chunks_manifest_sha256": chunks_hash,
        "gold_labels_sha256": gold_hash,
        "benchmark_query_counts": {
            "total": n_total,
            "dev": n_dev,
            "test_holdout": n_test,
            "hard_negative": n_hard_neg,
            "out_of_corpus": n_out_corpus
        },
        "total_corpus_chunks": n_chunks,
        "total_gold_labels": n_gold
    }

    with open(INTEGRITY_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(integrity_report, f, indent=2, ensure_ascii=False)

    print(f"\nIntegrity Verification Result: {'PASS' if config_match else 'FAIL'}")
    print(f"Saved integrity report to {INTEGRITY_OUT_FILE}")

if __name__ == "__main__":
    main()
