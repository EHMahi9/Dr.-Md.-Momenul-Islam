"""
Gate 5.15 — Phase 1: Pre-Evaluation Integrity Verification
"""

import json
import os
import hashlib
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

FROZEN_CONFIG_FILE = os.path.join(ROOT_DIR, "research", "gate_5_14_reranker_optimization", "frozen_candidate", "frozen_candidate_configuration.json")
BENCHMARK_FILE = os.path.join(ROOT_DIR, "research", "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
CHUNKS_FILE = os.path.join(ROOT_DIR, "research", "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(ROOT_DIR, "research", "gate_5_9_optimization", "chunk_gold_labels.json")
INTEGRITY_OUT_FILE = os.path.join(BASE_DIR, "integrity", "gate_5_15_integrity_verification.json")

EXPECTED_BENCHMARK_HASH = "7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81"
EXPECTED_CONFIG_HASH = "a79e7a0eca3e7617d2e87ef920ef916edfa680011ae3e8bbc906f29dfcb4f79e"

def hash_file(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def hash_dict(d: dict) -> str:
    s = json.dumps(d, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def main():
    print("="*80)
    print("GATE 5.15 — PHASE 1: PRE-EVALUATION INTEGRITY VERIFICATION")
    print("="*80)

    report = {
        "gate": "GATE_5.15",
        "timestamp": "2026-08-22T12:40:30+06:00",
        "checks": {}
    }

    # 1. Check frozen configuration file existence
    if not os.path.exists(FROZEN_CONFIG_FILE):
        print(f"[FAIL] Frozen configuration file not found: {FROZEN_CONFIG_FILE}")
        sys.exit(1)

    with open(FROZEN_CONFIG_FILE, "r", encoding="utf-8") as f:
        frozen_config = json.load(f)

    # Compute configuration content hash (excluding the hash key itself)
    config_copy = {k: v for k, v in frozen_config.items() if k != "configuration_hash"}
    computed_config_hash = hash_dict(config_copy)
    stored_config_hash = frozen_config.get("configuration_hash")

    print(f"Frozen Config Stored Hash:   {stored_config_hash}")
    print(f"Frozen Config Computed Hash: {computed_config_hash}")

    config_hash_match = (stored_config_hash == EXPECTED_CONFIG_HASH) and (computed_config_hash == EXPECTED_CONFIG_HASH)
    report["checks"]["frozen_configuration_hash"] = {
        "expected": EXPECTED_CONFIG_HASH,
        "actual_stored": stored_config_hash,
        "actual_computed": computed_config_hash,
        "status": "PASS" if config_hash_match else "FAIL"
    }

    if not config_hash_match:
        print("[FAIL] Configuration hash mismatch!")
        sys.exit(1)
    print("[PASS] Frozen configuration SHA-256 verified exactly.")

    # 2. Check Benchmark Hash
    actual_benchmark_hash = hash_file(BENCHMARK_FILE)
    benchmark_hash_match = (actual_benchmark_hash == EXPECTED_BENCHMARK_HASH)
    report["checks"]["frozen_benchmark_hash"] = {
        "expected": EXPECTED_BENCHMARK_HASH,
        "actual": actual_benchmark_hash,
        "status": "PASS" if benchmark_hash_match else "FAIL"
    }
    if not benchmark_hash_match:
        print("[FAIL] Benchmark hash mismatch!")
        sys.exit(1)
    print("[PASS] Frozen benchmark SHA-256 verified.")

    # 3. Verify parameter specifications
    params = frozen_config["parameters"]
    param_checks = {
        "candidate_strategy_name": frozen_config.get("candidate_strategy_name") == "STRATEGY_3_SAME_DOC_OVERVIEW_DEBIASING",
        "embedding_model": params.get("embedding_model") == "intfloat/multilingual-e5-small",
        "candidate_depth_k": params.get("candidate_depth_k") == 15,
        "reranker_model": params.get("reranker_model") == "BAAI/bge-reranker-v2-m3",
        "overview_debiasing_enabled": params.get("reranker_post_processing", {}).get("overview_debiasing_enabled") == True,
        "overview_chunk_suffix": params.get("reranker_post_processing", {}).get("overview_chunk_suffix") == "-HYB-000",
        "overview_score_multiplier": params.get("reranker_post_processing", {}).get("overview_score_multiplier") == 0.85,
        "final_top_k_context": params.get("final_top_k_context") == 5,
        "use_bm25_union": params.get("use_bm25_union") == False
    }

    all_params_pass = all(param_checks.values())
    report["checks"]["parameter_checks"] = {
        "details": param_checks,
        "status": "PASS" if all_params_pass else "FAIL"
    }
    if not all_params_pass:
        print(f"[FAIL] Parameter check failed: {param_checks}")
        sys.exit(1)
    print("[PASS] All runtime parameter specifications match frozen config.")

    # 4. Check Dataset Separation
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]
    test_queries = [q for q in benchmark if q["benchmark_split"] == "TEST_HOLDOUT"]
    hn_queries = [q for q in benchmark if q["benchmark_split"] == "HARD_NEGATIVE"]
    ooc_queries = [q for q in benchmark if q["benchmark_split"] == "OUT_OF_CORPUS"]

    separation_checks = {
        "dev_queries_count": len(dev_queries) == 40,
        "test_queries_count": len(test_queries) == 40,
        "hard_negative_count": len(hn_queries) == 12,
        "out_of_corpus_count": len(ooc_queries) == 8,
        "gate_5_14_dev_only_confirmed": frozen_config["dev_benchmark_metrics"]["n_queries"] == 40,
        "locked_holdout_untouched_flag": frozen_config["locked_holdout_status"] == "UNTOUCHED_AND_UNSEEN"
    }
    all_sep_pass = all(separation_checks.values())
    report["checks"]["dataset_separation"] = {
        "details": separation_checks,
        "status": "PASS" if all_sep_pass else "FAIL"
    }
    if not all_sep_pass:
        print(f"[FAIL] Dataset separation check failed: {separation_checks}")
        sys.exit(1)
    print("[PASS] Dataset separation & DEV-only provenance confirmed.")

    # Final Verification Verdict
    overall_status = "PASS" if (config_hash_match and benchmark_hash_match and all_params_pass and all_sep_pass) else "FAIL"
    report["overall_integrity_status"] = overall_status

    with open(INTEGRITY_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "="*80)
    print(f"INTEGRITY VERIFICATION OVERALL STATUS: {overall_status}")
    print(f"Report saved to: {INTEGRITY_OUT_FILE}")
    print("="*80)

if __name__ == "__main__":
    main()
