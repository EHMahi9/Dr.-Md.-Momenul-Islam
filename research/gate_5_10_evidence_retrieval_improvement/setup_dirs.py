import os

dirs = [
    "research/gate_5_10_evidence_retrieval_improvement/baseline",
    "research/gate_5_10_evidence_retrieval_improvement/diagnostics",
    "research/gate_5_10_evidence_retrieval_improvement/strategies",
    "research/gate_5_10_evidence_retrieval_improvement/evaluations",
    "research/gate_5_10_evidence_retrieval_improvement/frozen_candidate"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("Directories initialized.")
