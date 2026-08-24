"""
Gate 5.12 — Freezing Winning Strategy Configuration (Candidate 2)
"""

import json
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
EVAL_FILE = os.path.join(ROOT_DIR, "evaluations", "gate_5_12_dev_strategy_comparison.json")
FROZEN_OUT = os.path.join(ROOT_DIR, "frozen_candidate", "frozen_candidate_configuration.json")

def hash_dict(d: dict) -> str:
    s = json.dumps(d, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def main():
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        all_evals = json.load(f)

    winner = all_evals["CANDIDATE_2_DETERMINISTIC_QUERY_NORM_K15"]

    config = {
        "candidate_strategy_name": "CANDIDATE_2_DETERMINISTIC_QUERY_NORM_K15",
        "description": "Deterministic Clinical Concept Normalization -> Dense multilingual-e5-small (Top-15) -> bge-reranker-v2-m3 (Top-5 Context)",
        "selection_rule_applied": "1. DEV Chunk Evidence Recall@5 > 2. DEV Chunk Evidence Recall@3 > 3. DEV Chunk MRR > 4. Bangla/Banglish Robustness > 5. Simplicity",
        "parameters": {
            "query_normalization": {
                "enabled": True,
                "type": "deterministic_rule_based_concept_dictionary",
                "non_llm": True
            },
            "embedding_model": "intfloat/multilingual-e5-small",
            "candidate_depth_k": 15,
            "passage_representation": "standard_clean_chunk_text",
            "use_bm25_union": False,
            "similarity_metric": "cosine_dot_product_normalized",
            "reranker_model": "BAAI/bge-reranker-v2-m3",
            "final_top_k_context": 5,
            "reranker_input_format": "raw_clean_chunk_text"
        },
        "dev_benchmark_metrics": {
            "n_queries": 40,
            "candidate_pool": winner["candidate_pool_metrics"],
            "final_chunk_metrics": winner["final_chunk_metrics"],
            "language_breakdown": winner["language_breakdown"]
        },
        "locked_holdout_status": "UNTOUCHED_AND_UNSEEN"
    }

    config_hash = hash_dict(config)
    config["configuration_hash"] = config_hash

    with open(FROZEN_OUT, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"Winner configuration frozen to {FROZEN_OUT}")
    print(f"Configuration Hash: {config_hash}")
    print(f"\nWinner DEV Metrics:")
    print(f"  Candidate R@15: {winner['candidate_pool_metrics']['r15']}")
    print(f"  Chunk Recall@1: {winner['final_chunk_metrics']['r1']}")
    print(f"  Chunk Recall@3: {winner['final_chunk_metrics']['r3']}")
    print(f"  Chunk Recall@5: {winner['final_chunk_metrics']['r5']}")
    print(f"  Chunk MRR:      {winner['final_chunk_metrics']['mrr']}")

if __name__ == "__main__":
    main()
