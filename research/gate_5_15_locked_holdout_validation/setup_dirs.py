import os

dirs = [
    "research/gate_5_15_locked_holdout_validation/integrity",
    "research/gate_5_15_locked_holdout_validation/evaluations"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created directory: {d}")

print("Gate 5.15 directories initialized.")
