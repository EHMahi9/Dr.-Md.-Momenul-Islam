"""
Gate 5.9.2 — Comprehensive Chunk-Level Recall@K and Gold Integrity Audit Runner
Computes chunk-level R@1, R@3, R@5, MRR, Top-1 vs Top-5 evidence availability, and reranker chunk shifts.
"""

import json
import os
import hashlib
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BENCHMARK_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json"))
CONFIG_FILE = os.path.join(BASE_DIR, "frozen_config_manifest.json")
CHUNKS_FILE = os.path.join(BASE_DIR, "chunks", "hybrid_600", "provenance_manifest.json")
FROZEN_EVAL_FILE = os.path.join(BASE_DIR, "evaluations", "gate_5_9_locked_holdout_evaluation.json")
GOLD_LABELS_FILE = os.path.join(BASE_DIR, "chunk_gold_labels.json")
TOP5_RANKINGS_FILE = os.path.join(BASE_DIR, "evaluations", "gate_5_9_exact_top5_rankings.json")
AUDIT_OUT_FILE = os.path.join(BASE_DIR, "evaluations", "gate_5_9_2_audit_results.json")

def hash_file(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    with open(TOP5_RANKINGS_FILE, "r", encoding="utf-8") as f:
        top5_rankings = json.load(f)

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunk_map = {c["chunk_id"]: c for c in chunks}

    # Evaluate all queries
    eval_queries = []
    
    # Evidence availability categories
    evidence_availability = {
        "overall": {"TOP1_CORRECT": 0, "TOP1_WRONG_BUT_TOP3_CONTAINS_GOLD": 0, "TOP3_WRONG_BUT_TOP5_CONTAINS_GOLD": 0, "GOLD_ABSENT_FROM_TOP5": 0},
        "dev": {"TOP1_CORRECT": 0, "TOP1_WRONG_BUT_TOP3_CONTAINS_GOLD": 0, "TOP3_WRONG_BUT_TOP5_CONTAINS_GOLD": 0, "GOLD_ABSENT_FROM_TOP5": 0},
        "holdout": {"TOP1_CORRECT": 0, "TOP1_WRONG_BUT_TOP3_CONTAINS_GOLD": 0, "TOP3_WRONG_BUT_TOP5_CONTAINS_GOLD": 0, "GOLD_ABSENT_FROM_TOP5": 0}
    }

    # Reranker chunk-level effect tracking
    reranker_effects = {
        "dense_correct__rerank_correct": 0,
        "dense_wrong__rerank_correct": 0,       # Chunk improvement
        "dense_correct__rerank_wrong": 0,       # Chunk degradation (OBSERVED_CHUNK_RANKING_REGRESSION)
        "dense_wrong__rerank_wrong": 0,
        "source_improvement_but_chunk_regression": 0
    }

    disagreements = []

    for q in top5_rankings:
        qid = q["query_id"]
        q_text = q["query_text"]
        split = q["benchmark_split"]
        lang = q["language_category"]
        expected_sid = q["expected_source_id"]

        is_valid = (expected_sid != "NONE")
        if not is_valid:
            eval_queries.append({
                "query_id": qid,
                "query_text": q_text,
                "benchmark_split": split,
                "language_category": lang,
                "is_valid_query": False,
                "dense_top5_chunk_ids": q["dense_top5_chunk_ids"],
                "r5_top5_chunk_ids": q["r5_top5_chunk_ids"],
                "r5_top1_score": q["r5_top1_score"]
            })
            continue

        gold = gold_labels[qid]
        acceptable_cids = gold["gold_chunk_ids"]
        topic = gold["target_topic"]
        rationale = gold["gold_mapping_rationale"]

        dense_cids = q["dense_top5_chunk_ids"]
        r5_cids = q["r5_top5_chunk_ids"]

        # Dense Chunk-Level Metrics
        dense_chunk_hits = [cid in acceptable_cids for cid in dense_cids]
        dense_chunk_r1 = dense_chunk_hits[0]
        dense_chunk_r3 = any(dense_chunk_hits[:3])
        dense_chunk_r5 = any(dense_chunk_hits[:5])
        dense_chunk_rank = (dense_chunk_hits.index(True) + 1) if any(dense_chunk_hits) else 0
        dense_chunk_rr = (1.0 / dense_chunk_rank) if dense_chunk_rank > 0 else 0.0

        # Reranker Chunk-Level Metrics
        r5_chunk_hits = [cid in acceptable_cids for cid in r5_cids]
        r5_chunk_r1 = r5_chunk_hits[0]
        r5_chunk_r3 = any(r5_chunk_hits[:3])
        r5_chunk_r5 = any(r5_chunk_hits[:5])
        r5_chunk_rank = (r5_chunk_hits.index(True) + 1) if any(r5_chunk_hits) else 0
        r5_chunk_rr = (1.0 / r5_chunk_rank) if r5_chunk_rank > 0 else 0.0

        # Source-level metrics
        dense_sids = [chunk_map[cid]["parent_source_id"] for cid in dense_cids]
        r5_sids = [chunk_map[cid]["parent_source_id"] for cid in r5_cids]
        
        src_dense_r1 = (dense_sids[0] == expected_sid)
        src_r5_r1 = (r5_sids[0] == expected_sid)

        # Categorize evidence availability
        if r5_chunk_r1:
            avail_cat = "TOP1_CORRECT"
        elif r5_chunk_r3:
            avail_cat = "TOP1_WRONG_BUT_TOP3_CONTAINS_GOLD"
        elif r5_chunk_r5:
            avail_cat = "TOP3_WRONG_BUT_TOP5_CONTAINS_GOLD"
        else:
            avail_cat = "GOLD_ABSENT_FROM_TOP5"

        evidence_availability["overall"][avail_cat] += 1
        if split == "DEV":
            evidence_availability["dev"][avail_cat] += 1
        elif split == "TEST_HOLDOUT":
            evidence_availability["holdout"][avail_cat] += 1

        # Reranker dynamics at chunk level
        if dense_chunk_r1 and r5_chunk_r1:
            reranker_effects["dense_correct__rerank_correct"] += 1
        elif not dense_chunk_r1 and r5_chunk_r1:
            reranker_effects["dense_wrong__rerank_correct"] += 1
        elif dense_chunk_r1 and not r5_chunk_r1:
            reranker_effects["dense_correct__rerank_wrong"] += 1
        else:
            reranker_effects["dense_wrong__rerank_wrong"] += 1

        if not src_dense_r1 and src_r5_r1 and not r5_chunk_r1:
            reranker_effects["source_improvement_but_chunk_regression"] += 1

        # Check source vs chunk disagreement
        if src_r5_r1 and not r5_chunk_r1:
            # Classification of failure
            if r5_chunk_r5:
                fail_cat = "GOLD_IN_TOP5"
            else:
                fail_cat = "GOLD_OUTSIDE_TOP5"

            disagreements.append({
                "query_id": qid,
                "query_text": q_text,
                "target_topic": topic,
                "benchmark_split": split,
                "language_category": lang,
                "expected_source_id": expected_sid,
                "acceptable_gold_chunks": acceptable_cids,
                "retrieved_top1_chunk_id": r5_cids[0],
                "retrieved_top1_chunk_text": chunk_map[r5_cids[0]]["text"][:150],
                "dense_top5_chunk_ids": dense_cids,
                "r5_top5_chunk_ids": r5_cids,
                "failure_classification": fail_cat
            })

        eval_queries.append({
            "query_id": qid,
            "query_text": q_text,
            "target_topic": topic,
            "benchmark_split": split,
            "language_category": lang,
            "expected_source_id": expected_sid,
            "acceptable_gold_chunks": acceptable_cids,
            "gold_mapping_rationale": rationale,
            "dense_top5_chunk_ids": dense_cids,
            "r5_top5_chunk_ids": r5_cids,
            "source_dense_r1": src_dense_r1,
            "source_r5_r1": src_r5_r1,
            "dense_chunk_r1": dense_chunk_r1,
            "dense_chunk_r3": dense_chunk_r3,
            "dense_chunk_r5": dense_chunk_r5,
            "dense_chunk_rank": dense_chunk_rank,
            "dense_chunk_rr": dense_chunk_rr,
            "r5_chunk_r1": r5_chunk_r1,
            "r5_chunk_r3": r5_chunk_r3,
            "r5_chunk_r5": r5_chunk_r5,
            "r5_chunk_rank": r5_chunk_rank,
            "r5_chunk_rr": r5_chunk_rr,
            "evidence_availability_category": avail_cat
        })

    def calc_metrics(subset):
        valid = [q for q in subset if q.get("acceptable_gold_chunks")]
        if not valid: return {}
        n = len(valid)

        d_r1 = sum(1 for q in valid if q["dense_chunk_r1"])
        d_r3 = sum(1 for q in valid if q["dense_chunk_r3"])
        d_r5 = sum(1 for q in valid if q["dense_chunk_r5"])
        d_mrr = sum(q["dense_chunk_rr"] for q in valid) / n

        r5_r1 = sum(1 for q in valid if q["r5_chunk_r1"])
        r5_r3 = sum(1 for q in valid if q["r5_chunk_r3"])
        r5_r5 = sum(1 for q in valid if q["r5_chunk_r5"])
        r5_mrr = sum(q["r5_chunk_rr"] for q in valid) / n

        src_d_r1 = sum(1 for q in valid if q["source_dense_r1"])
        src_r5_r1 = sum(1 for q in valid if q["source_r5_r1"])

        return {
            "n": n,
            "source_level": {
                "dense_r1_count": f"{src_d_r1}/{n}",
                "dense_r1_pct": round((src_d_r1 / n) * 100, 2),
                "r5_r1_count": f"{src_r5_r1}/{n}",
                "r5_r1_pct": round((src_r5_r1 / n) * 100, 2)
            },
            "chunk_level_dense": {
                "r1_count": f"{d_r1}/{n}",
                "r1_pct": round((d_r1 / n) * 100, 2),
                "r3_count": f"{d_r3}/{n}",
                "r3_pct": round((d_r3 / n) * 100, 2),
                "r5_count": f"{d_r5}/{n}",
                "r5_pct": round((d_r5 / n) * 100, 2),
                "mrr": round(d_mrr, 4)
            },
            "chunk_level_r5": {
                "r1_count": f"{r5_r1}/{n}",
                "r1_pct": round((r5_r1 / n) * 100, 2),
                "r3_count": f"{r5_r3}/{n}",
                "r3_pct": round((r5_r3 / n) * 100, 2),
                "r5_count": f"{r5_r5}/{n}",
                "r5_pct": round((r5_r5 / n) * 100, 2),
                "mrr": round(r5_mrr, 4)
            }
        }

    overall_res = calc_metrics(eval_queries)
    dev_res = calc_metrics([q for q in eval_queries if q["benchmark_split"] == "DEV"])
    holdout_res = calc_metrics([q for q in eval_queries if q["benchmark_split"] == "TEST_HOLDOUT"])

    # Language breakdown for DEV and HOLDOUT
    dev_lang = {}
    holdout_lang = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        dev_lang[lang] = calc_metrics([q for q in eval_queries if q["benchmark_split"] == "DEV" and q["language_category"] == lang])
        holdout_lang[lang] = calc_metrics([q for q in eval_queries if q["benchmark_split"] == "TEST_HOLDOUT" and q["language_category"] == lang])

    output_data = {
        "reproducibility_hashes": {
            "frozen_benchmark_hash": hash_file(BENCHMARK_FILE),
            "frozen_config_hash": hash_file(CONFIG_FILE),
            "hybrid_600_chunks_hash": hash_file(CHUNKS_FILE),
            "frozen_gate_5_9_eval_hash": hash_file(FROZEN_EVAL_FILE),
            "gold_labels_hash": hash_file(GOLD_LABELS_FILE),
            "top5_rankings_hash": hash_file(TOP5_RANKINGS_FILE)
        },
        "overall_metrics": overall_res,
        "dev_split_metrics": dev_res,
        "locked_holdout_metrics": holdout_res,
        "dev_language_breakdown": dev_lang,
        "locked_holdout_language_breakdown": holdout_lang,
        "evidence_availability": evidence_availability,
        "reranker_chunk_effects": reranker_effects,
        "disagreement_cases_count": len(disagreements),
        "disagreements": disagreements,
        "query_evaluations": eval_queries
    }

    with open(AUDIT_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\n=== OVERALL CHUNK METRICS ===")
    print(json.dumps(overall_res, indent=2))
    print("\n=== DEV CHUNK METRICS ===")
    print(json.dumps(dev_res, indent=2))
    print("\n=== LOCKED HOLDOUT CHUNK METRICS ===")
    print(json.dumps(holdout_res, indent=2))
    print("\n=== EVIDENCE AVAILABILITY ===")
    print(json.dumps(evidence_availability, indent=2))
    print("\n=== RERANKER EFFECTS ===")
    print(json.dumps(reranker_effects, indent=2))

if __name__ == "__main__":
    main()
