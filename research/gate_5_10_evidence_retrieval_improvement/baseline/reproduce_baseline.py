"""
Gate 5.10 — Phase 1: Baseline Reproduction on DEV Split
Verifies that the frozen Gate 5.9 pipeline is exactly reproducible on DEV queries.
"""

import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OPT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "gate_5_9_optimization"))
CHUNKS_FILE = os.path.join(OPT_DIR, "chunks", "hybrid_600", "provenance_manifest.json")
BENCHMARK_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json"))
GOLD_LABELS_FILE = os.path.join(OPT_DIR, "chunk_gold_labels.json")
FROZEN_EVAL_FILE = os.path.join(OPT_DIR, "evaluations", "gate_5_9_2_audit_results.json")

def main():
    print("Loading artifacts for baseline reproduction...")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    with open(FROZEN_EVAL_FILE, "r", encoding="utf-8") as f:
        frozen_audit = json.load(f)
    frozen_dev_results = {q["query_id"]: q for q in frozen_audit["query_evaluations"] if q["benchmark_split"] == "DEV"}

    print(f"Total chunks in corpus: {len(chunks)}")
    print(f"Total DEV queries: {len(dev_queries)}")

    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    query_texts = [f"query: {q['query_text']}" for q in dev_queries]
    query_embeddings = dense_model.encode(query_texts, normalize_embeddings=True)

    sim_matrix = np.dot(query_embeddings, chunk_embeddings.T)

    mismatches = 0
    dev_eval_results = []

    for i, q in enumerate(dev_queries):
        qid = q["query_id"]
        q_text = q["query_text"]
        expected_sid = q["expected_source_id"]
        acceptable_cids = gold_labels[qid]["gold_chunk_ids"]

        scores = sim_matrix[i]
        ranked_indices = np.argsort(-scores)

        # Dense Top-5
        top5_indices = ranked_indices[:5]
        dense_top5_cids = [chunks[idx]["chunk_id"] for idx in top5_indices]

        # Reranker Top-5
        r5_pairs = [(q_text, chunks[idx]["text"]) for idx in top5_indices]
        r5_scores = reranker.predict(r5_pairs)
        r5_order = np.argsort(-r5_scores)
        r5_top5_cids = [dense_top5_cids[idx] for idx in r5_order]

        # Verify against frozen results
        frozen_q = frozen_dev_results[qid]
        if frozen_q["dense_top5_chunk_ids"] != dense_top5_cids or frozen_q["r5_top5_chunk_ids"] != r5_top5_cids:
            print(f"MISMATCH on {qid}!")
            mismatches += 1

        dense_chunk_hits = [cid in acceptable_cids for cid in dense_top5_cids]
        r5_chunk_hits = [cid in acceptable_cids for cid in r5_top5_cids]

        dev_eval_results.append({
            "query_id": qid,
            "query_text": q_text,
            "language_category": q["language_category"],
            "expected_source_id": expected_sid,
            "acceptable_gold_chunks": acceptable_cids,
            "dense_top5_chunk_ids": dense_top5_cids,
            "r5_top5_chunk_ids": r5_top5_cids,
            "dense_chunk_r1": dense_chunk_hits[0],
            "dense_chunk_r3": any(dense_chunk_hits[:3]),
            "dense_chunk_r5": any(dense_chunk_hits[:5]),
            "r5_chunk_r1": r5_chunk_hits[0],
            "r5_chunk_r3": any(r5_chunk_hits[:3]),
            "r5_chunk_r5": any(r5_chunk_hits[:5]),
            "all_ranked_chunk_ids": [chunks[idx]["chunk_id"] for idx in ranked_indices]
        })

    print(f"\nBaseline Reproduction Result: Mismatches = {mismatches} / {len(dev_queries)}")
    
    n = len(dev_queries)
    d_r1 = sum(1 for q in dev_eval_results if q["dense_chunk_r1"]) / n
    d_r3 = sum(1 for q in dev_eval_results if q["dense_chunk_r3"]) / n
    d_r5 = sum(1 for q in dev_eval_results if q["dense_chunk_r5"]) / n

    r_r1 = sum(1 for q in dev_eval_results if q["r5_chunk_r1"]) / n
    r_r3 = sum(1 for q in dev_eval_results if q["r5_chunk_r3"]) / n
    r_r5 = sum(1 for q in dev_eval_results if q["r5_chunk_r5"]) / n

    print(f"Dense Chunk Recall:    R@1={d_r1*100:.2f}%, R@3={d_r3*100:.2f}%, R@5={d_r5*100:.2f}%")
    print(f"Reranked Chunk Recall: R@1={r_r1*100:.2f}%, R@3={r_r3*100:.2f}%, R@5={r_r5*100:.2f}%")

    out_file = os.path.join(BASE_DIR, "dev_baseline_reproduced.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dev_eval_results, f, indent=2, ensure_ascii=False)

    print(f"Saved reproduced baseline to {out_file}")

if __name__ == "__main__":
    main()
