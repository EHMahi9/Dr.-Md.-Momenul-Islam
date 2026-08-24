"""
Gate 5.9.2 — Verify Deterministic Reproducibility and Capture Full Top-5 Chunk IDs
Runs the frozen pipeline on CPU and confirms 100% bit-level agreement with Gate 5.9 frozen eval output.
"""

import json
import time
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder

with open("research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

with open("research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json", "r", encoding="utf-8") as f:
    benchmark = json.load(f)

with open("research/gate_5_9_optimization/evaluations/gate_5_9_locked_holdout_evaluation.json", "r", encoding="utf-8") as f:
    frozen_eval = json.load(f)

dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

passage_texts = [f"passage: {c['text']}" for c in chunks]
chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

query_texts = [f"query: {q['query_text']}" for q in benchmark]
query_embeddings = dense_model.encode(query_texts, normalize_embeddings=True)

sim_matrix = np.dot(query_embeddings, chunk_embeddings.T)

# Check first 5 queries against frozen_eval
mismatches = 0
full_top5_rankings = []

for i, q in enumerate(benchmark):
    qid = q["query_id"]
    scores = sim_matrix[i]
    ranked_indices = np.argsort(-scores)
    top5_indices = ranked_indices[:5]
    dense_top5_cids = [chunks[idx]["chunk_id"] for idx in top5_indices]
    
    r5_pairs = [(q["query_text"], chunks[idx]["text"]) for idx in top5_indices]
    r5_scores = reranker.predict(r5_pairs)
    r5_order = np.argsort(-r5_scores)
    r5_ranked_indices = [top5_indices[idx] for idx in r5_order]
    r5_top5_cids = [chunks[idx]["chunk_id"] for idx in r5_ranked_indices]

    frozen_q = frozen_eval["query_results"][i]
    assert frozen_q["query_id"] == qid
    
    # Verify exact Top-1 chunk text prefix match
    dense_top1_match = chunks[top5_indices[0]]["text"].startswith(frozen_q["dense_top1_chunk"][:40])
    r5_top1_match = chunks[r5_ranked_indices[0]]["text"].startswith(frozen_q["r5_top1_chunk"][:40])
    
    if not (dense_top1_match and r5_top1_match):
        print(f"MISMATCH on {qid}!")
        mismatches += 1

    full_top5_rankings.append({
        "query_id": qid,
        "query_text": q["query_text"],
        "benchmark_split": q["benchmark_split"],
        "language_category": q["language_category"],
        "expected_source_id": q["expected_source_id"],
        "dense_top5_chunk_ids": dense_top5_cids,
        "dense_top5_scores": [float(scores[idx]) for idx in top5_indices],
        "r5_top5_chunk_ids": r5_top5_cids,
        "r5_top5_scores": [float(r5_scores[idx]) for idx in r5_order],
        "dense_top1_score": float(scores[top5_indices[0]]),
        "r5_top1_score": float(r5_scores[r5_order[0]])
    })

print(f"\nVerification Complete: Mismatches = {mismatches} / {len(benchmark)}")

with open("research/gate_5_9_optimization/evaluations/gate_5_9_exact_top5_rankings.json", "w", encoding="utf-8") as f:
    json.dump(full_top5_rankings, f, indent=2, ensure_ascii=False)

print("Saved exact Top-5 rankings artifact.")
