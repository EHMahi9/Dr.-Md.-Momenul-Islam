import json

with open('research/gate_5_8_retrieval_validation/evaluations/gate_5_8_candidate_a_v2_eval.json', 'r', encoding='utf-8') as f:
    cand_a = json.load(f)

with open('research/gate_5_8_retrieval_validation/evaluations/gate_5_8_baseline_fixed_eval.json', 'r', encoding='utf-8') as f:
    base = json.load(f)

print("=== SCORE DISTRIBUTIONS (Candidate A V2) ===")
print(json.dumps(cand_a['score_distributions'], indent=2))

print("\n=== SCORE DISTRIBUTIONS (Baseline Fixed) ===")
print(json.dumps(base['score_distributions'], indent=2))

print("\n=== LATENCY STATS (Candidate A V2) ===")
print(json.dumps(cand_a['latency_stats'], indent=2))

print(f"\n=== DEGRADATION CASES (Candidate A V2: N={len(cand_a['degradation_cases'])}) ===")
for d in cand_a['degradation_cases']:
    print(f"  [{d['query_id']}] ({d['language']}): '{d['query_text']}' -> Dense Rank: {d['dense_rank']}, Rerank Rank: {d['r5_rank']}")
    print(f"    Dense Top:  {repr(d['dense_top_chunk'][:60])}")
    print(f"    Rerank Top: {repr(d['rerank_top_chunk'][:60])}")

print(f"\n=== DEGRADATION CASES (Baseline Fixed: N={len(base['degradation_cases'])}) ===")
for d in base['degradation_cases']:
    print(f"  [{d['query_id']}] ({d['language']}): '{d['query_text']}' -> Dense Rank: {d['dense_rank']}, Rerank Rank: {d['r5_rank']}")
