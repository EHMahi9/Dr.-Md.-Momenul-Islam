"""
Gate 5.12 — Phase 1: Comprehensive Failure Decomposition on DEV Split
Runs Gate 5.11 baseline (Dense Top-15 -> Reranker Top-5) on the 40 DEV queries and performs deep multi-label failure diagnosis.
"""

import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
OPT_DIR = os.path.join(ROOT_DIR, "gate_5_9_optimization")
CHUNKS_FILE = os.path.join(OPT_DIR, "chunks", "hybrid_600", "provenance_manifest.json")
BENCHMARK_FILE = os.path.join(ROOT_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
GOLD_LABELS_FILE = os.path.join(OPT_DIR, "chunk_gold_labels.json")
OUT_FILE = os.path.join(BASE_DIR, "..", "diagnostics", "dev_failure_decomposition.json")

def main():
    print("Loading DEV data and models...")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunk_map = {c["chunk_id"]: c for c in chunks}

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    # Encode all 68 passages
    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    query_texts = [f"query: {q['query_text']}" for q in dev_queries]
    query_embeddings = dense_model.encode(query_texts, normalize_embeddings=True)

    # Similarity matrix
    sim_matrix = np.dot(query_embeddings, chunk_embeddings.T)

    results = []
    failure_counts = {
        "GOLD_OUTSIDE_DENSE15": 0,
        "GOLD_IN_DENSE15_BUT_RERANK_DEMOTED": 0,
        "GENERIC_OVERVIEW_BIAS": 0,
        "HEADING_OR_CONTEXT_REPRESENTATION_FAILURE": 0,
        "NATIVE_BANGLA_QUERY_MISMATCH": 0,
        "STANDARD_BANGLISH_QUERY_MISMATCH": 0,
        "ABBREVIATED_BANGLISH_QUERY_MISMATCH": 0,
        "LEXICAL_OR_EXACT_TERM_FAILURE": 0
    }

    for i, q in enumerate(dev_queries):
        qid = q["query_id"]
        q_text = q["query_text"]
        lang = q["language_category"]
        expected_sid = q["expected_source_id"]
        target_topic = q.get("target_topic", "")
        gold_cids = gold_labels[qid]["gold_chunk_ids"]

        dense_scores = sim_matrix[i]
        ranked_dense_indices = np.argsort(-dense_scores)
        top15_indices = ranked_dense_indices[:15]
        dense_top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]

        # Reranker scoring of Top-15
        pairs = [(q_text, chunks[idx]["text"]) for idx in top15_indices]
        r_scores = reranker.predict(pairs)
        r_order = np.argsort(-r_scores)
        r_top15_cids = [dense_top15_cids[idx] for idx in r_order]
        r_top15_scores = [float(r_scores[idx]) for idx in r_order]

        final_top5_cids = r_top15_cids[:5]
        final_top5_scores = r_top15_scores[:5]

        # Hits
        dense_hits = [cid in gold_cids for cid in dense_top15_cids]
        dense_r1 = dense_hits[0]
        dense_r3 = any(dense_hits[:3])
        dense_r5 = any(dense_hits[:5])
        dense_r15 = any(dense_hits[:15])
        dense_rank = (dense_hits.index(True) + 1) if any(dense_hits) else 0

        r_hits = [cid in gold_cids for cid in final_top5_cids]
        r_r1 = r_hits[0]
        r_r3 = any(r_hits[:3])
        r_r5 = any(r_hits[:5])
        r_rank = (r_hits.index(True) + 1) if any(r_hits) else 0

        # Detailed failure tagging
        tags = []
        is_top5_failure = not r_r5

        if not dense_r15:
            tags.append("GOLD_OUTSIDE_DENSE15")
            failure_counts["GOLD_OUTSIDE_DENSE15"] += 1
        elif dense_r15 and not r_r5:
            tags.append("GOLD_IN_DENSE15_BUT_RERANK_DEMOTED")
            failure_counts["GOLD_IN_DENSE15_BUT_RERANK_DEMOTED"] += 1

        # Check if top retrieved chunk is an overview/intro from the same document
        top1_chunk = chunk_map[final_top5_cids[0]]
        if not r_r1 and top1_chunk["parent_source_id"] == expected_sid and ("overview" in top1_chunk["text"].lower() or "about" in top1_chunk["text"].lower() or top1_chunk["chunk_index"] == 0):
            tags.append("GENERIC_OVERVIEW_BIAS")
            failure_counts["GENERIC_OVERVIEW_BIAS"] += 1

        # Check if gold chunk lacks section header context
        gold_chunk_objs = [chunk_map[cid] for cid in gold_cids]
        if any(len(gc["text"].split("\n")[0]) > 60 for gc in gold_chunk_objs) and is_top5_failure:
            tags.append("HEADING_OR_CONTEXT_REPRESENTATION_FAILURE")
            failure_counts["HEADING_OR_CONTEXT_REPRESENTATION_FAILURE"] += 1

        # Linguistic tagging
        if is_top5_failure:
            if lang == "Native_Bangla":
                tags.append("NATIVE_BANGLA_QUERY_MISMATCH")
                failure_counts["NATIVE_BANGLA_QUERY_MISMATCH"] += 1
            elif lang == "Standard_Banglish":
                tags.append("STANDARD_BANGLISH_QUERY_MISMATCH")
                failure_counts["STANDARD_BANGLISH_QUERY_MISMATCH"] += 1
            elif lang == "Abbreviated_Banglish":
                tags.append("ABBREVIATED_BANGLISH_QUERY_MISMATCH")
                failure_counts["ABBREVIATED_BANGLISH_QUERY_MISMATCH"] += 1

            # Check lexical term mismatch
            q_lower = q_text.lower()
            medical_terms = ["inhaler", "spacer", "cold water", "blister", "antiseptic", "bleeding", "pressure", "water", "ors", "rehydration", "saline", "urine", "pee"]
            if any(t in q_lower for t in medical_terms):
                tags.append("LEXICAL_OR_EXACT_TERM_FAILURE")
                failure_counts["LEXICAL_OR_EXACT_TERM_FAILURE"] += 1

        results.append({
            "query_id": qid,
            "query_text": q_text,
            "language_category": lang,
            "target_topic": target_topic,
            "expected_source_id": expected_sid,
            "gold_chunk_ids": gold_cids,
            "dense_top15_cids": dense_top15_cids,
            "dense_rank": dense_rank,
            "final_top5_cids": final_top5_cids,
            "final_top5_scores": final_top5_scores,
            "rerank_rank": r_rank,
            "is_top5_success": r_r5,
            "is_top1_success": r_r1,
            "failure_tags": tags
        })

    n = len(dev_queries)
    r1_count = sum(1 for r in results if r["is_top1_success"])
    r3_count = sum(1 for r in results if r["rerank_rank"] in [1, 2, 3])
    r5_count = sum(1 for r in results if r["is_top5_success"])
    mrr = sum(1.0 / r["rerank_rank"] for r in results if r["rerank_rank"] > 0) / n

    summary = {
        "n_dev_queries": n,
        "baseline_metrics": {
            "r1": f"{r1_count}/{n} ({r1_count/n*100:.2f}%)",
            "r3": f"{r3_count}/{n} ({r3_count/n*100:.2f}%)",
            "r5": f"{r5_count}/{n} ({r5_count/n*100:.2f}%)",
            "mrr": round(mrr, 4)
        },
        "failure_decomposition_counts": failure_counts,
        "failed_queries_count": n - r5_count,
        "query_breakdown": results
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "="*80)
    print("GATE 5.12 DEV FAILURE DECOMPOSITION SUMMARY")
    print("="*80)
    print(f"Total DEV Queries: {n}")
    print(f"DEV Chunk Recall@1: {summary['baseline_metrics']['r1']}")
    print(f"DEV Chunk Recall@3: {summary['baseline_metrics']['r3']}")
    print(f"DEV Chunk Recall@5: {summary['baseline_metrics']['r5']}")
    print(f"DEV Chunk MRR:      {summary['baseline_metrics']['mrr']}")
    print(f"Total DEV Top-5 Failures: {summary['failed_queries_count']} / {n}")
    print("\nFailure Taxonomy Breakdown:")
    for tag, count in failure_counts.items():
        print(f"  - {tag}: {count} / {n} ({count/n*100:.1f}%)")

if __name__ == "__main__":
    main()
