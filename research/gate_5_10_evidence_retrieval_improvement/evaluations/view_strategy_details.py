import json

with open("research/gate_5_10_evidence_retrieval_improvement/evaluations/all_strategies_dev_comparison.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for name in ["BASELINE_STANDARD_K5", "STRATEGY_EXPANDED_DEPTH_K10", "STRATEGY_EXPANDED_DEPTH_K15", "STRATEGY_CONTEXTUAL_K10", "STRATEGY_HYBRID_BM25_K10", "STRATEGY_SYNERGISTIC_COMBO_K10"]:
    s = data[name]
    print(f"\n==========================================")
    print(f"STRATEGY: {name}")
    print(f"Candidate: {s['candidate_recall']}")
    print(f"Reranked:  {s['reranked_recall']}")
    print(f"Movement:  {s['failure_movement']}")
    print(f"Language Breakdown:")
    for lang, lm in s['language_breakdown'].items():
        print(f"  {lang} (N={lm['n']}): R@1={lm['r1_count']} ({lm['r1_pct']}%), R@3={lm['r3_count']} ({lm['r3_pct']}%), R@5={lm['r5_count']} ({lm['r5_pct']}%), MRR={lm['mrr']}")
