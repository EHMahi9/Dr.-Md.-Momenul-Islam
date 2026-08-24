import os

dirs = [
    "research/gate_5_12_retrieval_failure_decomposition/baseline",
    "research/gate_5_12_retrieval_failure_decomposition/diagnostics",
    "research/gate_5_12_retrieval_failure_decomposition/strategies",
    "research/gate_5_12_retrieval_failure_decomposition/evaluations",
    "research/gate_5_12_retrieval_failure_decomposition/frozen_candidate"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("Gate 5.12 directories initialized.")
