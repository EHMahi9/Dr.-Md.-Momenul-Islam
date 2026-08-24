"""
Gate 4F.1 — Deep Audit Script: Diagnosing Heading Heuristic False Positives in Candidate A
"""

import os
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(BASE_DIR, "outputs", "candidate_a_heading", "provenance_manifest.json")
PROCESSED_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_4e_ingestion", "processed"))

with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
    chunks = json.load(f)

print(f"Total Candidate A Chunks: {len(chunks)}")

misclassified_headings = []
for c in chunks:
    lines = [l.strip() for l in c["text"].split('\n\n') if l.strip()]
    first_line = lines[0] if lines else ""
    # Check if first line is a false heading (e.g. a single word or partial phrase from inline text)
    if first_line in ['montelukast', 'paracetamol', 'ibuprofen', 'exercise', 'quit smoking', 'healthy weight', 'flu vaccine', 'acid and chemical burns', 'get help from 111 online']:
        misclassified_headings.append({
            "chunk_id": c["chunk_id"],
            "parent_source_id": c["parent_source_id"],
            "false_heading": first_line,
            "chunk_snippet": c["text"][:120].replace('\n', ' ')
        })

print(f"Found {len(misclassified_headings)} chunks starting with false headings due to inline anchor splitting:")
for m in misclassified_headings:
    print(f"  [{m['chunk_id']}] ({m['parent_source_id']}): '{m['false_heading']}' -> {m['chunk_snippet']}")
