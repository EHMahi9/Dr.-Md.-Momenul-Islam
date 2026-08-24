"""
Gate 5.10 — Strategy Analysis, Winner Selection & Candidate Freezing
Ranks all evaluated strategies against the explicit selection rules and freezes the candidate configuration.
"""

import json
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
EVAL_DIR = os.path.join(BASE_DIR, "..", "evaluations")
CANDIDATE_FILE = os.path.join(EVAL_DIR, "all_strategies_dev_comparison.json")
DIAG_FILE = os.path.join(EVAL_DIR, "candidate_pool_diagnostics.json")
FROZEN_DIR = os.path.join(BASE_DIR, "..", "frozen_candidate")

def hash_dict(d: dict) -> str:
    s = json.dumps(d, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def main():
    with open(CANDIDATE_FILE, "r", encoding="utf-8") as f:
        strat_results = json.load(f)

    with open(DIAG_FILE, "r", encoding="utf-8") as f:
        diag_results = json.load(f)

    print("=== SUMMARY OF CANDIDATE POOL DIAGNOSTICS ===")
    for k, v in diag_results.items():
        print(f"{k}: R@5={v['r5']}, R@10={v['r10']}, R@15={v['r15']}, R@20={v['r20']}, MRR={v['mrr']}")

    print("\n=== SUMMARY OF POST-RERANK STRATEGIES (SORTED BY SELECTION RULE) ===")
    
    # Sort strategies by: 1. R@5, 2. R@3, 3. MRR, 4. R@1
    def sort_key(item):
        s = item[1]
        r5 = float(s["reranked_recall"]["r5_pct"])
        r3 = float(s["reranked_recall"]["r3_pct"])
        mrr = float(s["reranked_recall"]["mrr"])
        r1 = float(s["reranked_recall"]["r1_pct"])
        return (r5, r3, mrr, r1)

    sorted_strats = sorted(strat_results.items(), key=sort_key, reverse=True)

    table_rows = []
    for name, s in sorted_strats:
        r = s["reranked_recall"]
        c = s["candidate_recall"]
        mov = s["failure_movement"]
        row = {
            "Strategy": name,
            "Depth (K)": s["candidate_depth_k"],
            "Candidate R@5": f"{c['r5_count']} ({c['r5_pct']}%)",
            "Post-Rerank R@1": f"{r['r1_count']} ({r['r1_pct']}%)",
            "Post-Rerank R@3": f"{r['r3_count']} ({r['r3_pct']}%)",
            "Post-Rerank R@5": f"{r['r5_count']} ({r['r5_pct']}%)",
            "Post-Rerank MRR": r["mrr"],
            "Net Movement": f"+{mov['net_improvement']} (F->S:{mov['failure_to_success']}, S->F:{mov['success_to_failure']})"
        }
        table_rows.append(row)
        print(f"[{name}]")
        print(f"  Post-Rerank: R@5={r['r5_pct']}% | R@3={r['r3_pct']}% | MRR={r['mrr']} | R@1={r['r1_pct']}% | Net={mov['net_improvement']}")

    # Winner Analysis:
    # 1. STRATEGY_EXPANDED_DEPTH_K15 achieves R@5 = 75.00% (30/40), MRR = 0.5524, R@1 = 45.00% (18/40), R@3 = 60.00% (24/40)
    # 2. STRATEGY_SYNERGISTIC_COMBO_K10 achieves R@5 = 67.50% (27/40), R@3 = 65.00% (26/40), MRR = 0.5528, R@1 = 45.00% (18/40)
    # 3. STRATEGY_CONTEXTUAL_K10 achieves R@5 = 67.50% (27/40), R@3 = 60.00% (24/40), MRR = 0.5512, R@1 = 47.50% (19/40)
    # 4. BASELINE_STANDARD_K5: R@5 = 65.00% (26/40), R@3 = 62.50% (25/40), MRR = 0.5217, R@1 = 45.00% (18/40)

    # Let's inspect: Why does EXPANDED_DEPTH_K15 win on R@5 (75.0% vs 65.0% baseline)?
    # Because at Depth 15, the dense retriever feeds 33/40 (82.5%) valid candidate pools to the reranker!
    # And the reranker maintains 30/40 (75.0%) within Top-5!

    winner_name = sorted_strats[0][0]
    winner_obj = sorted_strats[0][1]
    print(f"\nWINNER SELECTED BY SELECTION RULE: {winner_name}")

    # Freeze candidate configuration
    frozen_config = {
        "candidate_strategy_name": winner_name,
        "selection_rule_applied": "1. Chunk R@5 > 2. Chunk R@3 > 3. Chunk MRR > 4. Chunk R@1 > 5. Complexity",
        "parameters": {
            "embedding_model": "intfloat/multilingual-e5-small",
            "reranker_model": "BAAI/bge-reranker-v2-m3",
            "chunking_algorithm": "HYBRID_600",
            "passage_representation": winner_obj["passage_representation"],
            "use_bm25_rrf": winner_obj["use_bm25_rrf"],
            "candidate_depth_k": winner_obj["candidate_depth_k"],
            "similarity_metric": "cosine_dot_product_normalized",
            "reranker_scoring_input": "raw_clean_chunk_text"
        },
        "dev_benchmark_metrics": {
            "n_queries": 40,
            "candidate_pool": winner_obj["candidate_recall"],
            "post_rerank": winner_obj["reranked_recall"],
            "failure_movement": winner_obj["failure_movement"],
            "language_breakdown": winner_obj["language_breakdown"]
        },
        "locked_holdout_status": "UNTOUCHED_AND_UNSEEN"
    }

    config_hash = hash_dict(frozen_config)
    frozen_config["configuration_hash"] = config_hash

    frozen_config_file = os.path.join(FROZEN_DIR, "frozen_candidate_configuration.json")
    with open(frozen_config_file, "w", encoding="utf-8") as f:
        json.dump(frozen_config, f, indent=2, ensure_ascii=False)

    print(f"Frozen configuration saved to {frozen_config_file}")
    print(f"Configuration Hash: {config_hash}")

if __name__ == "__main__":
    main()
