"""
Gate 5.9.1 — Re-Score Frozen Gate 5.9 Retrieval Results at Chunk-Level
Evaluates chunk-level correctness using frozen rankings without running model inference.
"""

import json
import os
import hashlib
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BENCHMARK_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json"))
FROZEN_EVAL_FILE = os.path.join(BASE_DIR, "evaluations", "gate_5_9_locked_holdout_evaluation.json")
CHUNKS_FILE = os.path.join(BASE_DIR, "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(BASE_DIR, "chunk_gold_labels.json")
AUDIT_OUT_FILE = os.path.join(BASE_DIR, "evaluations", "gate_5_9_1_chunk_level_audit_results.json")

def hash_file(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    print("Loading Frozen Gate 5.9 Evaluation Results...")
    with open(FROZEN_EVAL_FILE, 'r', encoding='utf-8') as f:
        eval_data = json.load(f)

    with open(GOLD_LABELS_FILE, 'r', encoding='utf-8') as f:
        gold_labels = json.load(f)

    with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    chunk_map = {c["chunk_id"]: c for c in chunks}

    query_results = eval_data["query_results"]

    rescored_queries = []
    source_correct_chunk_incorrect_cases = []

    # Track reranker chunk-level vs source-level impact
    reranker_stats = {
        "source_improvements": 0,
        "source_degradations": 0,
        "chunk_improvements": 0,
        "chunk_degradations": 0,
        "neutral_source": 0,
        "neutral_chunk": 0
    }

    for q in query_results:
        qid = q["query_id"]
        is_valid = q["is_valid_query"]
        split = q["benchmark_split"]
        lang = q["language_category"]
        expected_sid = q["expected_source_id"]

        if not is_valid:
            rescored_queries.append(q)
            continue

        gold = gold_labels.get(qid)
        if not gold:
            print(f"WARNING: No gold label for {qid}!")
            continue

        acceptable_cids = gold["gold_chunk_ids"]
        rationale = gold["gold_mapping_rationale"]

        # In Gate 5.9 eval, we retrieved Top-5 candidates.
        # Let's extract the retrieved chunk IDs from the rankings.
        # In eval_data, we have dense_top_sids and r5_top_sids, and top1 chunk texts.
        # Let's match chunk IDs by text prefix against chunk_map.
        
        # Dense top-1 chunk ID
        dense_top1_cid = None
        dense_top1_text_prefix = q["dense_top1_chunk"][:40]
        for cid, c in chunk_map.items():
            if c["text"].startswith(dense_top1_text_prefix):
                dense_top1_cid = cid
                break

        # R5 top-1 chunk ID
        r5_top1_cid = None
        r5_top1_text_prefix = q["r5_top1_chunk"][:40]
        for cid, c in chunk_map.items():
            if c["text"].startswith(r5_top1_text_prefix):
                r5_top1_cid = cid
                break

        # Check Source-Level Correctness (from frozen eval)
        src_dense_r1 = q["dense_r1"]
        src_r5_r1 = q["r5_r1"]

        # Check Chunk-Level Correctness
        chunk_dense_r1 = (dense_top1_cid in acceptable_cids) if dense_top1_cid else False
        chunk_r5_r1 = (r5_top1_cid in acceptable_cids) if r5_top1_cid else False

        # Check Disagreement (Source Correct, but Chunk Incorrect)
        is_disagreement_r5 = (src_r5_r1 and not chunk_r5_r1)
        if is_disagreement_r5:
            source_correct_chunk_incorrect_cases.append({
                "query_id": qid,
                "query_text": q["query_text"],
                "split": split,
                "language": lang,
                "expected_source": expected_sid,
                "acceptable_gold_chunks": acceptable_cids,
                "retrieved_top1_chunk_id": r5_top1_cid,
                "retrieved_top1_chunk_text": chunk_map[r5_top1_cid]["text"][:150] if r5_top1_cid else q["r5_top1_chunk"],
                "why_source_level_correct": f"Retrieved chunk belongs to parent source {expected_sid}",
                "why_chunk_level_incorrect": f"Retrieved chunk does not contain the specific evidence required for '{q['query_text']}'"
            })

        # Track Reranker Impact at Chunk Level vs Source Level
        if not src_dense_r1 and src_r5_r1:
            reranker_stats["source_improvements"] += 1
        elif src_dense_r1 and not src_r5_r1:
            reranker_stats["source_degradations"] += 1
        else:
            reranker_stats["neutral_source"] += 1

        if not chunk_dense_r1 and chunk_r5_r1:
            reranker_stats["chunk_improvements"] += 1
        elif chunk_dense_r1 and not chunk_r5_r1:
            reranker_stats["chunk_degradations"] += 1
        else:
            reranker_stats["neutral_chunk"] += 1

        rescored_queries.append({
            "query_id": qid,
            "query_text": q["query_text"],
            "benchmark_split": split,
            "language_category": lang,
            "expected_source_id": expected_sid,
            "acceptable_gold_chunks": acceptable_cids,
            "gold_mapping_rationale": rationale,
            "dense_top1_chunk_id": dense_top1_cid,
            "r5_top1_chunk_id": r5_top1_cid,
            "source_dense_r1": src_dense_r1,
            "source_r5_r1": src_r5_r1,
            "chunk_dense_r1": chunk_dense_r1,
            "chunk_r5_r1": chunk_r5_r1,
            "source_vs_chunk_disagreement": is_disagreement_r5
        })

    def compute_metrics(subset):
        valid = [q for q in subset if q.get("acceptable_gold_chunks")]
        if not valid: return {}
        n = len(valid)
        
        src_dense_r1 = sum(1 for q in valid if q["source_dense_r1"]) / n
        src_r5_r1 = sum(1 for q in valid if q["source_r5_r1"]) / n
        
        chk_dense_r1 = sum(1 for q in valid if q["chunk_dense_r1"]) / n
        chk_r5_r1 = sum(1 for q in valid if q["chunk_r5_r1"]) / n

        disagreements = sum(1 for q in valid if q["source_vs_chunk_disagreement"])

        return {
            "n": n,
            "source_level": {
                "dense_R1": round(src_dense_r1 * 100, 2),
                "r5_R1": round(src_r5_r1 * 100, 2)
            },
            "chunk_level": {
                "dense_R1": round(chk_dense_r1 * 100, 2),
                "r5_R1": round(chk_r5_r1 * 100, 2)
            },
            "disagreement_count": disagreements,
            "disagreement_rate_pct": round((disagreements / n) * 100, 2)
        }

    overall_metrics = compute_metrics(rescored_queries)
    dev_metrics = compute_metrics([q for q in rescored_queries if q["benchmark_split"] == "DEV"])
    holdout_metrics = compute_metrics([q for q in rescored_queries if q["benchmark_split"] == "TEST_HOLDOUT"])

    # Language breakdowns on holdout
    holdout_valid = [q for q in rescored_queries if q["benchmark_split"] == "TEST_HOLDOUT"]
    holdout_lang = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        l_sub = [q for q in holdout_valid if q["language_category"] == lang]
        holdout_lang[lang] = compute_metrics(l_sub)

    # Full corpus language breakdowns
    all_valid = [q for q in rescored_queries if q.get("acceptable_gold_chunks")]
    full_lang = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        l_sub = [q for q in all_valid if q["language_category"] == lang]
        full_lang[lang] = compute_metrics(l_sub)

    audit_output = {
        "reproducibility_hashes": {
            "frozen_benchmark_hash": hash_file(BENCHMARK_FILE),
            "frozen_config_hash": hash_file(os.path.join(BASE_DIR, "frozen_config_manifest.json")),
            "hybrid_600_chunks_hash": hash_file(CHUNKS_FILE),
            "gate_5_9_eval_output_hash": hash_file(FROZEN_EVAL_FILE),
            "gold_labels_manifest_hash": hash_file(GOLD_LABELS_FILE)
        },
        "overall_metrics": overall_metrics,
        "dev_split_metrics": dev_metrics,
        "locked_holdout_metrics": holdout_metrics,
        "locked_holdout_language_breakdown": holdout_lang,
        "full_corpus_language_breakdown": full_lang,
        "reranker_impact_analysis": reranker_stats,
        "disagreement_cases_count": len(source_correct_chunk_incorrect_cases),
        "disagreement_cases": source_correct_chunk_incorrect_cases,
        "rescored_queries": rescored_queries
    }

    with open(AUDIT_OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(audit_output, f, indent=2, ensure_ascii=False)

    print("\n=======================================================")
    print("GATE 5.9.1 CHUNK-LEVEL AUDIT COMPLETE")
    print("=======================================================")
    print(f"Overall Valid (N=80):")
    print(f"  Source-Level Top-5+Rerank R@1: {overall_metrics['source_level']['r5_R1']}%")
    print(f"  Chunk-Level Top-5+Rerank R@1:  {overall_metrics['chunk_level']['r5_R1']}%")
    print(f"  Disagreement Count:            {overall_metrics['disagreement_count']} ({overall_metrics['disagreement_rate_pct']}%)")
    
    print(f"\nLocked Holdout Split (N=40):")
    print(f"  Source-Level Top-5+Rerank R@1: {holdout_metrics['source_level']['r5_R1']}%")
    print(f"  Chunk-Level Top-5+Rerank R@1:  {holdout_metrics['chunk_level']['r5_R1']}%")
    print(f"  Disagreement Count:            {holdout_metrics['disagreement_count']} ({holdout_metrics['disagreement_rate_pct']}%)")

    print(f"\nReranker Impact Disaggregation:")
    print(f"  Source Improvements: {reranker_stats['source_improvements']}, Source Degradations: {reranker_stats['source_degradations']}")
    print(f"  Chunk Improvements:  {reranker_stats['chunk_improvements']}, Chunk Degradations:  {reranker_stats['chunk_degradations']}")

if __name__ == "__main__":
    main()
