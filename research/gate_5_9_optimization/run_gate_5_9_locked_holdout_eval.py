"""
Gate 5.9 — Single Locked Holdout Evaluation Runner
Executes the frozen HYBRID_600 configuration exactly ONCE on the full benchmark including the locked holdout split.
"""

import os
import json
import time
import hashlib
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from typing import List, Dict, Tuple, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FROZEN_CONFIG_PATH = os.path.join(BASE_DIR, "frozen_config_manifest.json")
BENCHMARK_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json"))
CHUNKS_PATH = os.path.join(BASE_DIR, "chunks", "hybrid_600", "provenance_manifest.json")
EVALS_DIR = os.path.join(BASE_DIR, "evaluations")

def hash_file(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def cosine_similarity_matrix(query_embeddings: np.ndarray, doc_embeddings: np.ndarray) -> np.ndarray:
    return np.dot(query_embeddings, doc_embeddings.T)

def main():
    print("=======================================================", flush=True)
    print("GATE 5.9 — SINGLE LOCKED HOLDOUT EVALUATION EXECUTION", flush=True)
    print("=======================================================", flush=True)

    with open(FROZEN_CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"Loaded Frozen Config: Strategy={config['selected_chunking_strategy']}, Target={config['chunk_size_parameters']['target_char_size']} chars", flush=True)

    with open(BENCHMARK_FILE, 'r', encoding='utf-8') as f:
        benchmark = json.load(f)
    print(f"Loaded Frozen Benchmark: {len(benchmark)} total queries", flush=True)

    with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    print(f"Loaded HYBRID_600 Chunks: {len(chunks)} chunks across all 8 NHS documents", flush=True)

    # Load Real Models
    print("Instantiating Real ML Models...", flush=True)
    t0 = time.time()
    e5_model = SentenceTransformer(config["retrieval_architecture"]["dense_embedding_model"])
    print(f"E5 instantiated in {time.time() - t0:.2f} s", flush=True)

    t0 = time.time()
    reranker = CrossEncoder(config["retrieval_architecture"]["reranker_model"])
    print(f"BGE Reranker instantiated in {time.time() - t0:.2f} s", flush=True)

    # Encode Passages
    passage_texts = [f"passage: {c['text']}" for c in chunks]
    t0 = time.time()
    passage_embeddings = e5_model.encode(passage_texts, normalize_embeddings=True, show_progress_bar=False)
    passage_enc_time = time.time() - t0
    print(f"Encoded {len(passage_texts)} passages in {passage_enc_time:.3f} s", flush=True)

    # Encode Queries
    query_texts = [f"query: {q['query_text']}" for q in benchmark]
    t0 = time.time()
    query_embeddings = e5_model.encode(query_texts, normalize_embeddings=True, show_progress_bar=False)
    query_enc_time = time.time() - t0
    print(f"Encoded {len(query_texts)} queries in {query_enc_time:.3f} s", flush=True)

    sim_matrix = cosine_similarity_matrix(query_embeddings, passage_embeddings)

    query_results = []
    dense_latencies = []
    rerank_latencies = []

    for i, q in enumerate(benchmark):
        qid = q["query_id"]
        q_text = q["query_text"]
        expected_sid = q["expected_source_id"]
        split = q["benchmark_split"]
        lang = q["language_category"]

        t_start = time.time()
        scores = sim_matrix[i]
        ranked_indices = np.argsort(-scores)
        dense_latencies.append(time.time() - t_start)

        top5_indices = ranked_indices[:5]
        top5_scores = scores[top5_indices]
        top5_chunks = [chunks[idx] for idx in top5_indices]

        # Config A: Dense
        dense_top_sids = [c["parent_source_id"] for c in top5_chunks]
        dense_top1_score = float(top5_scores[0])
        dense_top2_score = float(top5_scores[1]) if len(top5_scores) > 1 else 0.0
        dense_margin = dense_top1_score - dense_top2_score

        # Rerank Top-5 Candidates (Single batch)
        t_r = time.time()
        r5_pairs = [(q_text, chunks[idx]["text"]) for idx in top5_indices]
        r5_scores = reranker.predict(r5_pairs)
        rerank_latencies.append(time.time() - t_r)

        # Config B: Rerank Top-3
        r3_scores = r5_scores[:3]
        r3_order = np.argsort(-r3_scores)
        r3_ranked_indices = [top5_indices[:3][idx] for idx in r3_order]
        r3_top_sids = [chunks[idx]["parent_source_id"] for idx in r3_ranked_indices]
        r3_top1_score = float(r3_scores[r3_order[0]])

        # Config C: Rerank Top-5
        r5_order = np.argsort(-r5_scores)
        r5_ranked_indices = [top5_indices[idx] for idx in r5_order]
        r5_top_sids = [chunks[idx]["parent_source_id"] for idx in r5_ranked_indices]
        r5_top1_score = float(r5_scores[r5_order[0]])

        is_valid = (expected_sid != "NONE")
        dense_r1 = (dense_top_sids[0] == expected_sid) if is_valid else False
        dense_r3 = (expected_sid in dense_top_sids[:3]) if is_valid else False
        dense_r5 = (expected_sid in dense_top_sids[:5]) if is_valid else False
        dense_rank = (dense_top_sids.index(expected_sid) + 1) if (is_valid and expected_sid in dense_top_sids) else 0

        r3_r1 = (r3_top_sids[0] == expected_sid) if is_valid else False
        r3_r3 = (expected_sid in r3_top_sids[:3]) if is_valid else False
        r3_rank = (r3_top_sids.index(expected_sid) + 1) if (is_valid and expected_sid in r3_top_sids) else 0

        r5_r1 = (r5_top_sids[0] == expected_sid) if is_valid else False
        r5_r3 = (expected_sid in r5_top_sids[:3]) if is_valid else False
        r5_r5 = (expected_sid in r5_top_sids[:5]) if is_valid else False
        r5_rank = (r5_top_sids.index(expected_sid) + 1) if (is_valid and expected_sid in r5_top_sids) else 0

        degraded_in_r5 = (dense_r1 and not r5_r1)
        improved_in_r5 = (not dense_r1 and r5_r1)

        query_results.append({
            "query_id": qid,
            "query_text": q_text,
            "expected_source_id": expected_sid,
            "benchmark_split": split,
            "language_category": lang,
            "is_valid_query": is_valid,
            "dense_top_sids": dense_top_sids,
            "dense_top1_score": dense_top1_score,
            "dense_margin": dense_margin,
            "dense_rank": dense_rank,
            "dense_r1": dense_r1,
            "dense_r3": dense_r3,
            "dense_r5": dense_r5,
            "r3_top_sids": r3_top_sids,
            "r3_top1_score": r3_top1_score,
            "r3_rank": r3_rank,
            "r3_r1": r3_r1,
            "r3_r3": r3_r3,
            "r5_top_sids": r5_top_sids,
            "r5_top1_score": r5_top1_score,
            "r5_rank": r5_rank,
            "r5_r1": r5_r1,
            "r5_r3": r5_r3,
            "r5_r5": r5_r5,
            "degraded_in_r5": degraded_in_r5,
            "improved_in_r5": improved_in_r5,
            "dense_top1_chunk": top5_chunks[0]["text"][:80],
            "r5_top1_chunk": chunks[r5_ranked_indices[0]]["text"][:80]
        })

    def compute_metrics(subset: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid_subset = [q for q in subset if q["is_valid_query"]]
        if not valid_subset:
            return {"n": 0}
        n = len(valid_subset)
        
        dense_r1 = sum(1 for q in valid_subset if q["dense_r1"]) / n
        dense_r3 = sum(1 for q in valid_subset if q["dense_r3"]) / n
        dense_r5 = sum(1 for q in valid_subset if q["dense_r5"]) / n
        dense_mrr = sum((1.0 / q["dense_rank"]) if q["dense_rank"] > 0 else 0.0 for q in valid_subset) / n

        r3_r1 = sum(1 for q in valid_subset if q["r3_r1"]) / n
        r3_r3 = sum(1 for q in valid_subset if q["r3_r3"]) / n
        r3_mrr = sum((1.0 / q["r3_rank"]) if q["r3_rank"] > 0 else 0.0 for q in valid_subset) / n

        r5_r1 = sum(1 for q in valid_subset if q["r5_r1"]) / n
        r5_r3 = sum(1 for q in valid_subset if q["r5_r3"]) / n
        r5_r5 = sum(1 for q in valid_subset if q["r5_r5"]) / n
        r5_mrr = sum((1.0 / q["r5_rank"]) if q["r5_rank"] > 0 else 0.0 for q in valid_subset) / n

        r5_degradations = sum(1 for q in valid_subset if q["degraded_in_r5"])
        r5_improvements = sum(1 for q in valid_subset if q["improved_in_r5"])

        return {
            "n": n,
            "dense_R1": round(dense_r1 * 100, 2),
            "dense_R3": round(dense_r3 * 100, 2),
            "dense_R5": round(dense_r5 * 100, 2),
            "dense_MRR": round(dense_mrr, 4),
            "r3_R1": round(r3_r1 * 100, 2),
            "r3_R3": round(r3_r3 * 100, 2),
            "r3_MRR": round(r3_mrr, 4),
            "r5_R1": round(r5_r1 * 100, 2),
            "r5_R3": round(r5_r3 * 100, 2),
            "r5_R5": round(r5_r5 * 100, 2),
            "r5_MRR": round(r5_mrr, 4),
            "r5_degradations": r5_degradations,
            "r5_improvements": r5_improvements
        }

    overall_valid = compute_metrics(query_results)
    dev_metrics = compute_metrics([q for q in query_results if q["benchmark_split"] == "DEV"])
    holdout_metrics = compute_metrics([q for q in query_results if q["benchmark_split"] == "TEST_HOLDOUT"])

    # Language breakdown on LOCKED HOLDOUT
    holdout_queries = [q for q in query_results if q["benchmark_split"] == "TEST_HOLDOUT"]
    holdout_lang_metrics = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        lang_subset = [q for q in holdout_queries if q["language_category"] == lang]
        holdout_lang_metrics[lang] = compute_metrics(lang_subset)

    # Negative Score Distribution Analysis
    hn_subset = [q for q in query_results if q["benchmark_split"] == "HARD_NEGATIVE"]
    ooc_subset = [q for q in query_results if q["benchmark_split"] == "OUT_OF_CORPUS"]

    def score_stats(q_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        dense_scores = [q["dense_top1_score"] for q in q_list]
        margins = [q["dense_margin"] for q in q_list]
        r5_scores = [q["r5_top1_score"] for q in q_list]
        return {
            "n": len(q_list),
            "dense_top1_mean": round(float(np.mean(dense_scores)), 4) if dense_scores else 0,
            "dense_top1_min": round(float(np.min(dense_scores)), 4) if dense_scores else 0,
            "dense_top1_max": round(float(np.max(dense_scores)), 4) if dense_scores else 0,
            "margin_mean": round(float(np.mean(margins)), 4) if margins else 0,
            "r5_top1_mean": round(float(np.mean(r5_scores)), 4) if r5_scores else 0,
            "r5_top1_min": round(float(np.min(r5_scores)), 4) if r5_scores else 0,
            "r5_top1_max": round(float(np.max(r5_scores)), 4) if r5_scores else 0
        }

    score_distributions = {
        "valid_queries": score_stats([q for q in query_results if q["is_valid_query"]]),
        "dev_queries": score_stats([q for q in query_results if q["benchmark_split"] == "DEV"]),
        "holdout_queries": score_stats(holdout_queries),
        "hard_negatives": score_stats(hn_subset),
        "out_of_corpus": score_stats(ooc_subset)
    }

    latency_stats = {
        "passage_encoding_total_s": round(passage_enc_time, 3),
        "passage_encoding_per_chunk_ms": round((passage_enc_time / len(chunks)) * 1000, 2),
        "query_encoding_per_query_ms": round((query_enc_time / len(benchmark)) * 1000, 2),
        "dense_search_per_query_ms": round(float(np.mean(dense_latencies)) * 1000, 2),
        "rerank_top5_per_query_ms": round(float(np.mean(rerank_latencies)) * 1000, 2),
        "total_e2e_config_a_ms": round(((query_enc_time / len(benchmark)) + float(np.mean(dense_latencies))) * 1000, 2),
        "total_e2e_config_c_ms": round(((query_enc_time / len(benchmark)) + float(np.mean(dense_latencies)) + float(np.mean(rerank_latencies))) * 1000, 2)
    }

    final_report = {
        "frozen_configuration": config,
        "total_chunks": len(chunks),
        "total_queries_evaluated": len(benchmark),
        "overall_valid_metrics": overall_valid,
        "dev_split_metrics": dev_metrics,
        "locked_holdout_metrics": holdout_metrics,
        "locked_holdout_language_breakdown": holdout_lang_metrics,
        "score_distributions": score_distributions,
        "latency_stats": latency_stats,
        "query_results": query_results
    }

    out_file = os.path.join(EVALS_DIR, "gate_5_9_locked_holdout_evaluation.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2)
    print(f"\nSaved Locked Holdout Evaluation Results to {out_file}", flush=True)

    print("\n=======================================================", flush=True)
    print("GATE 5.9 LOCKED HOLDOUT EVALUATION COMPLETE", flush=True)
    print("=======================================================", flush=True)
    print(f"Overall Valid (N=80):   Dense R@1={overall_valid['dense_R1']}%, Top-5+Rerank R@1={overall_valid['r5_R1']}%, MRR={overall_valid['r5_MRR']}", flush=True)
    print(f"DEV Split (N=40):       Dense R@1={dev_metrics['dense_R1']}%, Top-5+Rerank R@1={dev_metrics['r5_R1']}%, MRR={dev_metrics['r5_MRR']}", flush=True)
    print(f"LOCKED HOLDOUT (N=40):  Dense R@1={holdout_metrics['dense_R1']}%, Top-5+Rerank R@1={holdout_metrics['r5_R1']}%, MRR={holdout_metrics['r5_MRR']}", flush=True)
    print(f"\nLocked Holdout Language Breakdown:", flush=True)
    for l, m in holdout_lang_metrics.items():
        print(f"  {l} (N={m['n']}): Dense R@1={m['dense_R1']}%, Top-5+Rerank R@1={m['r5_R1']}%, MRR={m['r5_MRR']}", flush=True)

if __name__ == "__main__":
    main()
