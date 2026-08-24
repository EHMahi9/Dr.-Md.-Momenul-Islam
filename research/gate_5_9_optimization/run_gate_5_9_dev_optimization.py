"""
Gate 5.9 — Development-Only Chunking Optimization Runner
Evaluates 5 chunking candidates strictly on the 40 DEV queries (Asthma, Burns, Cuts, Dehydration).
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
BENCHMARK_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json"))
EVALS_DIR = os.path.join(BASE_DIR, "evaluations")
CHUNKS_DIR = os.path.join(BASE_DIR, "chunks")

DEV_SOURCES = {"DOC-NHS-004", "DOC-NHS-005", "DOC-NHS-006", "DOC-NHS-007"}

def hash_file(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def cosine_similarity_matrix(query_embeddings: np.ndarray, doc_embeddings: np.ndarray) -> np.ndarray:
    return np.dot(query_embeddings, doc_embeddings.T)

def evaluate_dev_on_candidate(
    cand_name: str,
    chunks: List[Dict[str, Any]],
    dev_queries: List[Dict[str, Any]],
    e5_model: SentenceTransformer,
    reranker: CrossEncoder
) -> Dict[str, Any]:
    print(f"\n=======================================================", flush=True)
    print(f"EVALUATING DEV ON: {cand_name} ({len(chunks)} chunks)", flush=True)
    print(f"=======================================================", flush=True)

    passage_texts = [f"passage: {c['text']}" for c in chunks]
    t0 = time.time()
    passage_embeddings = e5_model.encode(passage_texts, normalize_embeddings=True, show_progress_bar=False)
    passage_enc_time = time.time() - t0

    query_texts = [f"query: {q['query_text']}" for q in dev_queries]
    t0 = time.time()
    query_embeddings = e5_model.encode(query_texts, normalize_embeddings=True, show_progress_bar=False)
    query_enc_time = time.time() - t0

    sim_matrix = cosine_similarity_matrix(query_embeddings, passage_embeddings)

    query_results = []
    dense_latencies = []
    rerank_latencies = []

    for i, q in enumerate(dev_queries):
        qid = q["query_id"]
        q_text = q["query_text"]
        expected_sid = q["expected_source_id"]
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

        # Rerank Top-5 Candidates (Single batch of 5 pairs per query)
        t_r = time.time()
        r5_pairs = [(q_text, chunks[idx]["text"]) for idx in top5_indices]
        r5_scores = reranker.predict(r5_pairs)
        t_r_end = time.time()
        rerank_latencies.append(t_r_end - t_r)

        # Config B: Rerank Top-3 (take first 3 scores)
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

        query_results.append({
            "query_id": qid,
            "query_text": q_text,
            "expected_source_id": expected_sid,
            "language_category": lang,
            "dense_top_sids": dense_top_sids,
            "dense_rank": dense_rank,
            "dense_r1": dense_r1,
            "dense_r3": dense_r3,
            "dense_r5": dense_r5,
            "r3_top_sids": r3_top_sids,
            "r3_rank": r3_rank,
            "r3_r1": r3_r1,
            "r3_r3": r3_r3,
            "r5_top_sids": r5_top_sids,
            "r5_rank": r5_rank,
            "r5_r1": r5_r1,
            "r5_r3": r5_r3,
            "r5_r5": r5_r5,
            "degraded_in_r5": degraded_in_r5,
            "dense_top_chunk": top5_chunks[0]["text"][:80],
            "r5_top_chunk": chunks[r5_ranked_indices[0]]["text"][:80]
        })

    def compute_metrics(subset):
        n = len(subset)
        if n == 0: return {"n": 0}
        dense_r1 = sum(1 for q in subset if q["dense_r1"]) / n
        dense_r3 = sum(1 for q in subset if q["dense_r3"]) / n
        dense_r5 = sum(1 for q in subset if q["dense_r5"]) / n
        dense_mrr = sum((1.0 / q["dense_rank"]) if q["dense_rank"] > 0 else 0.0 for q in subset) / n

        r3_r1 = sum(1 for q in subset if q["r3_r1"]) / n
        r3_r3 = sum(1 for q in subset if q["r3_r3"]) / n
        r3_mrr = sum((1.0 / q["r3_rank"]) if q["r3_rank"] > 0 else 0.0 for q in subset) / n

        r5_r1 = sum(1 for q in subset if q["r5_r1"]) / n
        r5_r3 = sum(1 for q in subset if q["r5_r3"]) / n
        r5_r5 = sum(1 for q in subset if q["r5_r5"]) / n
        r5_mrr = sum((1.0 / q["r5_rank"]) if q["r5_rank"] > 0 else 0.0 for q in subset) / n

        r5_degradations = sum(1 for q in subset if q["degraded_in_r5"])

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
            "r5_degradations": r5_degradations
        }

    overall = compute_metrics(query_results)
    
    # Language breakdowns
    lang_breakdown = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        l_subset = [q for q in query_results if q["language_category"] == lang]
        lang_breakdown[lang] = compute_metrics(l_subset)

    # Compute Composite Engineering Index (CEI)
    # CEI = 0.35 * R@1 + 0.25 * (100 * MRR) + 0.20 * R@1_std_banglish + 0.10 * R@1_bangla - 5.0 * N_degrade
    r1 = overall["r5_R1"]
    mrr = overall["r5_MRR"] * 100.0
    r1_banglish = lang_breakdown.get("Standard_Banglish", {}).get("r5_R1", 0.0)
    r1_bangla = lang_breakdown.get("Native_Bangla", {}).get("r5_R1", 0.0)
    degrade_pen = 5.0 * overall["r5_degradations"]

    cei = round(0.35 * r1 + 0.25 * mrr + 0.20 * r1_banglish + 0.10 * r1_bangla - degrade_pen, 2)

    latency_stats = {
        "passage_enc_ms_per_chunk": round((passage_enc_time / len(chunks)) * 1000, 2),
        "query_enc_ms_per_query": round((query_enc_time / len(dev_queries)) * 1000, 2),
        "dense_search_ms_per_query": round(float(np.mean(dense_latencies)) * 1000, 2),
        "rerank_top5_ms_per_query": round(float(np.mean(rerank_latencies)) * 1000, 2),
        "e2e_config_c_ms": round(((query_enc_time / len(dev_queries)) + float(np.mean(dense_latencies)) + float(np.mean(rerank_latencies))) * 1000, 2)
    }

    print(f"Results for {cand_name}:", flush=True)
    print(f"  Top5+Rerank R@1: {overall['r5_R1']}%, MRR: {overall['r5_MRR']}", flush=True)
    print(f"  Banglish R@1: {r1_banglish}%, Bangla R@1: {r1_bangla}%", flush=True)
    print(f"  Degradations: {overall['r5_degradations']}, CEI_DEV: {cei}", flush=True)

    return {
        "candidate_name": cand_name,
        "total_dev_chunks": len(chunks),
        "overall_dev_metrics": overall,
        "language_breakdown": lang_breakdown,
        "composite_engineering_index": cei,
        "latency_stats": latency_stats,
        "query_results": query_results
    }

def main():
    print("Loading Frozen Benchmark for DEV split only...", flush=True)
    with open(BENCHMARK_FILE, 'r', encoding='utf-8') as f:
        bench = json.load(f)
    
    # Filter strictly DEV queries
    dev_queries = [q for q in bench if q["benchmark_split"] == "DEV"]
    print(f"Loaded {len(dev_queries)} DEV queries strictly targeting {DEV_SOURCES}.", flush=True)

    # Load Real Models
    print("Instantiating Real ML Models...", flush=True)
    t0 = time.time()
    e5_model = SentenceTransformer('intfloat/multilingual-e5-small')
    print(f"E5 instantiated in {time.time() - t0:.2f} s", flush=True)

    t0 = time.time()
    reranker = CrossEncoder('BAAI/bge-reranker-v2-m3')
    print(f"BGE Reranker instantiated in {time.time() - t0:.2f} s", flush=True)

    candidate_names = [
        "baseline_fixed_clean",
        "candidate_a_v2_clean",
        "hybrid_600",
        "hybrid_700",
        "hybrid_800"
    ]

    all_dev_results = {}

    for cname in candidate_names:
        cpath = os.path.join(CHUNKS_DIR, cname, "provenance_manifest.json")
        with open(cpath, 'r', encoding='utf-8') as f:
            all_chunks = json.load(f)
        # Filter chunks strictly to DEV sources for pure development evaluation
        dev_chunks = [c for c in all_chunks if c["parent_source_id"] in DEV_SOURCES]
        
        res = evaluate_dev_on_candidate(
            cand_name=cname.upper(),
            chunks=dev_chunks,
            dev_queries=dev_queries,
            e5_model=e5_model,
            reranker=reranker
        )
        all_dev_results[cname.upper()] = res

    # Save DEV Optimization Results
    out_file = os.path.join(EVALS_DIR, "gate_5_9_dev_evaluation.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(all_dev_results, f, indent=2)
    print(f"\nSaved DEV Evaluation Results to {out_file}", flush=True)

    # Rank Candidates by CEI_DEV
    print("\n=======================================================", flush=True)
    print("DEVELOPMENT CANDIDATE RANKINGS (by Composite Engineering Index):", flush=True)
    print("=======================================================", flush=True)
    sorted_cands = sorted(all_dev_results.items(), key=lambda x: x[1]["composite_engineering_index"], reverse=True)
    for rank, (name, data) in enumerate(sorted_cands, 1):
        m = data["overall_dev_metrics"]
        cei = data["composite_engineering_index"]
        print(f"{rank}. {name}: CEI = {cei} | Top-5+Rerank R@1 = {m['r5_R1']}%, MRR = {m['r5_MRR']}, Degradations = {m['r5_degradations']}", flush=True)

if __name__ == "__main__":
    main()
