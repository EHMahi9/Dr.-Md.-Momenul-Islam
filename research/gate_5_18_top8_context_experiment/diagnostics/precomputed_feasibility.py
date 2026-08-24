import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('research/gate_5_17_heading_aware_reranker/baseline/dev_baseline_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
queries = data['queries']

ranks = [q['rank'] for q in queries]
print("DEV QUERY RANKS DISTRIBUTION (N=40)")
print("=" * 60)
print(f"Total Queries: {len(ranks)}")
print(f"GOLD_IN_TOP1 (Rank 1):        {sum(1 for r in ranks if r == 1)}/40 ({sum(1 for r in ranks if r == 1)/40*100:.1f}%)")
print(f"GOLD_IN_TOP3 (Rank 1-3):      {sum(1 for r in ranks if 1 <= r <= 3)}/40 ({sum(1 for r in ranks if 1 <= r <= 3)/40*100:.1f}%)")
print(f"GOLD_IN_TOP5 (Rank 1-5):      {sum(1 for r in ranks if 1 <= r <= 5)}/40 ({sum(1 for r in ranks if 1 <= r <= 5)/40*100:.1f}%)")
print(f"GOLD_IN_TOP8 (Rank 1-8):      {sum(1 for r in ranks if 1 <= r <= 8)}/40 ({sum(1 for r in ranks if 1 <= r <= 8)/40*100:.1f}%)")
print(f"  -> Rank 6-8 increment:      {sum(1 for r in ranks if 6 <= r <= 8)}/40 ({sum(1 for r in ranks if 6 <= r <= 8)/40*100:.1f}%)")
print(f"GOLD_IN_TOP15 (Rank 1-15):    {sum(1 for r in ranks if 1 <= r <= 15)}/40 ({sum(1 for r in ranks if 1 <= r <= 15)/40*100:.1f}%)")
print(f"  -> Rank 9-15 count:         {sum(1 for r in ranks if 9 <= r <= 15)}/40 ({sum(1 for r in ranks if 9 <= r <= 15)/40*100:.1f}%)")
print(f"GOLD_OUTSIDE_TOP15 (Rank 0):  {sum(1 for r in ranks if r == 0)}/40 ({sum(1 for r in ranks if r == 0)/40*100:.1f}%)")
print("=" * 60)

print("\nQueries with Gold at Rank 6-8:")
for q in queries:
    if 6 <= q['rank'] <= 8:
        print(f"  [Rank {q['rank']}] {q['query_id']} ({q['language_category']}): {q['raw_query']}")

print("\nQueries with Gold at Rank 9-15:")
for q in queries:
    if 9 <= q['rank'] <= 15:
        print(f"  [Rank {q['rank']}] {q['query_id']} ({q['language_category']}): {q['raw_query']}")

print("\nQueries with Gold Outside Top-15:")
for q in queries:
    if q['rank'] == 0:
        print(f"  [Rank 0] {q['query_id']} ({q['language_category']}): {q['raw_query']}")
