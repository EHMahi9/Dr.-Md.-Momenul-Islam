"""
Gate 5.24.1 — Detailed Strategy 1 vs Strategy 5 Audit Script
"""

import json

with open('research/gate_5_24_reranker_development_research/benchmark/dev24_benchmark.json', 'r', encoding='utf-8') as f:
    bm = {q['query_id']: q for q in json.load(f)['queries']}

with open('research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json', 'r', encoding='utf-8') as f:
    chunks = {c['chunk_id']: c for c in json.load(f)}

with open('research/gate_5_24_reranker_development_research/comparisons/gate_5_24_strategy_comparison.json', 'r', encoding='utf-8') as f:
    comp = json.load(f)

s1_evals = {e['query_id']: e for e in comp['STRATEGY_1_CONTROL_BASELINE']['query_evaluations']}
s5_evals = {e['query_id']: e for e in comp['STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR']['query_evaluations']}

print("=" * 80)
print("AUDIT: ALL 6 IMPROVED / PROMOTED QUERIES UNDER STRATEGY 5")
print("=" * 80)
improved_ids = ['DEV24-AST-04', 'DEV24-BUR-04', 'DEV24-BUR-05', 'DEV24-CUT-04', 'DEV24-ANA-04', 'DEV24-ANA-05']
for qid in improved_ids:
    q = bm[qid]
    e1 = s1_evals[qid]
    e5 = s5_evals[qid]
    print(f"\n[{qid}] ({q['language']})")
    print(f"  Query: {q['query_text']}")
    print(f"  Gold: {q['gold_chunk_ids']}")
    print(f"  Dense Rank: {e1['best_dense_rank']}")
    print(f"  Baseline (S1) Rank: {e1['best_final_rank']} | S5 Rank: {e5['best_final_rank']}")
    print(f"  S1 Top-3: {e1['final_top5_cids'][:3]}")
    print(f"  S5 Top-3: {e5['final_top5_cids'][:3]}")

print("\n" + "=" * 80)
print("AUDIT: ALL 4 REGRESSED QUERIES UNDER STRATEGY 5")
print("=" * 80)
regressed_ids = ['DEV24-AST-02', 'DEV24-CUT-05', 'DEV24-DEH-04', 'DEV24-FEV-05']
for qid in regressed_ids:
    q = bm[qid]
    e1 = s1_evals[qid]
    e5 = s5_evals[qid]
    print(f"\n[{qid}] ({q['language']})")
    print(f"  Query: {q['query_text']}")
    print(f"  Gold: {q['gold_chunk_ids']}")
    print(f"  Dense Rank: {e1['best_dense_rank']}")
    print(f"  Baseline (S1) Rank: {e1['best_final_rank']} | S5 Rank: {e5['best_final_rank']}")
    print(f"  S1 Top-5: {e1['final_top5_cids']}")
    print(f"  S5 Top-5: {e5['final_top5_cids']}")
