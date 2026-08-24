"""
Evaluate the 20 unsupported queries (12 Hard Negative + 8 Out-of-Corpus)
using the exact frozen Gate 5.12 configuration.
"""

import json
import os
import time
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from run_single_holdout_validation import normalize_query_text, CHUNKS_FILE, BENCHMARK_FILE, FROZEN_CONFIG_FILE, EVAL_OUT_FILE

def main():
    with open(FROZEN_CONFIG_FILE, "r", encoding="utf-8") as f:
        frozen_config = json.load(f)

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    unsupported_queries = [q for q in benchmark if q["benchmark_split"] in ("HARD_NEGATIVE", "OUT_OF_CORPUS")]
    print(f"Total Unsupported Queries to evaluate: {len(unsupported_queries)}")

    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    unsupported_results = []
    for q in unsupported_queries:
        qid = q["query_id"]
        q_text = q["query_text"]
        norm_q_text = normalize_query_text(q_text)
        lang = q["language_category"]
        q_type = q["query_type"]
        split = q["benchmark_split"]

        q_emb = dense_model.encode([f"query: {norm_q_text}"], normalize_embeddings=True)
        scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-scores)[:15]

        pairs = [(norm_q_text, chunks[idx]["text"]) for idx in top15_indices]
        r_scores = reranker.predict(pairs)
        r_order = np.argsort(-r_scores)

        top1_idx = top15_indices[r_order[0]]
        top1_score = float(r_scores[r_order[0]])
        dense_top1_score = float(scores[top15_indices[0]])

        unsupported_results.append({
            "query_id": qid,
            "query_text": q_text,
            "normalized_query_text": norm_q_text,
            "language_category": lang,
            "query_type": q_type,
            "benchmark_split": split,
            "dense_top1_cid": chunks[top15_indices[0]]["chunk_id"],
            "dense_top1_score": dense_top1_score,
            "rerank_top1_cid": chunks[top1_idx]["chunk_id"],
            "rerank_top1_score": top1_score,
            "rerank_top5_cids": [chunks[top15_indices[i]]["chunk_id"] for i in r_order[:5]],
            "rerank_top5_scores": [float(r_scores[i]) for i in r_order[:5]]
        })

    # Update the main evaluation JSON
    with open(EVAL_OUT_FILE, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    eval_data["sample_sizes"]["unsupported_queries_n"] = len(unsupported_results)
    eval_data["unsupported_queries_evaluation"] = {
        "total_unsupported_queries": len(unsupported_results),
        "hard_negatives_n": len([r for r in unsupported_results if r["benchmark_split"] == "HARD_NEGATIVE"]),
        "out_of_corpus_n": len([r for r in unsupported_results if r["benchmark_split"] == "OUT_OF_CORPUS"]),
        "max_reranker_score": max(r["rerank_top1_score"] for r in unsupported_results),
        "min_reranker_score": min(r["rerank_top1_score"] for r in unsupported_results),
        "avg_reranker_score": sum(r["rerank_top1_score"] for r in unsupported_results) / len(unsupported_results),
        "unsupported_queries": unsupported_results
    }

    with open(EVAL_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2, ensure_ascii=False)

    print(f"Appended {len(unsupported_results)} unsupported queries to {EVAL_OUT_FILE}")
    print(f"Max Reranker Score on Unsupported: {eval_data['unsupported_queries_evaluation']['max_reranker_score']:.4f}")
    print(f"Min Reranker Score on Unsupported: {eval_data['unsupported_queries_evaluation']['min_reranker_score']:.4f}")
    print(f"Avg Reranker Score on Unsupported: {eval_data['unsupported_queries_evaluation']['avg_reranker_score']:.4f}")

if __name__ == "__main__":
    main()
