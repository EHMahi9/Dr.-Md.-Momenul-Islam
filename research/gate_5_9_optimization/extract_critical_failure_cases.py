import json

with open("research/gate_5_9_optimization/evaluations/gate_5_9_2_audit_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

disagreements = data["disagreements"]
print(f"Total Disagreements: {len(disagreements)}")

gold_in_top5 = [d for d in disagreements if d["failure_classification"] == "GOLD_IN_TOP5"]
gold_outside_top5 = [d for d in disagreements if d["failure_classification"] == "GOLD_OUTSIDE_TOP5"]

print(f"  GOLD_IN_TOP5 (Reranker Selection Failure): {len(gold_in_top5)}")
print(f"  GOLD_OUTSIDE_TOP5 (Dense Recall Failure):    {len(gold_outside_top5)}")

lines = []
lines.append(f"=== CRITICAL FAILURE BREAKDOWN (N={len(disagreements)}) ===")
lines.append(f"1. GOLD_IN_TOP5 (Reranker chose wrong chunk from Top-5 pool): {len(gold_in_top5)} ({round(len(gold_in_top5)/len(disagreements)*100, 2)}%)")
lines.append(f"2. GOLD_OUTSIDE_TOP5 (Dense pool missed gold chunk entirely): {len(gold_outside_top5)} ({round(len(gold_outside_top5)/len(disagreements)*100, 2)}%)")

lines.append("\n--- REPRESENTATIVE CASES: GOLD_IN_TOP5 ---")
for d in gold_in_top5[:8]:
    lines.append(f"[{d['query_id']}] ({d['benchmark_split']}/{d['language_category']}): '{d['query_text']}'")
    lines.append(f"  Topic: {d['target_topic']}")
    lines.append(f"  Gold Chunks: {d['acceptable_gold_chunks']}")
    lines.append(f"  Top-1 Chunk:  {d['retrieved_top1_chunk_id']}")
    lines.append(f"  Dense Top-5:  {d['dense_top5_chunk_ids']}")
    lines.append(f"  Rerank Top-5: {d['r5_top5_chunk_ids']}\n")

lines.append("\n--- REPRESENTATIVE CASES: GOLD_OUTSIDE_TOP5 ---")
for d in gold_outside_top5[:8]:
    lines.append(f"[{d['query_id']}] ({d['benchmark_split']}/{d['language_category']}): '{d['query_text']}'")
    lines.append(f"  Topic: {d['target_topic']}")
    lines.append(f"  Gold Chunks: {d['acceptable_gold_chunks']}")
    lines.append(f"  Top-1 Chunk:  {d['retrieved_top1_chunk_id']}")
    lines.append(f"  Dense Top-5:  {d['dense_top5_chunk_ids']}")
    lines.append(f"  Rerank Top-5: {d['r5_top5_chunk_ids']}\n")

with open("research/gate_5_9_optimization/failure_cases_details.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("failure_cases_details.txt written.")
