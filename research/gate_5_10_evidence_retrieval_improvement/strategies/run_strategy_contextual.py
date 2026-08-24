"""
Gate 5.10 — Strategy A & B: Contextual Passage Embedding Representation
Adds deterministic Document Title and Section Headings to passage embeddings for dense retrieval.
"""

import json
import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
CHUNKS_FILE = os.path.join(ROOT_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
BENCHMARK_FILE = os.path.join(ROOT_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
GOLD_LABELS_FILE = os.path.join(ROOT_DIR, "gate_5_9_optimization", "chunk_gold_labels.json")

DOC_TITLES = {
    "DOC-NHS-004": "Asthma",
    "DOC-NHS-005": "Burns and scalds",
    "DOC-NHS-006": "Cuts and grazes",
    "DOC-NHS-007": "Dehydration",
    "DOC-NHS-008": "Diarrhoea and vomiting",
    "DOC-NHS-009": "Headaches",
    "DOC-NHS-010": "High temperature (fever) in children",
    "DOC-NHS-011": "Anaphylaxis"
}

def extract_section_title(text: str) -> str:
    lines = text.strip().split("\n")
    first_line = lines[0].strip() if lines else ""
    if len(first_line) < 60 and not first_line.endswith("."):
        return first_line
    return "Overview and Guidance"

def evaluate_strategy_contextual(candidate_depth=5):
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    # Construct contextual passage text
    contextual_passages = []
    for c in chunks:
        sid = c["parent_source_id"]
        doc_title = DOC_TITLES.get(sid, c.get("source_title", "Medical Guidance"))
        sec_title = extract_section_title(c["text"])
        ctx_text = f"Document: {doc_title} | Section: {sec_title} | Content: {c['text']}"
        contextual_passages.append(f"passage: {ctx_text}")

    chunk_embeddings = dense_model.encode(contextual_passages, normalize_embeddings=True)

    query_texts = [f"query: {q['query_text']}" for q in dev_queries]
    query_embeddings = dense_model.encode(query_texts, normalize_embeddings=True)

    sim_matrix = np.dot(query_embeddings, chunk_embeddings.T)

    results = []
    for i, q in enumerate(dev_queries):
        qid = q["query_id"]
        q_text = q["query_text"]
        acceptable_cids = gold_labels[qid]["gold_chunk_ids"]

        scores = sim_matrix[i]
        ranked_indices = np.argsort(-scores)
        top_k_indices = ranked_indices[:candidate_depth]
        dense_top_k_cids = [chunks[idx]["chunk_id"] for idx in top_k_indices]

        # Rerank Top-K (using clean original chunk text for reranking!)
        pairs = [(q_text, chunks[idx]["text"]) for idx in top_k_indices]
        r_scores = reranker.predict(pairs)
        r_order = np.argsort(-r_scores)
        r_top_k_cids = [dense_top_k_cids[idx] for idx in r_order]

        dense_hits = [cid in acceptable_cids for cid in dense_top_k_cids]
        r_hits = [cid in acceptable_cids for cid in r_top_k_cids]

        results.append({
            "query_id": qid,
            "query_text": q_text,
            "language_category": q["language_category"],
            "acceptable_gold_chunks": acceptable_cids,
            "dense_top_cids": dense_top_k_cids,
            "rerank_top_cids": r_top_k_cids,
            "dense_r1": dense_hits[0],
            "dense_r3": any(dense_hits[:3]),
            "dense_r5": any(dense_hits[:5]),
            "rerank_r1": r_hits[0],
            "rerank_r3": any(r_hits[:3]),
            "rerank_r5": any(r_hits[:5]),
            "dense_rank": (dense_hits.index(True) + 1) if any(dense_hits) else 0,
            "rerank_rank": (r_hits.index(True) + 1) if any(r_hits) else 0
        })

    n = len(dev_queries)
    metrics = {
        "candidate_depth": candidate_depth,
        "n": n,
        "dense_r1": round(sum(1 for r in results if r["dense_r1"]) / n * 100, 2),
        "dense_r3": round(sum(1 for r in results if r["dense_r3"]) / n * 100, 2),
        "dense_r5": round(sum(1 for r in results if r["dense_r5"]) / n * 100, 2),
        "dense_mrr": round(sum(1.0/r["dense_rank"] for r in results if r["dense_rank"] > 0) / n, 4),
        "rerank_r1": round(sum(1 for r in results if r["rerank_r1"]) / n * 100, 2),
        "rerank_r3": round(sum(1 for r in results if r["rerank_r3"]) / n * 100, 2),
        "rerank_r5": round(sum(1 for r in results if r["rerank_r5"]) / n * 100, 2),
        "rerank_mrr": round(sum(1.0/r["rerank_rank"] for r in results if r["rerank_rank"] > 0) / n, 4),
        "results": results
    }

    return metrics

if __name__ == "__main__":
    for depth in [5, 10, 15]:
        print(f"\nEvaluating Contextual Strategy with Depth K={depth}...")
        m = evaluate_strategy_contextual(candidate_depth=depth)
        print(f"Depth {depth}: Dense R@5={m['dense_r5']}%, Rerank R@1={m['rerank_r1']}%, R@3={m['rerank_r3']}%, R@5={m['rerank_r5']}%, MRR={m['rerank_mrr']}")
        out_file = os.path.join(BASE_DIR, f"strategy_contextual_k{depth}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2, ensure_ascii=False)
