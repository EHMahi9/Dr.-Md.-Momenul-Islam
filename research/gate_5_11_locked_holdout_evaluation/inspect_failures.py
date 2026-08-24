import json
import hashlib

def hash_file(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

with open("research/gate_5_11_locked_holdout_evaluation/evaluations/gate_5_11_locked_holdout_results.json", "r", encoding="utf-8") as f:
    res = json.load(f)

eval_file = "research/gate_5_11_locked_holdout_evaluation/evaluations/gate_5_11_locked_holdout_results.json"
eval_hash = hash_file(eval_file)
print(f"Results File SHA-256: {eval_hash}")

# Failures (GOLD_ABSENT_FROM_TOP5)
absent_queries = [q for q in res["query_evaluations"] if q["evidence_availability"] == "GOLD_ABSENT_FROM_TOP5"]
print(f"\nTotal GOLD_ABSENT_FROM_TOP5: {len(absent_queries)} / 40")

lost_after_rerank = [q for q in absent_queries if q["dense_vs_rerank_loss"] == "GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK"]
outside_dense15 = [q for q in absent_queries if q["dense_vs_rerank_loss"] == "GOLD_OUTSIDE_DENSE15"]

print(f"  - In Dense Top-15 but dropped by Reranker: {len(lost_after_rerank)}")
print(f"  - Completely outside Dense Top-15:        {len(outside_dense15)}")

lines = []
lines.append("--- LOST AFTER RERANK ---")
for q in lost_after_rerank:
    lines.append(f"[{q['query_id']}] ({q['language_category']}): '{q['query_text']}'")
    lines.append(f"  Topic: {q['target_topic']}")
    lines.append(f"  Gold: {q['acceptable_gold_chunks']}")
    lines.append(f"  Dense Rank: {q['chunk_level']['dense_rank']}, Final Top-5: {q['final_top5_cids']}\n")

lines.append("\n--- OUTSIDE DENSE 15 ---")
for q in outside_dense15:
    lines.append(f"[{q['query_id']}] ({q['language_category']}): '{q['query_text']}'")
    lines.append(f"  Topic: {q['target_topic']}")
    lines.append(f"  Gold: {q['acceptable_gold_chunks']}")
    lines.append(f"  Dense Top-5: {q['dense_top15_cids'][:5]}\n")

with open("research/gate_5_11_locked_holdout_evaluation/holdout_failures_summary.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("holdout_failures_summary.txt written.")
