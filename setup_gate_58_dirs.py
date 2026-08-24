import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.join(BASE_DIR, "research", "gate_5_8_retrieval_validation")
DIRS = [
    os.path.join(RESEARCH_DIR, "benchmark"),
    os.path.join(RESEARCH_DIR, "evaluations"),
    os.path.join(RESEARCH_DIR, "logs")
]

for d in DIRS:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")
