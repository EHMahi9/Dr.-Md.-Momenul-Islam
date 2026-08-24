import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('research/gate_5_17_heading_aware_reranker/diagnostics/gate_5_17_failure_movement_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total queries with differences: {data['total_queries_with_rank_or_context_difference']}")
print(f"Improved queries ({len(data['improved_queries'])}): {data['improved_queries']}")
print(f"Degraded queries ({len(data['degraded_queries'])}): {data['degraded_queries']}")
print("=" * 90)

for diff in data['differences']:
    qid = diff['query_id']
    b_r = diff['baseline_rank']
    e_r = diff['experimental_rank']
    if diff['improved'] or diff['degraded'] or (b_r <= 5 and e_r > 5) or (b_r > 5 and e_r <= 5):
        status = "IMPROVED" if diff['improved'] else "DEGRADED"
        print(f"[{status}] {qid} ({diff['language']})")
        print(f"  Query: {diff['raw_query']}")
        print(f"  Gold CIDs: {diff['gold_chunk_ids']}")
        print(f"  Rank: Base={b_r} -> Exp={e_r}")
        print(f"  Gold Score: Base={diff['baseline_score']:.4f} -> Exp={diff['experimental_score']:.4f}")
        print(f"  Top-1: Base={diff['baseline_top1']} -> Exp={diff['experimental_top1']}")
        print(f"  Base Top-5: {diff['baseline_top5']}")
        print(f"  Exp Top-5:  {diff['experimental_top5']}")
        print("-" * 90)
