import json

with open('research/gate_5_19_dual_failure_mitigation/comparisons/gate_5_19_mitigation_strategies_comparison.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"{'Strategy Name':<42} | {'Dense R@15':<12} | {'Chunk R@1':<12} | {'Chunk R@3':<12} | {'Chunk R@5':<12} | {'Chunk MRR':<10}")
print("=" * 105)
for s_name, s in data.items():
    print(f"{s_name:<42} | {s['dense_r15_count']:<12} | {s['chunk_r1_count']:<12} | {s['chunk_r3_count']:<12} | {s['chunk_r5_count']:<12} | {s['chunk_mrr']:<10}")

print("\n" + "=" * 105)
print("LANGUAGE BREAKDOWN FOR WINNING CANDIDATE: STRATEGY_2_TRACK_A_ROBUST_NORM")
print("=" * 105)
strat2 = data["STRATEGY_2_TRACK_A_ROBUST_NORM"]
for lang, stats in strat2["language_breakdown"].items():
    print(f"[{lang}] (N={stats['n']}):")
    print(f"  Dense R@15: {stats['dense_r15']}")
    print(f"  Chunk R@1:  {stats['r1_count']} ({stats['r1_pct']}%)")
    print(f"  Chunk R@3:  {stats['r3_count']} ({stats['r3_pct']}%)")
    print(f"  Chunk R@5:  {stats['r5_count']} ({stats['r5_pct']}%)")
    print(f"  Chunk MRR:  {stats['mrr']}")
