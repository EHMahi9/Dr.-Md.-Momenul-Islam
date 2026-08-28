import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.join(BASE_DIR, "research", "gate_5_9_optimization")
DIRS = [
    os.path.join(RESEARCH_DIR, "chunks"),
    os.path.join(RESEARCH_DIR, "evaluations"),
    os.path.join(RESEARCH_DIR, "logs")
]

for d in DIRS:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")
