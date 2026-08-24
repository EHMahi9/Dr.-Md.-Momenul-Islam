"""
Gate 5.9.1 — Comprehensive Chunk-Level Evaluation and Audit Engine
Computes source vs chunk metrics across splits and linguistic categories from frozen Gate 5.9 outputs.
"""

import json
import os
import hashlib
from collections import defaultdict

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
    with open(FROZEN_EVAL_FILE, 'r', encoding='utf-8') as f:
        eval_data = json.load(f)

    with open(GOLD_LABELS_FILE, 'r', encoding='utf-8') as f:
        gold_labels = json.load(f)

    with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    chunk_map = {c["chunk_id"]: c for c in chunks}

    query_results = eval_data["query_results"]

    rescored = []
    disagreements = []

    reranker_impact = {
        "source_level": {"improvements": 0, "degradations": 0, "neutral": 0},
        "chunk_level": {"improvements": 0, "degradations": 0, "neutral": 0}
    }

    for q in query_results:
        qid = q["query_id"]
        is_valid = q["is_valid_query"]
        split = q["benchmark_split"]
        lang = q["language_category"]
        expected_sid = q["expected_source_id"]

        if not is_valid:
            rescored.append(q)
            continue

        gold = gold_labels[qid]
        acceptable_cids = gold["gold_chunk_ids"]
        topic = gold["target_topic"]
        rationale = gold["gold_mapping_rationale"]

        # Identify retrieved chunk IDs
        dense_top1_cid = None
        dense_prefix = q["dense_top1_chunk"][:40]
        for cid, c in chunk_map.items():
            if c["text"].startswith(dense_prefix):
                dense_top1_cid = cid
                break

        r5_top1_cid = None
        r5_prefix = q["r5_top1_chunk"][:40]
        for cid, c in chunk_map.items():
            if c["text"].startswith(r5_prefix):
                r5_top1_cid = cid
                break

        src_dense_r1 = q["dense_r1"]
        src_r5_r1 = q["r5_r1"]

        chk_dense_r1 = (dense_top1_cid in acceptable_cids) if dense_top1_cid else False
        chk_r5_r1 = (r5_top1_cid in acceptable_cids) if r5_top1_cid else False

        # Reranker impact
        if not src_dense_r1 and src_r5_r1:
            reranker_impact["source_level"]["improvements"] += 1
        elif src_dense_r1 and not src_r5_r1:
            reranker_impact["source_level"]["degradations"] += 1
        else:
            reranker_impact["source_level"]["neutral"] += 1

        if not chk_dense_r1 and chk_r5_r1:
            reranker_impact["chunk_level"]["improvements"] += 1
        elif chk_dense_r1 and not chk_r5_r1:
            reranker_impact["chunk_level"]["degradations"] += 1
        else:
            reranker_impact["chunk_level"]["neutral"] += 1

        # Check Disagreement
        is_disagreement = (src_r5_r1 and not chk_r5_r1)
        if is_disagreement:
            retrieved_chunk_text = chunk_map[r5_top1_cid]["text"] if r5_top1_cid else q["r5_top1_chunk"]
            disagreements.append({
                "query_id": qid,
                "query_text": q["query_text"],
                "target_topic": topic,
                "split": split,
                "language": lang,
                "expected_source": expected_sid,
                "acceptable_gold_chunks": acceptable_cids,
                "retrieved_top1_chunk_id": r5_top1_cid,
                "retrieved_top1_chunk_text": retrieved_chunk_text[:180],
                "why_source_level_correct": f"Retrieved chunk belongs to expected parent source {expected_sid}",
                "why_chunk_level_incorrect": f"Retrieved chunk ({r5_top1_cid}) does not contain the specific evidence for '{topic}'."
            })

        rescored.append({
            "query_id": qid,
            "query_text": q["query_text"],
            "target_topic": topic,
            "benchmark_split": split,
            "language_category": lang,
            "expected_source_id": expected_sid,
            "acceptable_gold_chunks": acceptable_cids,
            "gold_mapping_rationale": rationale,
            "dense_top1_chunk_id": dense_top1_cid,
            "r5_top1_chunk_id": r5_top1_cid,
            "source_dense_r1": src_dense_r1,
            "source_r5_r1": src_r5_r1,
            "chunk_dense_r1": chk_dense_r1,
            "chunk_r5_r1": chk_r5_r1,
            "source_vs_chunk_disagreement": is_disagreement
        })

    def calc_slice_metrics(subset):
        valid = [q for q in subset if q.get("acceptable_gold_chunks")]
        if not valid: return {}
        n = len(valid)
        
        src_d_r1 = sum(1 for q in valid if q["source_dense_r1"]) / n
        src_r5_r1 = sum(1 for q in valid if q["source_r5_r1"]) / n
        
        chk_d_r1 = sum(1 for q in valid if q["chunk_dense_r1"]) / n
        chk_r5_r1 = sum(1 for q in valid if q["chunk_r5_r1"]) / n

        dis_cnt = sum(1 for q in valid if q["source_vs_chunk_disagreement"])

        return {
            "n": n,
            "source_level_dense_R1": round(src_d_r1 * 100, 2),
            "source_level_r5_R1": round(src_r5_r1 * 100, 2),
            "chunk_level_dense_R1": round(chk_d_r1 * 100, 2),
            "chunk_level_r5_R1": round(chk_r5_r1 * 100, 2),
            "disagreement_count": dis_cnt,
            "disagreement_rate_pct": round((dis_cnt / n) * 100, 2)
        }

    overall_metrics = calc_slice_metrics(rescored)
    dev_metrics = calc_slice_metrics([q for q in rescored if q["benchmark_split"] == "DEV"])
    holdout_metrics = calc_slice_metrics([q for q in rescored if q["benchmark_split"] == "TEST_HOLDOUT"])

    # Language breakdown across whole corpus & holdout
    holdout_lang = {}
    full_lang = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        holdout_lang[lang] = calc_slice_metrics([q for q in rescored if q["benchmark_split"] == "TEST_HOLDOUT" and q["language_category"] == lang])
        full_lang[lang] = calc_slice_metrics([q for q in rescored if q["language_category"] == lang])

    out_data = {
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
        "reranker_impact_disaggregation": reranker_impact,
        "total_disagreements": len(disagreements),
        "disagreements": disagreements,
        "rescored_queries": rescored
    }

    with open(AUDIT_OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)

    print(json.dumps(overall_metrics, indent=2))
    print("\nDEV Metrics:", json.dumps(dev_metrics, indent=2))
    print("\nHOLDOUT Metrics:", json.dumps(holdout_metrics, indent=2))
    print("\nHOLDOUT Languages:", json.dumps(holdout_lang, indent=2))
    print("\nReranker Impact:", json.dumps(reranker_impact, indent=2))

if __name__ == "__main__":
    main()
