import json

with open("research/gate_5_9_optimization/evaluations/gate_5_9_locked_holdout_evaluation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Top-level keys:", data.keys())
print("\nSample query result keys:")
print(data["query_results"][0].keys())

print("\nSample query result content:")
print(json.dumps(data["query_results"][0], indent=2))
