import json

with open('research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json', 'r', encoding='utf-8') as f:
    bench = json.load(f)

valid = [q for q in bench if q['expected_source_id'] != 'NONE']

with open('research/gate_5_9_optimization/exact_queries.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total valid queries: {len(valid)}\n")
    for q in valid:
        out.write(f"[{q['query_id']}] ({q['benchmark_split']}/{q['language_category']}): '{q['query_text']}'\n")
        out.write(f"  Target Topic: {q['target_topic']}\n")
        out.write(f"  Expected Source: {q['expected_source_id']}\n\n")

print("exact_queries.txt written.")
