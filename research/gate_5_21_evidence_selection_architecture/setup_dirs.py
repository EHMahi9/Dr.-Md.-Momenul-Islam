import os

dirs = [
    "research/gate_5_21_evidence_selection_architecture/baseline",
    "research/gate_5_21_evidence_selection_architecture/diagnostics",
    "research/gate_5_21_evidence_selection_architecture/experiments",
    "research/gate_5_21_evidence_selection_architecture/comparisons",
    "research/gate_5_21_evidence_selection_architecture/candidate"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("Gate 5.21 workspace initialized.")
