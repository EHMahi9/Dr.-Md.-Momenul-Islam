import os

dirs = [
    "research/gate_5_19_dual_failure_mitigation/baseline",
    "research/gate_5_19_dual_failure_mitigation/track_a_dense_normalization",
    "research/gate_5_19_dual_failure_mitigation/track_b_reranker_mitigation",
    "research/gate_5_19_dual_failure_mitigation/combined_evaluations",
    "research/gate_5_19_dual_failure_mitigation/safety_evaluations",
    "research/gate_5_19_dual_failure_mitigation/comparisons"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("Gate 5.19 workspace initialized.")
