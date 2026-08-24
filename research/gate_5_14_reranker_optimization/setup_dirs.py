import os

dirs = [
    "research/gate_5_14_reranker_optimization/diagnostics",
    "research/gate_5_14_reranker_optimization/strategies",
    "research/gate_5_14_reranker_optimization/evaluations",
    "research/gate_5_14_reranker_optimization/frozen_candidate"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("Gate 5.14 directories initialized.")
