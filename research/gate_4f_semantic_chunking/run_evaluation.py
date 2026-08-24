"""
Gate 4F — Comprehensive Boundary Integrity, Regression, and Reproducibility Runner.
"""

import os
import sys
import glob
import json
import hashlib
import re
from typing import List, Dict, Tuple, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strategies.chunkers import (
    chunk_baseline_fixed,
    chunk_candidate_a_heading,
    chunk_candidate_b_sentence,
    chunk_candidate_c_combined,
    hash_str,
    is_heading
)

INGESTION_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gate_4e_ingestion"))
PROCESSED_DIR = os.path.join(INGESTION_DIR, "processed")
MANIFEST_PATH = os.path.join(INGESTION_DIR, "ingestion_manifest.json")
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "outputs")
EVALS_DIR = os.path.join(os.path.dirname(__file__), "evaluations")

STRATEGIES = {
    "BASELINE_FIXED": chunk_baseline_fixed,
    "CANDIDATE_A_HEADING": chunk_candidate_a_heading,
    "CANDIDATE_B_SENTENCE": chunk_candidate_b_sentence,
    "CANDIDATE_C_COMBINED": chunk_candidate_c_combined
}

def load_source_documents() -> List[Dict[str, Any]]:
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    docs = []
    for item in manifest:
        sid = item["source_id"]
        txt_path = os.path.join(PROCESSED_DIR, f"{sid}.txt")
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        docs.append({
            "source_id": sid,
            "title": item["title"],
            "requested_url": item["requested_url"],
            "final_url": item["final_url"],
            "canonical_url": item["canonical_url"],
            "retrieval_timestamp_utc": item["retrieval_timestamp_utc"],
            "html_hash": item["html_hash"],
            "text_hash": item["text_hash"],
            "text": text
        })
    return docs

# -----------------------------------------------------------------------------
# BOUNDARY INTEGRITY EVALUATION ENGINE
# -----------------------------------------------------------------------------
def evaluate_boundary_integrity(strategy_name: str, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    fn = STRATEGIES[strategy_name]
    
    total_chunks = 0
    mid_word_splits = []
    mid_sentence_splits = []
    heading_separations = []
    orphaned_emergencies = []
    duplicate_chunks = []
    chunk_lengths = []
    
    doc_results = {}

    for doc in docs:
        sid = doc["source_id"]
        text = doc["text"]
        chunks = fn(text)
        total_chunks += len(chunks)
        
        doc_mid_word = 0
        doc_mid_sentence = 0
        doc_heading_sep = 0
        doc_orphaned_emerg = 0
        doc_duplicates = 0
        
        seen_texts = set()

        for idx, c in enumerate(chunks):
            chunk_lengths.append(len(c))
            
            # 1. Duplicate check
            if c in seen_texts:
                doc_duplicates += 1
                duplicate_chunks.append({"source_id": sid, "chunk_index": idx})
            seen_texts.add(c)

            # 2. Mid-word split detection
            # If chunk does not end on whitespace/punctuation or next chunk does not start on whitespace/start of word in original text
            # We can check if chunk starts or ends with a fragmented word
            first_word = c.strip().split()[0] if c.strip().split() else ""
            last_word = c.strip().split()[-1] if c.strip().split() else ""
            
            # Check against original text boundaries
            # If chunk is a substring of text, find its start and end in text
            c_start = text.find(c)
            if c_start != -1:
                c_end = c_start + len(c)
                # Check if c_start is mid-word in text
                if c_start > 0 and text[c_start-1].isalnum() and text[c_start].isalnum():
                    doc_mid_word += 1
                    mid_word_splits.append({
                        "source_id": sid,
                        "chunk_index": idx,
                        "position": "start",
                        "context": text[max(0, c_start-10):min(len(text), c_start+15)]
                    })
                # Check if c_end is mid-word in text
                if c_end < len(text) and text[c_end-1].isalnum() and text[c_end].isalnum():
                    doc_mid_word += 1
                    mid_word_splits.append({
                        "source_id": sid,
                        "chunk_index": idx,
                        "position": "end",
                        "context": text[max(0, c_end-15):min(len(text), c_end+10)]
                    })

            # 3. Mid-sentence split detection
            # A chunk that terminates without punctuation (. ! ? :) or ends on incomplete clause
            last_char = c.strip()[-1] if c.strip() else ""
            if last_char not in ['.', '!', '?', ':', ')', '"', '\''] and idx < len(chunks) - 1:
                # Also verify if the next character in text is not a new paragraph
                doc_mid_sentence += 1
                mid_sentence_splits.append({
                    "source_id": sid,
                    "chunk_index": idx,
                    "snippet": c.strip()[-60:]
                })

            # 4. Heading separation
            # If chunk ends with a heading without body content
            last_p = [p.strip() for p in c.split('\n\n') if p.strip()][-1] if c.strip() else ""
            if is_heading(last_p) and len(c.strip().split('\n\n')) > 1 and idx < len(chunks) - 1:
                doc_heading_sep += 1
                heading_separations.append({
                    "source_id": sid,
                    "chunk_index": idx,
                    "heading": last_p
                })

            # 5. Orphaned emergency instructions
            # If chunk has "Call 999 if:" or "Immediate action required:" at the end without the conditions
            if ("Call 999 if:" in c or "Immediate action required:" in c) and ("999" in c and not any(cond in c for cond in ["start to feel", "severe", "large", "breathing", "blue", "pain", "swollen", "unconscious", "lips", "throat", "burn"])):
                doc_orphaned_emerg += 1
                orphaned_emergencies.append({
                    "source_id": sid,
                    "chunk_index": idx,
                    "snippet": c
                })

        doc_results[sid] = {
            "num_chunks": len(chunks),
            "mid_word_splits": doc_mid_word,
            "mid_sentence_splits": doc_mid_sentence,
            "heading_separations": doc_heading_sep,
            "orphaned_emergencies": doc_orphaned_emerg,
            "duplicates": doc_duplicates
        }

    avg_len = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
    min_len = min(chunk_lengths) if chunk_lengths else 0
    max_len = max(chunk_lengths) if chunk_lengths else 0

    return {
        "strategy": strategy_name,
        "total_chunks": total_chunks,
        "avg_chunk_length": round(avg_len, 1),
        "min_chunk_length": min_len,
        "max_chunk_length": max_len,
        "total_mid_word_splits": len(mid_word_splits),
        "total_mid_sentence_splits": len(mid_sentence_splits),
        "total_heading_separations": len(heading_separations),
        "total_orphaned_emergencies": len(orphaned_emergencies),
        "total_duplicates": len(duplicate_chunks),
        "doc_breakdown": doc_results,
        "mid_word_examples": mid_word_splits[:5],
        "mid_sentence_examples": mid_sentence_splits[:5],
        "heading_sep_examples": heading_separations[:5]
    }

# -----------------------------------------------------------------------------
# SOURCE RECONSTRUCTION CHECK
# -----------------------------------------------------------------------------
def evaluate_source_reconstruction(strategy_name: str, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    fn = STRATEGIES[strategy_name]
    doc_reconstruction = {}
    
    total_docs = len(docs)
    lossless_docs = 0

    for doc in docs:
        sid = doc["source_id"]
        original_text = doc["text"]
        chunks = fn(original_text)
        
        # Check if all paragraphs from original text exist across the chunks
        orig_paras = [p.strip() for p in original_text.split('\n\n') if p.strip()]
        missing_paras = []
        
        for p in orig_paras:
            # Check if paragraph is present in at least one chunk
            found = False
            for c in chunks:
                if p in c:
                    found = True
                    break
            if not found:
                missing_paras.append(p)

        is_lossless = (len(missing_paras) == 0)
        if is_lossless:
            lossless_docs += 1

        # Check total text coverage (union of unique words)
        orig_words = set(re.findall(r'\b\w+\b', original_text.lower()))
        chunk_words = set()
        for c in chunks:
            chunk_words.update(re.findall(r'\b\w+\b', c.lower()))
            
        missing_words = orig_words - chunk_words

        doc_reconstruction[sid] = {
            "num_chunks": len(chunks),
            "original_char_count": len(original_text),
            "original_para_count": len(orig_paras),
            "missing_paras_count": len(missing_paras),
            "missing_words_count": len(missing_words),
            "is_lossless": is_lossless,
            "missing_para_examples": missing_paras[:2]
        }

    return {
        "strategy": strategy_name,
        "total_docs": total_docs,
        "lossless_docs": lossless_docs,
        "lossless_rate": f"{lossless_docs}/{total_docs}",
        "doc_details": doc_reconstruction
    }

# -----------------------------------------------------------------------------
# REGRESSION TEST SUITE (Gate 4E Mid-Word Failure)
# -----------------------------------------------------------------------------
def run_regression_tests(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    asthma_doc = next((d for d in docs if d["source_id"] == "DOC-NHS-004"), None)
    if not asthma_doc:
        return {"error": "DOC-NHS-004 not found"}
        
    text = asthma_doc["text"]
    regression_results = {}

    for strat_name, fn in STRATEGIES.items():
        chunks = fn(text)
        
        # Test 1: Search for fragmented "ld air"
        has_ld_air = any(c.strip().startswith("ld air") or "\nld air" in c for c in chunks)
        
        # Test 2: Search for cut "it can happen at" at the end of a chunk
        has_cut_at = any(c.strip().endswith("it can happen at") for c in chunks)
        
        # Test 3: Any word boundary fractures across all chunks
        word_splits = 0
        for c in chunks:
            c_start = text.find(c)
            if c_start != -1:
                c_end = c_start + len(c)
                if c_start > 0 and text[c_start-1].isalnum() and text[c_start].isalnum():
                    word_splits += 1
                if c_end < len(text) and text[c_end-1].isalnum() and text[c_end].isalnum():
                    word_splits += 1

        regression_results[strat_name] = {
            "gate_4e_midword_failure_reproduced": has_ld_air,
            "gate_4e_midsentence_failure_reproduced": has_cut_at,
            "total_word_fractures": word_splits,
            "passed_regression_test": (not has_ld_air and not has_cut_at and word_splits == 0)
        }

    return regression_results

# -----------------------------------------------------------------------------
# REPRODUCIBILITY SUITE
# -----------------------------------------------------------------------------
def evaluate_reproducibility(docs: List[Dict[str, Any]], runs: int = 3) -> Dict[str, Any]:
    repro_results = {}
    for strat_name, fn in STRATEGIES.items():
        run_hashes = []
        for r in range(runs):
            doc_hashes = []
            for doc in docs:
                chunks = fn(doc["text"])
                for c in chunks:
                    doc_hashes.append(hash_str(c))
            overall_run_hash = hash_str("".join(doc_hashes))
            run_hashes.append(overall_run_hash)
        
        all_identical = len(set(run_hashes)) == 1
        repro_results[strat_name] = {
            "runs": runs,
            "run_hashes": run_hashes,
            "is_deterministic": all_identical
        }
    return repro_results

# -----------------------------------------------------------------------------
# EXPORT CHUNKS & PROVENANCE MANIFESTS
# -----------------------------------------------------------------------------
def export_strategy_outputs(docs: List[Dict[str, Any]]):
    for strat_name, fn in STRATEGIES.items():
        strat_dir = os.path.join(OUTPUTS_DIR, strat_name.lower())
        os.makedirs(strat_dir, exist_ok=True)
        
        manifest = []
        for doc in docs:
            sid = doc["source_id"]
            chunks = fn(doc["text"])
            for idx, c in enumerate(chunks):
                cid = f"{sid}-{strat_name[:3]}-{idx:03d}"
                c_hash = hash_str(c)
                manifest.append({
                    "chunk_id": cid,
                    "parent_source_id": sid,
                    "source_title": doc["title"],
                    "requested_url": doc["requested_url"],
                    "final_url": doc["final_url"],
                    "canonical_url": doc["canonical_url"],
                    "retrieval_timestamp_utc": doc["retrieval_timestamp_utc"],
                    "html_hash": doc["html_hash"],
                    "text_hash": doc["text_hash"],
                    "chunk_index": idx,
                    "total_chunks_in_doc": len(chunks),
                    "chunk_strategy": strat_name,
                    "chunk_hash": c_hash,
                    "char_length": len(c),
                    "text": c
                })
        
        out_path = os.path.join(strat_dir, "provenance_manifest.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        print(f"Exported {len(manifest)} chunks for {strat_name} to {out_path}")

# -----------------------------------------------------------------------------
# MAIN EXECUTION
# -----------------------------------------------------------------------------
def main():
    print("Loading source documents...")
    docs = load_source_documents()
    print(f"Loaded {len(docs)} documents.")

    print("\n--- 1. Boundary Integrity Evaluation ---")
    boundary_results = {}
    for strat_name in STRATEGIES.keys():
        res = evaluate_boundary_integrity(strat_name, docs)
        boundary_results[strat_name] = res
        print(f"[{strat_name}] Chunks: {res['total_chunks']}, Mid-word splits: {res['total_mid_word_splits']}, Mid-sentence splits: {res['total_mid_sentence_splits']}, Heading seps: {res['total_heading_separations']}")

    with open(os.path.join(EVALS_DIR, "boundary_integrity_eval.json"), 'w', encoding='utf-8') as f:
        json.dump(boundary_results, f, indent=2)

    print("\n--- 2. Source Reconstruction Evaluation ---")
    reconstruction_results = {}
    for strat_name in STRATEGIES.keys():
        res = evaluate_source_reconstruction(strat_name, docs)
        reconstruction_results[strat_name] = res
        print(f"[{strat_name}] Lossless docs: {res['lossless_rate']}")

    with open(os.path.join(EVALS_DIR, "source_reconstruction_eval.json"), 'w', encoding='utf-8') as f:
        json.dump(reconstruction_results, f, indent=2)

    print("\n--- 3. Regression Tests (Gate 4E Failure) ---")
    regression_results = run_regression_tests(docs)
    print(json.dumps(regression_results, indent=2))
    with open(os.path.join(EVALS_DIR, "regression_eval.json"), 'w', encoding='utf-8') as f:
        json.dump(regression_results, f, indent=2)

    print("\n--- 4. Reproducibility Suite ---")
    repro_results = evaluate_reproducibility(docs)
    print(json.dumps(repro_results, indent=2))
    with open(os.path.join(EVALS_DIR, "reproducibility_eval.json"), 'w', encoding='utf-8') as f:
        json.dump(repro_results, f, indent=2)

    print("\n--- 5. Exporting Chunk Artifacts ---")
    export_strategy_outputs(docs)

    print("\nGate 4F Evaluation Run Finished Successfully.")

if __name__ == "__main__":
    main()
