import os

dirs = [
    "research/gate_5_20_locked_holdout_validation/integrity",
    "research/gate_5_20_locked_holdout_validation/evaluations",
    "research/gate_5_20_locked_holdout_validation/diagnostics"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("Gate 5.20 workspace initialized.")
