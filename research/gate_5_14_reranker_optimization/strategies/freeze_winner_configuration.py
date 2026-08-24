"""
Gate 5.14 — Freezing Winning Strategy Configuration (Strategy 3: Overview De-Biased Cross-Encoder Top-5)
"""

import json
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
EVAL_FILE = os.path.join(ROOT_DIR, "evaluations", "gate_5_14_dev_reranker_comparison.json")
FROZEN_OUT = os.path.join(ROOT_DIR, "frozen_candidate", "frozen_candidate_configuration.json")

def hash_dict(d: dict) -> str:
    s = json.dumps(d, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def main():
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        all_evals = json.load(f)

    winner = all_evals["STRATEGY_3_SAME_DOC_OVERVIEW_DEBIASING"]

    config = {
        "candidate_strategy_name": "STRATEGY_3_SAME_DOC_OVERVIEW_DEBIASING",
        "description": "Deterministic Query Normalization -> Dense multilingual-e5-small (Top-15) -> bge-reranker-v2-m3 with Same-Document Overview De-Biasing (0.85x factor on chunk 000) -> Top-5 Final Context",
        "selection_rule_applied": "1. DEV Chunk Evidence Recall@5 > 2. DEV Chunk Evidence Recall@3 > 3. DEV Chunk MRR > 4. Overview Demotion Resistance > 5. Simplicity",
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
            "reranker_post_processing": {
                "overview_debiasing_enabled": True,
                "overview_chunk_suffix": "-HYB-000",
                "overview_score_multiplier": 0.85
            },
            "final_top_k_context": 5
        },
        "dev_benchmark_metrics": {
            "n_queries": 40,
            "candidate_pool_r15": "37/40 (92.50%)",
            "chunk_recall_at_1": winner["final_chunk_r1"],
            "chunk_recall_at_3": winner["final_chunk_r3"],
            "chunk_recall_at_5": winner["final_chunk_r5"],
            "mrr": winner["mrr"],
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
    print(f"  Chunk Recall@1: {winner['final_chunk_r1']}")
    print(f"  Chunk Recall@3: {winner['final_chunk_r3']}")
    print(f"  Chunk Recall@5: {winner['final_chunk_r5']}")
    print(f"  Chunk MRR:      {winner['mrr']}")

if __name__ == "__main__":
    main()
