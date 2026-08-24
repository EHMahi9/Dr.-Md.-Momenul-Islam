"""
Gate 5.8 — Independent Retrieval Generalization & Chunking Impact Validation Runner
Executes real model inference using intfloat/multilingual-e5-small and BAAI/bge-reranker-v2-m3.
"""

import os
import sys
import json
import time
import hashlib
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from typing import List, Dict, Tuple, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BENCHMARK_FILE = os.path.join(BASE_DIR, "benchmark", "frozen_benchmark.json")
EVALS_DIR = os.path.join(BASE_DIR, "evaluations")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

CORRECTED_CHUNKS_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_4f_semantic_chunking", "outputs", "candidate_a_heading_v2", "provenance_manifest.json"))
BASELINE_CHUNKS_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_4f_semantic_chunking", "outputs", "baseline_fixed", "provenance_manifest.json"))

os.makedirs(EVALS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def hash_file(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def cosine_similarity_matrix(query_embeddings: np.ndarray, doc_embeddings: np.ndarray) -> np.ndarray:
    # Assuming normalized embeddings, dot product = cosine similarity
    return np.dot(query_embeddings, doc_embeddings.T)

# -----------------------------------------------------------------------------
# RETRIEVAL EVALUATION PIPELINE
# -----------------------------------------------------------------------------
def evaluate_retrieval_on_corpus(
    corpus_name: str,
    chunks: List[Dict[str, Any]],
    queries: List[Dict[str, Any]],
    e5_model: SentenceTransformer,
    reranker: CrossEncoder
) -> Dict[str, Any]:
    print(f"\n=======================================================")
    print(f"EVALUATING RETRIEVAL ON: {corpus_name} ({len(chunks)} chunks)")
    print(f"=======================================================")

    # 1. Encode Corpus Passages (with 'passage: ' prefix)
    passage_texts = [f"passage: {c['text']}" for c in chunks]
    print(f"Encoding {len(passage_texts)} passages with E5...")
    t0 = time.time()
    passage_embeddings = e5_model.encode(passage_texts, normalize_embeddings=True, show_progress_bar=False)
    passage_enc_time = time.time() - t0
    print(f"Passages encoded in {passage_enc_time:.3f} s")

    # 2. Encode Queries (with 'query: ' prefix)
    query_texts = [f"query: {q['query_text']}" for q in queries]
    print(f"Encoding {len(query_texts)} queries with E5...")
    t0 = time.time()
    query_embeddings = e5_model.encode(query_texts, normalize_embeddings=True, show_progress_bar=False)
    query_enc_time = time.time() - t0
    print(f"Queries encoded in {query_enc_time:.3f} s")

    # 3. Dense Similarity Matrix
    sim_matrix = cosine_similarity_matrix(query_embeddings, passage_embeddings)

    # 4. Evaluate each query across Config A (Dense), Config B (Rerank Top-3), Config C (Rerank Top-5)
    query_results = []
    
    dense_latencies = []
    rerank3_latencies = []
    rerank5_latencies = []

    for i, q in enumerate(queries):
        qid = q["query_id"]
        q_text = q["query_text"]
        expected_sid = q["expected_source_id"]
        split = q["benchmark_split"]
        lang = q["language_category"]

        # Dense ranking
        t_dense_start = time.time()
        scores = sim_matrix[i]
        ranked_indices = np.argsort(-scores)
        t_dense_end = time.time()
        dense_latencies.append(t_dense_end - t_dense_start)

        # Retrieve top 5 dense candidates
        top5_indices = ranked_indices[:5]
        top5_scores = scores[top5_indices]
        top5_chunks = [chunks[idx] for idx in top5_indices]

        # Config A: Dense Results
        dense_top_sids = [c["parent_source_id"] for c in top5_chunks]
        dense_top1_score = float(top5_scores[0])
        dense_top2_score = float(top5_scores[1]) if len(top5_scores) > 1 else 0.0
        dense_margin = dense_top1_score - dense_top2_score

        # Config B: Rerank Top-3
        t_r3_start = time.time()
        r3_pairs = [(q_text, chunks[idx]["text"]) for idx in top5_indices[:3]]
        r3_scores = reranker.predict(r3_pairs)
        r3_order = np.argsort(-r3_scores)
        r3_ranked_indices = [top5_indices[:3][idx] for idx in r3_order]
        r3_top_sids = [chunks[idx]["parent_source_id"] for idx in r3_ranked_indices]
        r3_top1_score = float(r3_scores[r3_order[0]])
        t_r3_end = time.time()
        rerank3_latencies.append(t_r3_end - t_r3_start)

        # Config C: Rerank Top-5
        t_r5_start = time.time()
        r5_pairs = [(q_text, chunks[idx]["text"]) for idx in top5_indices]
        r5_scores = reranker.predict(r5_pairs)
        r5_order = np.argsort(-r5_scores)
        r5_ranked_indices = [top5_indices[idx] for idx in r5_order]
        r5_top_sids = [chunks[idx]["parent_source_id"] for idx in r5_ranked_indices]
        r5_top1_score = float(r5_scores[r5_order[0]])
        t_r5_end = time.time()
        rerank5_latencies.append(t_r5_end - t_r5_start)

        # Evaluate matches for valid queries
        is_valid = (expected_sid != "NONE")
        
        # Dense ranks
        dense_r1 = (dense_top_sids[0] == expected_sid) if is_valid else False
        dense_r3 = (expected_sid in dense_top_sids[:3]) if is_valid else False
        dense_r5 = (expected_sid in dense_top_sids[:5]) if is_valid else False
        dense_rank = (dense_top_sids.index(expected_sid) + 1) if (is_valid and expected_sid in dense_top_sids) else 0

        # Rerank 3 ranks
        r3_r1 = (r3_top_sids[0] == expected_sid) if is_valid else False
        r3_r3 = (expected_sid in r3_top_sids[:3]) if is_valid else False
        r3_rank = (r3_top_sids.index(expected_sid) + 1) if (is_valid and expected_sid in r3_top_sids) else 0

        # Rerank 5 ranks
        r5_r1 = (r5_top_sids[0] == expected_sid) if is_valid else False
        r5_r3 = (expected_sid in r5_top_sids[:3]) if is_valid else False
        r5_r5 = (expected_sid in r5_top_sids[:5]) if is_valid else False
        r5_rank = (r5_top_sids.index(expected_sid) + 1) if (is_valid and expected_sid in r5_top_sids) else 0

        # Check for degradation: E5 got rank 1, but reranker dropped it
        degraded_in_r3 = (dense_r1 and not r3_r1)
        degraded_in_r5 = (dense_r1 and not r5_r1)

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
            "degraded_in_r3": degraded_in_r3,
            "r5_top_sids": r5_top_sids,
            "r5_top1_score": r5_top1_score,
            "r5_rank": r5_rank,
            "r5_r1": r5_r1,
            "r5_r3": r5_r3,
            "r5_r5": r5_r5,
            "degraded_in_r5": degraded_in_r5,
            "top1_dense_chunk": top5_chunks[0]["text"][:100],
            "top1_r5_chunk": chunks[r5_ranked_indices[0]]["text"][:100]
        })

    # Aggregate Metrics by Subsets
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

        r3_degradations = sum(1 for q in valid_subset if q["degraded_in_r3"])
        r5_degradations = sum(1 for q in valid_subset if q["degraded_in_r5"])

        return {
            "n": n,
            "dense_R1": round(dense_r1 * 100, 2),
            "dense_R3": round(dense_r3 * 100, 2),
            "dense_R5": round(dense_r5 * 100, 2),
            "dense_MRR": round(dense_mrr, 4),
            "r3_R1": round(r3_r1 * 100, 2),
            "r3_R3": round(r3_r3 * 100, 2),
            "r3_MRR": round(r3_mrr, 4),
            "r3_degradations": r3_degradations,
            "r5_R1": round(r5_r1 * 100, 2),
            "r5_R3": round(r5_r3 * 100, 2),
            "r5_R5": round(r5_r5 * 100, 2),
            "r5_MRR": round(r5_mrr, 4),
            "r5_degradations": r5_degradations
        }

    # Aggregate by categories
    overall_valid = compute_metrics(query_results)
    dev_metrics = compute_metrics([q for q in query_results if q["benchmark_split"] == "DEV"])
    test_holdout_metrics = compute_metrics([q for q in query_results if q["benchmark_split"] == "TEST_HOLDOUT"])

    # Language breakdown (on all valid queries)
    valid_queries = [q for q in query_results if q["is_valid_query"]]
    lang_metrics = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        lang_subset = [q for q in valid_queries if q["language_category"] == lang]
        lang_metrics[lang] = compute_metrics(lang_subset)

    # Source breakdown
    source_metrics = {}
    for sid in sorted(list({q["expected_source_id"] for q in valid_queries})):
        src_subset = [q for q in valid_queries if q["expected_source_id"] == sid]
        source_metrics[sid] = compute_metrics(src_subset)

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
        "valid_queries": score_stats(valid_queries),
        "hard_negatives": score_stats(hn_subset),
        "out_of_corpus": score_stats(ooc_subset)
    }

    # Latencies
    latency_stats = {
        "passage_encoding_total_s": round(passage_enc_time, 3),
        "passage_encoding_per_chunk_ms": round((passage_enc_time / len(chunks)) * 1000, 2),
        "query_encoding_per_query_ms": round((query_enc_time / len(queries)) * 1000, 2),
        "dense_search_per_query_ms": round(float(np.mean(dense_latencies)) * 1000, 2),
        "rerank_top3_per_query_ms": round(float(np.mean(rerank3_latencies)) * 1000, 2),
        "rerank_top5_per_query_ms": round(float(np.mean(rerank5_latencies)) * 1000, 2),
        "total_e2e_config_a_ms": round(((query_enc_time / len(queries)) + float(np.mean(dense_latencies))) * 1000, 2),
        "total_e2e_config_b_ms": round(((query_enc_time / len(queries)) + float(np.mean(dense_latencies)) + float(np.mean(rerank3_latencies))) * 1000, 2),
        "total_e2e_config_c_ms": round(((query_enc_time / len(queries)) + float(np.mean(dense_latencies)) + float(np.mean(rerank5_latencies))) * 1000, 2)
    }

    degradation_cases = [
        {
            "query_id": q["query_id"],
            "query_text": q["query_text"],
            "language": q["language_category"],
            "expected_source": q["expected_source_id"],
            "dense_rank": q["dense_rank"],
            "r5_rank": q["r5_rank"],
            "dense_top_chunk": q["top1_dense_chunk"],
            "rerank_top_chunk": q["top1_r5_chunk"]
        }
        for q in valid_queries if q["degraded_in_r5"]
    ]

    return {
        "corpus_name": corpus_name,
        "total_chunks": len(chunks),
        "total_queries_evaluated": len(queries),
        "overall_valid_metrics": overall_valid,
        "dev_split_metrics": dev_metrics,
        "test_holdout_metrics": test_holdout_metrics,
        "language_breakdown": lang_metrics,
        "source_breakdown": source_metrics,
        "score_distributions": score_distributions,
        "latency_stats": latency_stats,
        "degradation_cases": degradation_cases,
        "query_results": query_results
    }

# -----------------------------------------------------------------------------
# MAIN EXECUTION
# -----------------------------------------------------------------------------
def main():
    print("Loading Frozen Benchmark...")
    with open(BENCHMARK_FILE, 'r', encoding='utf-8') as f:
        benchmark_queries = json.load(f)
    print(f"Loaded {len(benchmark_queries)} benchmark queries.")

    print("\nLoading Corrected Candidate A V2 Chunks...")
    with open(CORRECTED_CHUNKS_PATH, 'r', encoding='utf-8') as f:
        cand_a_chunks = json.load(f)
    print(f"Loaded {len(cand_a_chunks)} Candidate A V2 chunks.")

    print("\nLoading Baseline Fixed Chunks...")
    with open(BASELINE_CHUNKS_PATH, 'r', encoding='utf-8') as f:
        baseline_chunks = json.load(f)
    print(f"Loaded {len(baseline_chunks)} Baseline Fixed chunks.")

    # Load Models (Real ML Inference)
    print("\n--- Instantiating Real ML Models ---")
    t0 = time.time()
    e5_model = SentenceTransformer('intfloat/multilingual-e5-small')
    print(f"E5 Model instantiated in {time.time() - t0:.2f} s")

    t0 = time.time()
    reranker = CrossEncoder('BAAI/bge-reranker-v2-m3')
    print(f"BGE Reranker instantiated in {time.time() - t0:.2f} s")

    # Run 1: Evaluation on Corrected Candidate A V2 Chunks
    cand_a_eval = evaluate_retrieval_on_corpus(
        corpus_name="CORRECTED_STRUCTURAL_CHUNKS_CANDIDATE_A_V2",
        chunks=cand_a_chunks,
        queries=benchmark_queries,
        e5_model=e5_model,
        reranker=reranker
    )

    # Run 2: Evaluation on Baseline Fixed Chunks (Controlled Comparison)
    baseline_eval = evaluate_retrieval_on_corpus(
        corpus_name="BASELINE_FIXED_CHARACTER_CHUNKS",
        chunks=baseline_chunks,
        queries=benchmark_queries,
        e5_model=e5_model,
        reranker=reranker
    )

    # Save Evaluation Artifacts
    with open(os.path.join(EVALS_DIR, "gate_5_8_candidate_a_v2_eval.json"), 'w', encoding='utf-8') as f:
        json.dump(cand_a_eval, f, indent=2, ensure_ascii=False)

    with open(os.path.join(EVALS_DIR, "gate_5_8_baseline_fixed_eval.json"), 'w', encoding='utf-8') as f:
        json.dump(baseline_eval, f, indent=2, ensure_ascii=False)

    # Summary Comparison
    comparison = {
        "benchmark_hash": hash_file(BENCHMARK_FILE),
        "candidate_a_v2_metrics": {
            "overall_valid": cand_a_eval["overall_valid_metrics"],
            "dev_split": cand_a_eval["dev_split_metrics"],
            "test_holdout_split": cand_a_eval["test_holdout_metrics"],
            "language": cand_a_eval["language_breakdown"]
        },
        "baseline_fixed_metrics": {
            "overall_valid": baseline_eval["overall_valid_metrics"],
            "dev_split": baseline_eval["dev_split_metrics"],
            "test_holdout_split": baseline_eval["test_holdout_metrics"],
            "language": baseline_eval["language_breakdown"]
        }
    }

    with open(os.path.join(EVALS_DIR, "gate_5_8_chunking_comparison.json"), 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2)

    print("\n=======================================================")
    print("GATE 5.8 RETRIEVAL VALIDATION COMPLETE")
    print("=======================================================")
    print(f"Corrected Candidate A V2 Chunks (91 chunks):")
    print(f"  Overall Valid (N=80): Dense R@1={cand_a_eval['overall_valid_metrics']['dense_R1']}%, Top5+Rerank R@1={cand_a_eval['overall_valid_metrics']['r5_R1']}%, MRR={cand_a_eval['overall_valid_metrics']['r5_MRR']}")
    print(f"  Dev Split (N=40):     Dense R@1={cand_a_eval['dev_split_metrics']['dense_R1']}%, Top5+Rerank R@1={cand_a_eval['dev_split_metrics']['r5_R1']}%, MRR={cand_a_eval['dev_split_metrics']['r5_MRR']}")
    print(f"  Holdout Test (N=40):  Dense R@1={cand_a_eval['test_holdout_metrics']['dense_R1']}%, Top5+Rerank R@1={cand_a_eval['test_holdout_metrics']['r5_R1']}%, MRR={cand_a_eval['test_holdout_metrics']['r5_MRR']}")
    
    print(f"\nBaseline Fixed Chunks (63 chunks):")
    print(f"  Overall Valid (N=80): Dense R@1={baseline_eval['overall_valid_metrics']['dense_R1']}%, Top5+Rerank R@1={baseline_eval['overall_valid_metrics']['r5_R1']}%, MRR={baseline_eval['overall_valid_metrics']['r5_MRR']}")
    print(f"  Dev Split (N=40):     Dense R@1={baseline_eval['dev_split_metrics']['dense_R1']}%, Top5+Rerank R@1={baseline_eval['dev_split_metrics']['r5_R1']}%, MRR={baseline_eval['dev_split_metrics']['r5_MRR']}")
    print(f"  Holdout Test (N=40):  Dense R@1={baseline_eval['test_holdout_metrics']['dense_R1']}%, Top5+Rerank R@1={baseline_eval['test_holdout_metrics']['r5_R1']}%, MRR={baseline_eval['test_holdout_metrics']['r5_MRR']}")

if __name__ == "__main__":
    main()
