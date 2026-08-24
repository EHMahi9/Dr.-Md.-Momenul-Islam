import json

with open("research/gate_5_9_optimization/evaluations/gate_5_9_locked_holdout_evaluation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

lines = []
lines.append("=== SCORE DISTRIBUTIONS ===")
lines.append(json.dumps(data["score_distributions"], indent=2))

lines.append("\n=== LATENCY STATS ===")
lines.append(json.dumps(data["latency_stats"], indent=2))

lines.append("\n=== OVERALL VALID METRICS ===")
lines.append(json.dumps(data["overall_valid_metrics"], indent=2))

lines.append("\n=== DEV METRICS ===")
lines.append(json.dumps(data["dev_split_metrics"], indent=2))

lines.append("\n=== LOCKED HOLDOUT METRICS ===")
lines.append(json.dumps(data["locked_holdout_metrics"], indent=2))

lines.append("\n=== LOCKED HOLDOUT LANGUAGE BREAKDOWN ===")
lines.append(json.dumps(data["locked_holdout_language_breakdown"], indent=2))

hn_queries = [q for q in data["query_results"] if q["benchmark_split"] == "HARD_NEGATIVE"]
ooc_queries = [q for q in data["query_results"] if q["benchmark_split"] == "OUT_OF_CORPUS"]

lines.append(f"\n=== HARD NEGATIVES (N={len(hn_queries)}) ===")
for q in hn_queries:
    lines.append(f"  [{q['query_id']}] ({q['language_category']}): '{q['query_text']}' -> Dense Top1: {q['dense_top1_score']:.4f} (Src: {q['dense_top_sids'][0]}), R5 Top1: {q['r5_top1_score']:.4f}")

lines.append(f"\n=== OUT OF CORPUS (N={len(ooc_queries)}) ===")
for q in ooc_queries:
    lines.append(f"  [{q['query_id']}] ({q['language_category']}): '{q['query_text']}' -> Dense Top1: {q['dense_top1_score']:.4f} (Src: {q['dense_top_sids'][0]}), R5 Top1: {q['r5_top1_score']:.4f}")

holdout_failures = [q for q in data["query_results"] if q["benchmark_split"] == "TEST_HOLDOUT" and not q["r5_r1"]]
lines.append(f"\n=== LOCKED HOLDOUT FAILURES (N={len(holdout_failures)}) ===")
for q in holdout_failures:
    lines.append(f"  [{q['query_id']}] ({q['language_category']}): '{q['query_text']}' -> Expected: {q['expected_source_id']}, Dense Rank: {q['dense_rank']}, R5 Rank: {q['r5_rank']}")
    lines.append(f"    R5 Top1 Chunk: {repr(q['r5_top1_chunk'][:70])}")

with open("research/gate_5_9_optimization/holdout_summary.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("holdout_summary.txt written successfully.")
