import os

dirs = [
    "research/gate_5_17_heading_aware_reranker/baseline",
    "research/gate_5_17_heading_aware_reranker/experiment",
    "research/gate_5_17_heading_aware_reranker/comparisons",
    "research/gate_5_17_heading_aware_reranker/diagnostics"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("Gate 5.17 workspace initialized.")
