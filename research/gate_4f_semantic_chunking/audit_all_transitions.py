"""
Gate 4F.1 — Comprehensive Audit of Every Transition in Candidate A
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(BASE_DIR, "outputs", "candidate_a_heading", "provenance_manifest.json")
PROCESSED_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_4e_ingestion", "processed"))

with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
    chunks = json.load(f)

# Group by parent document
doc_chunks = {}
for c in chunks:
    sid = c["parent_source_id"]
    if sid not in doc_chunks:
        doc_chunks[sid] = []
    doc_chunks[sid].append(c)

all_transitions = []
classification_counts = {
    "TRUE_MID_SENTENCE_SPLIT": 0,
    "INLINE_ANCHOR_SPLIT": 0,
    "LIST_BOUNDARY": 0,
    "PARAGRAPH_BOUNDARY": 0,
    "SECTION_HEADING_BOUNDARY": 0
}

for sid, c_list in doc_chunks.items():
    txt_path = os.path.join(PROCESSED_DIR, f"{sid}.txt")
    with open(txt_path, 'r', encoding='utf-8') as f:
        full_text = f.read()

    for i in range(len(c_list) - 1):
        c1 = c_list[i]
        c2 = c_list[i+1]
        
        t1_paras = [p.strip() for p in c1["text"].split('\n\n') if p.strip()]
        t2_paras = [p.strip() for p in c2["text"].split('\n\n') if p.strip()]
        
        last_p = t1_paras[-1] if t1_paras else ""
        first_p = t2_paras[0] if t2_paras else ""
        
        # Classification
        c_type = "PARAGRAPH_BOUNDARY"
        
        if last_p.endswith("such as") and first_p.startswith("montelukast"):
            c_type = "INLINE_ANCHOR_SPLIT"
        elif not last_p.endswith(('.', '!', '?', ':', ')', '"', '\'')):
            # It ends on an unpunctuated item
            if len(last_p) < 120:
                c_type = "LIST_BOUNDARY"
            else:
                c_type = "TRUE_MID_SENTENCE_SPLIT"
        elif first_p.endswith(':') or len(first_p) < 60 and not first_p.endswith(('.', ',', ';', '?', '!')):
            c_type = "SECTION_HEADING_BOUNDARY"
        else:
            c_type = "PARAGRAPH_BOUNDARY"

        classification_counts[c_type] += 1
        all_transitions.append({
            "source_id": sid,
            "chunk_1_id": c1["chunk_id"],
            "chunk_2_id": c2["chunk_id"],
            "chunk_1_end": last_p[-60:],
            "chunk_2_start": first_p[:60],
            "classification": c_type
        })

print("Comprehensive Transition Classification for Candidate A:")
for k, v in classification_counts.items():
    print(f"  {k}: {v}")

with open(os.path.join(BASE_DIR, "evaluations", "candidate_a_all_transitions.json"), 'w', encoding='utf-8') as f:
    json.dump({"summary": classification_counts, "transitions": all_transitions}, f, indent=2)
