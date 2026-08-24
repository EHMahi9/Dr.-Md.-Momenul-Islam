"""
Gate 5.9.2 — Audit Gold-Label Integrity
Independently verifies all 80 gold labels against HYBRID_600 provenance manifest and benchmark.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BENCHMARK_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json"))
CHUNKS_FILE = os.path.join(BASE_DIR, "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(BASE_DIR, "chunk_gold_labels.json")

def audit_gold_labels():
    if not os.path.exists(GOLD_LABELS_FILE):
        print("GOLD_LABEL_ARTIFACT_UNAVAILABLE")
        return

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunk_map = {c["chunk_id"]: c for c in chunks}

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    valid_queries = [q for q in benchmark if q["expected_source_id"] != "NONE"]

    valid_mappings = 0
    invalid_mappings = 0
    unresolved_mappings = 0
    ambiguous_mappings = 0
    multiple_gold_mappings = 0

    issues = []

    for q in valid_queries:
        qid = q["query_id"]
        expected_sid = q["expected_source_id"]

        if qid not in gold_labels:
            unresolved_mappings += 1
            issues.append(f"MISSING: Query {qid} has no gold label entry!")
            continue

        entry = gold_labels[qid]
        gold_cids = entry.get("gold_chunk_ids", [])
        topic = entry.get("target_topic", "")
        rationale = entry.get("gold_mapping_rationale", "")

        if not gold_cids:
            unresolved_mappings += 1
            issues.append(f"EMPTY: Query {qid} has empty gold_chunk_ids!")
            continue

        if len(gold_cids) > 1:
            multiple_gold_mappings += 1

        # Check existence and source alignment
        all_cids_valid = True
        for cid in gold_cids:
            if cid not in chunk_map:
                invalid_mappings += 1
                issues.append(f"INVALID_CHUNK_ID: Query {qid} references non-existent chunk {cid}!")
                all_cids_valid = False
            else:
                chunk_src = chunk_map[cid]["parent_source_id"]
                if chunk_src != expected_sid:
                    invalid_mappings += 1
                    issues.append(f"SOURCE_MISMATCH: Query {qid} expected {expected_sid} but chunk {cid} belongs to {chunk_src}!")
                    all_cids_valid = False

        if all_cids_valid:
            valid_mappings += 1

    summary = {
        "total_valid_benchmark_queries": len(valid_queries),
        "total_gold_labels_recorded": len(gold_labels),
        "valid_mappings_count": valid_mappings,
        "invalid_mappings_count": invalid_mappings,
        "unresolved_mappings_count": unresolved_mappings,
        "multiple_acceptable_chunks_count": multiple_gold_mappings,
        "integrity_status": "GOLD_LABELS_100_PERCENT_VALID" if invalid_mappings == 0 and unresolved_mappings == 0 and valid_mappings == len(valid_queries) else "INTEGRITY_FAILURES_DETECTED",
        "issues": issues
    }

    print(json.dumps(summary, indent=2))
    
    with open(os.path.join(BASE_DIR, "evaluations", "gold_label_integrity_audit_report.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    audit_gold_labels()
