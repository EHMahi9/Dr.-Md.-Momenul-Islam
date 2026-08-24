import os

dirs = [
    "research/gate_5_16_reranker_failure_analysis/reproducibility",
    "research/gate_5_16_reranker_failure_analysis/diagnostics",
    "research/gate_5_16_reranker_failure_analysis/per_query",
    "research/gate_5_16_reranker_failure_analysis/comparisons"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("Gate 5.16 workspace initialized.")
