"""
Gate 5.10 — Strategy D: Hybrid Retrieval (Lexical BM25 + Dense E5 with RRF)
Combines deterministic BM25 lexical ranking with dense semantic similarity via Reciprocal Rank Fusion.
"""

import json
import os
import re
import math
import numpy as np
from collections import Counter
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
CHUNKS_FILE = os.path.join(ROOT_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
BENCHMARK_FILE = os.path.join(ROOT_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
GOLD_LABELS_FILE = os.path.join(ROOT_DIR, "gate_5_9_optimization", "chunk_gold_labels.json")

class BM25Okapi:
    def __init__(self, corpus_docs, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus_docs)
        self.tokenized_corpus = [self._tokenize(doc) for doc in corpus_docs]
        self.doc_lens = [len(doc) for doc in self.tokenized_corpus]
        self.avgdl = sum(self.doc_lens) / self.corpus_size if self.corpus_size > 0 else 1.0

        # Calculate document frequencies
        self.df = defaultdict(int)
        for doc in self.tokenized_corpus:
            for term in set(doc):
                self.df[term] += 1

        # Calculate IDFs
        self.idf = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def _tokenize(self, text: str):
        return re.findall(r'[\w]+', text.lower())

    def get_scores(self, query: str):
        query_terms = self._tokenize(query)
        scores = np.zeros(self.corpus_size)

        for term in query_terms:
            if term not in self.idf:
                continue
            idf_val = self.idf[term]
            for i, doc in enumerate(self.tokenized_corpus):
                if term not in doc:
                    continue
                tf = doc.count(term)
                denom = tf + self.k1 * (1 - self.b + self.b * (self.doc_lens[i] / self.avgdl))
                scores[i] += idf_val * (tf * (self.k1 + 1.0) / denom)

        return scores

def evaluate_hybrid_retrieval(candidate_depth=10, rrf_k=60):
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    # Dense embeddings
    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    query_texts = [f"query: {q['query_text']}" for q in dev_queries]
    query_embeddings = dense_model.encode(query_texts, normalize_embeddings=True)

    sim_matrix = np.dot(query_embeddings, chunk_embeddings.T)

    # BM25 index over raw chunk texts
    chunk_raw_texts = [c["text"] for c in chunks]
    bm25 = BM25Okapi(chunk_raw_texts)

    results = []
    for i, q in enumerate(dev_queries):
        qid = q["query_id"]
        q_text = q["query_text"]
        acceptable_cids = gold_labels[qid]["gold_chunk_ids"]

        # Dense ranking
        dense_scores = sim_matrix[i]
        dense_rank_order = np.argsort(-dense_scores)

        # BM25 ranking
        bm25_scores = bm25.get_scores(q_text)
        bm25_rank_order = np.argsort(-bm25_scores)

        # Reciprocal Rank Fusion (RRF)
        rrf_scores = np.zeros(len(chunks))
        for rank, idx in enumerate(dense_rank_order):
            rrf_scores[idx] += 1.0 / (rrf_k + rank + 1)
        for rank, idx in enumerate(bm25_rank_order):
            rrf_scores[idx] += 1.0 / (rrf_k + rank + 1)

        fused_rank_order = np.argsort(-rrf_scores)
        top_k_indices = fused_rank_order[:candidate_depth]
        fused_top_k_cids = [chunks[idx]["chunk_id"] for idx in top_k_indices]

        # Rerank Top-K with Cross-Encoder
        pairs = [(q_text, chunks[idx]["text"]) for idx in top_k_indices]
        r_scores = reranker.predict(pairs)
        r_order = np.argsort(-r_scores)
        r_top_k_cids = [fused_top_k_cids[idx] for idx in r_order]

        fused_hits = [cid in acceptable_cids for cid in fused_top_k_cids]
        r_hits = [cid in acceptable_cids for cid in r_top_k_cids]

        results.append({
            "query_id": qid,
            "query_text": q_text,
            "language_category": q["language_category"],
            "acceptable_gold_chunks": acceptable_cids,
            "fused_top_cids": fused_top_k_cids,
            "rerank_top_cids": r_top_k_cids,
            "fused_r1": fused_hits[0],
            "fused_r3": any(fused_hits[:3]),
            "fused_r5": any(fused_hits[:5]),
            "rerank_r1": r_hits[0],
            "rerank_r3": any(r_hits[:3]),
            "rerank_r5": any(r_hits[:5]),
            "fused_rank": (fused_hits.index(True) + 1) if any(fused_hits) else 0,
            "rerank_rank": (r_hits.index(True) + 1) if any(r_hits) else 0
        })

    n = len(dev_queries)
    metrics = {
        "candidate_depth": candidate_depth,
        "rrf_k": rrf_k,
        "n": n,
        "fused_r1": round(sum(1 for r in results if r["fused_r1"]) / n * 100, 2),
        "fused_r3": round(sum(1 for r in results if r["fused_r3"]) / n * 100, 2),
        "fused_r5": round(sum(1 for r in results if r["fused_r5"]) / n * 100, 2),
        "fused_mrr": round(sum(1.0/r["fused_rank"] for r in results if r["fused_rank"] > 0) / n, 4),
        "rerank_r1": round(sum(1 for r in results if r["rerank_r1"]) / n * 100, 2),
        "rerank_r3": round(sum(1 for r in results if r["rerank_r3"]) / n * 100, 2),
        "rerank_r5": round(sum(1 for r in results if r["rerank_r5"]) / n * 100, 2),
        "rerank_mrr": round(sum(1.0/r["rerank_rank"] for r in results if r["rerank_rank"] > 0) / n, 4),
        "results": results
    }

    return metrics

if __name__ == "__main__":
    for depth in [5, 10, 15]:
        print(f"\nEvaluating Hybrid BM25+Dense Strategy with Depth K={depth}...")
        m = evaluate_hybrid_retrieval(candidate_depth=depth)
        print(f"Depth {depth}: Fused R@5={m['fused_r5']}%, Rerank R@1={m['rerank_r1']}%, R@3={m['rerank_r3']}%, R@5={m['rerank_r5']}%, MRR={m['rerank_mrr']}")
        out_file = os.path.join(BASE_DIR, f"strategy_hybrid_bm25_k{depth}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2, ensure_ascii=False)
