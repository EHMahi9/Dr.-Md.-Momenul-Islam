import os

dirs = [
    "research/gate_5_11_locked_holdout_evaluation/evaluations",
    "research/gate_5_11_locked_holdout_evaluation/reproducibility"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("Gate 5.11 directories initialized.")
