import json
from collections import defaultdict

with open('research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json', 'r', encoding='utf-8') as f:
    bench = json.load(f)

valid = [q for q in bench if q['expected_source_id'] != 'NONE']

by_src = defaultdict(list)
for q in valid:
    by_src[q['expected_source_id']].append(q)

with open('research/gate_5_9_optimization/valid_queries_dump.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total valid queries: {len(valid)}\n")
    for sid in sorted(by_src.keys()):
        out.write(f"\n=======================================================\n")
        out.write(f"SOURCE: {sid} ({len(by_src[sid])} queries)\n")
        out.write(f"=======================================================\n")
        for q in by_src[sid]:
            out.write(f"[{q['query_id']}] ({q['benchmark_split']}/{q['language_category']}): '{q['query_text']}'\n")
            out.write(f"  Target Topic: {q['target_topic']}\n")

print("Dump of valid queries written.")
