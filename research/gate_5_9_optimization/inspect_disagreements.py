import json

with open("research/gate_5_9_optimization/evaluations/gate_5_9_1_chunk_level_audit_results.json", "r", encoding="utf-8") as f:
    audit = json.load(f)

lines = []
lines.append("=== CHUNK-LEVEL AUDIT SUMMARY ===")
lines.append(f"Total Valid Queries: {audit['overall_metrics']['n']}")
lines.append(f"Source-Level R@1: {audit['overall_metrics']['source_level']['r5_R1']}%")
lines.append(f"Chunk-Level R@1:  {audit['overall_metrics']['chunk_level']['r5_R1']}%")
lines.append(f"Disagreements:    {audit['overall_metrics']['disagreement_count']} ({audit['overall_metrics']['disagreement_rate_pct']}%)")

lines.append("\n=== LOCKED HOLDOUT LANGUAGE BREAKDOWN ===")
lines.append(json.dumps(audit["locked_holdout_language_breakdown"], indent=2))

lines.append("\n=== FULL CORPUS LANGUAGE BREAKDOWN ===")
lines.append(json.dumps(audit["full_corpus_language_breakdown"], indent=2))

lines.append(f"\n=== DISAGREEMENT CASES (N={len(audit['disagreement_cases'])}) ===")
for c in audit["disagreement_cases"]:
    lines.append(f"\n[{c['query_id']}] ({c['split']}/{c['language']}): '{c['query_text']}'")
    lines.append(f"  Source: {c['expected_source']}")
    lines.append(f"  Acceptable Gold Chunks: {c['acceptable_gold_chunks']}")
    lines.append(f"  Retrieved Top-1 Chunk:  {c['retrieved_top1_chunk_id']}")
    lines.append(f"  Retrieved Chunk Text:   {repr(c['retrieved_top1_chunk_text'][:120])}")

with open("research/gate_5_9_optimization/disagreements_summary.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("disagreements_summary.txt written.")
