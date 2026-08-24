import json

with open("research/gate_5_9_optimization/evaluations/gate_5_9_2_audit_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== DEV LANGUAGE BREAKDOWN ===")
for lang, m in data["dev_language_breakdown"].items():
    print(f"\n--- {lang} (N={m['n']}) ---")
    print(f"  Source R@1: Dense={m['source_level']['dense_r1_count']} ({m['source_level']['dense_r1_pct']}%), R5={m['source_level']['r5_r1_count']} ({m['source_level']['r5_r1_pct']}%)")
    print(f"  Chunk Dense: R@1={m['chunk_level_dense']['r1_count']} ({m['chunk_level_dense']['r1_pct']}%), R@3={m['chunk_level_dense']['r3_count']} ({m['chunk_level_dense']['r3_pct']}%), R@5={m['chunk_level_dense']['r5_count']} ({m['chunk_level_dense']['r5_pct']}%), MRR={m['chunk_level_dense']['mrr']}")
    print(f"  Chunk Rerank: R@1={m['chunk_level_r5']['r1_count']} ({m['chunk_level_r5']['r1_pct']}%), R@3={m['chunk_level_r5']['r3_count']} ({m['chunk_level_r5']['r3_pct']}%), R@5={m['chunk_level_r5']['r5_count']} ({m['chunk_level_r5']['r5_pct']}%), MRR={m['chunk_level_r5']['mrr']}")

print("\n\n=== LOCKED HOLDOUT LANGUAGE BREAKDOWN ===")
for lang, m in data["locked_holdout_language_breakdown"].items():
    print(f"\n--- {lang} (N={m['n']}) ---")
    print(f"  Source R@1: Dense={m['source_level']['dense_r1_count']} ({m['source_level']['dense_r1_pct']}%), R5={m['source_level']['r5_r1_count']} ({m['source_level']['r5_r1_pct']}%)")
    print(f"  Chunk Dense: R@1={m['chunk_level_dense']['r1_count']} ({m['chunk_level_dense']['r1_pct']}%), R@3={m['chunk_level_dense']['r3_count']} ({m['chunk_level_dense']['r3_pct']}%), R@5={m['chunk_level_dense']['r5_count']} ({m['chunk_level_dense']['r5_pct']}%), MRR={m['chunk_level_dense']['mrr']}")
    print(f"  Chunk Rerank: R@1={m['chunk_level_r5']['r1_count']} ({m['chunk_level_r5']['r1_pct']}%), R@3={m['chunk_level_r5']['r3_count']} ({m['chunk_level_r5']['r3_pct']}%), R@5={m['chunk_level_r5']['r5_count']} ({m['chunk_level_r5']['r5_pct']}%), MRR={m['chunk_level_r5']['mrr']}")
