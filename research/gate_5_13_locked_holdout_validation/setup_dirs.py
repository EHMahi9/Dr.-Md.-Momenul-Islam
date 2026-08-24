import os

dirs = [
    "research/gate_5_13_locked_holdout_validation/evaluations",
    "research/gate_5_13_locked_holdout_validation/reproducibility"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("Gate 5.13 directories initialized.")
