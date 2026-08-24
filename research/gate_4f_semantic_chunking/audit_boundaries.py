"""
Gate 4F.1 — Deep Audit Script for Metric Integrity and Chunk Boundary Classification
"""

import os
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
INGESTION_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_4e_ingestion"))
PROCESSED_DIR = os.path.join(INGESTION_DIR, "processed")
MANIFEST_PATH = os.path.join(INGESTION_DIR, "ingestion_manifest.json")

def audit_candidate_a_boundaries():
    manifest_path = os.path.join(OUTPUTS_DIR, "candidate_a_heading", "provenance_manifest.json")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Group by parent document
    doc_chunks = {}
    for c in chunks:
        sid = c["parent_source_id"]
        if sid not in doc_chunks:
            doc_chunks[sid] = []
        doc_chunks[sid].append(c)

    results = []
    
    total_transitions = 0
    true_mid_sentence = 0
    paragraph_boundary = 0
    heading_boundary = 0
    list_boundary = 0

    for sid, c_list in doc_chunks.items():
        txt_path = os.path.join(PROCESSED_DIR, f"{sid}.txt")
        with open(txt_path, 'r', encoding='utf-8') as f:
            full_text = f.read()

        orig_paras = [p.strip() for p in full_text.split('\n\n') if p.strip()]

        for i in range(len(c_list) - 1):
            total_transitions += 1
            cur_c = c_list[i]["text"]
            next_c = c_list[i+1]["text"]
            
            cur_end_para = [p.strip() for p in cur_c.split('\n\n') if p.strip()][-1]
            next_start_para = [p.strip() for p in next_c.split('\n\n') if p.strip()][0]

            # Check if cur_end_para is a complete paragraph in original text
            is_full_para = cur_end_para in orig_paras
            
            # Check last character
            last_char = cur_end_para[-1] if cur_end_para else ""
            
            # Classification
            boundary_type = "UNKNOWN"
            
            if not is_full_para:
                boundary_type = "TRUE_MID_SENTENCE_SPLIT"
                true_mid_sentence += 1
            else:
                # It is a complete paragraph in the source text.
                # Is it a list item, a heading, or a regular paragraph?
                if cur_end_para.endswith(':'):
                    boundary_type = "HEADING_BOUNDARY"
                    heading_boundary += 1
                elif len(cur_end_para) < 80 and not cur_end_para.endswith(('.', '?', '!', ';')):
                    # Short non-punctuated lines in NHS markdown/text are list items
                    boundary_type = "LIST_BOUNDARY"
                    list_boundary += 1
                else:
                    boundary_type = "PARAGRAPH_BOUNDARY"
                    paragraph_boundary += 1

            results.append({
                "source_id": sid,
                "transition_index": i,
                "chunk_id_1": c_list[i]["chunk_id"],
                "chunk_id_2": c_list[i+1]["chunk_id"],
                "last_snippet": cur_end_para[-50:],
                "first_snippet_next": next_start_para[:50],
                "last_char": last_char,
                "is_full_source_paragraph": is_full_para,
                "boundary_classification": boundary_type
            })

    summary = {
        "total_chunk_transitions": total_transitions,
        "true_mid_sentence_splits": true_mid_sentence,
        "list_boundaries": list_boundary,
        "paragraph_boundaries": paragraph_boundary,
        "heading_boundaries": heading_boundary,
        "details": results
    }

    with open(os.path.join(BASE_DIR, "evaluations", "candidate_a_boundary_audit.json"), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print("Candidate A Boundary Audit Summary:")
    print(f"  Total Transitions: {total_transitions}")
    print(f"  TRUE_MID_SENTENCE_SPLIT: {true_mid_sentence}")
    print(f"  LIST_BOUNDARY: {list_boundary}")
    print(f"  PARAGRAPH_BOUNDARY: {paragraph_boundary}")
    print(f"  HEADING_BOUNDARY: {heading_boundary}")

if __name__ == "__main__":
    audit_candidate_a_boundaries()
