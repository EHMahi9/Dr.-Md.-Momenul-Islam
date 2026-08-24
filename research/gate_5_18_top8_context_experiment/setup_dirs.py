import os

dirs = [
    "research/gate_5_18_top8_context_experiment/baseline",
    "research/gate_5_18_top8_context_experiment/diagnostics",
    "research/gate_5_18_top8_context_experiment/experiment",
    "research/gate_5_18_top8_context_experiment/comparisons"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("Gate 5.18 workspace initialized.")
