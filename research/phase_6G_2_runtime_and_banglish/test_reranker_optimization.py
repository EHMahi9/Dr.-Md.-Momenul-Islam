"""
Semantic Equivalence and Performance Benchmark for BGE Reranker Optimizations.
Tests:
1. Baseline ce.predict(pairs)
2. Opt 1: ce.predict(pairs, batch_size=8, max_length=512)
3. Opt 2: with torch.inference_mode(): ce.predict(pairs, batch_size=8, max_length=512)

Strict Rule:
If any query has a score delta > 1e-5 or different Top-1/Top-5 rankings, REJECT optimization.
"""

import time
import json
import os
import sys
import numpy as np
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.services.retrieval_service import get_retrieval_service
from app.core.config import settings

def run_semantic_and_perf_test():
    print("="*80)
    print("BGE RERANKER OPTIMIZATION & SEMANTIC EQUIVALENCE TEST")
    print("="*80)
    
    svc = get_retrieval_service()
    ce = svc.reranker
    
    # 6 representative development test queries (English, Bangla, Banglish)
    test_queries = [
        "how to treat minor burns with cool water",
        "clean cut or graze with clean water and dressing",
        "বাচ্চার জ্বর হলে করণীয় কি?",
        "কাটা বা ছড়ে যাওয়ার প্রাথমিক চিকিৎসা কি?",
        "nak diye rokt porle ki korbo?",
        "bacchar jor hole ki paracetamol dewa jabe?"
    ]
    
    query_results = []
    
    total_baseline_ms = 0.0
    total_opt1_ms = 0.0
    total_opt2_ms = 0.0
    
    max_delta_global = 0.0
    rankings_identical = True
    
    for idx, q in enumerate(test_queries, start=1):
        print(f"\nQuery {idx}/{len(test_queries)}: '{q}'")
        
        # Dense candidate retrieval
        norm_q = q
        q_emb = svc.dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, svc.chunk_embeddings.T)[0]
        top_k_indices = np.argsort(-dense_scores)[:settings.DENSE_K]
        candidate_cids = [svc.chunks[i]["chunk_id"] for i in top_k_indices]
        pairs = [[q, svc.chunks_by_id[cid]["text"]] for cid in candidate_cids]
        
        # 1. Baseline
        t0 = time.perf_counter()
        scores_base = ce.predict(pairs)
        t_base_ms = round((time.perf_counter() - t0) * 1000, 2)
        total_baseline_ms += t_base_ms
        
        # 2. Opt 1 (batch_size=8, max_length=512)
        t1 = time.perf_counter()
        scores_opt1 = ce.predict(pairs, batch_size=8, max_length=512)
        t_opt1_ms = round((time.perf_counter() - t1) * 1000, 2)
        total_opt1_ms += t_opt1_ms
        
        # 3. Opt 2 (inference_mode + batch_size=8 + max_length=512)
        t2 = time.perf_counter()
        with torch.inference_mode():
            scores_opt2 = ce.predict(pairs, batch_size=8, max_length=512)
        t_opt2_ms = round((time.perf_counter() - t2) * 1000, 2)
        total_opt2_ms += t_opt2_ms
        
        # Compare deltas
        arr_base = np.array(scores_base)
        arr_opt1 = np.array(scores_opt1)
        arr_opt2 = np.array(scores_opt2)
        
        delta_1 = float(np.max(np.abs(arr_base - arr_opt1)))
        delta_2 = float(np.max(np.abs(arr_base - arr_opt2)))
        max_delta = max(delta_1, delta_2)
        max_delta_global = max(max_delta_global, max_delta)
        
        order_base = list(np.argsort(-arr_base)[:5])
        order_opt1 = list(np.argsort(-arr_opt1)[:5])
        order_opt2 = list(np.argsort(-arr_opt2)[:5])
        
        cids_base = [candidate_cids[i] for i in order_base]
        cids_opt1 = [candidate_cids[i] for i in order_opt1]
        cids_opt2 = [candidate_cids[i] for i in order_opt2]
        
        match_1 = (cids_base == cids_opt1)
        match_2 = (cids_base == cids_opt2)
        if not (match_1 and match_2):
            rankings_identical = False
            
        print(f"  - Baseline: {t_base_ms} ms | Top-1: {cids_base[0]}")
        print(f"  - Opt 1 (bs=8, max_len=512): {t_opt1_ms} ms | Delta: {delta_1:.2e} | Top-1: {cids_opt1[0]} (Match: {match_1})")
        print(f"  - Opt 2 (inf_mode+bs=8): {t_opt2_ms} ms | Delta: {delta_2:.2e} | Top-1: {cids_opt2[0]} (Match: {match_2})")
        
        query_results.append({
            "query": q,
            "latency_baseline_ms": t_base_ms,
            "latency_opt1_ms": t_opt1_ms,
            "latency_opt2_ms": t_opt2_ms,
            "max_score_delta": max_delta,
            "top5_base": cids_base,
            "top5_opt1": cids_opt1,
            "top5_opt2": cids_opt2,
            "top5_exact_match": match_1 and match_2
        })
        
    print("\n" + "="*80)
    print("OVERALL BENCHMARK SUMMARY")
    print("="*80)
    avg_base = round(total_baseline_ms / len(test_queries), 2)
    avg_opt1 = round(total_opt1_ms / len(test_queries), 2)
    avg_opt2 = round(total_opt2_ms / len(test_queries), 2)
    
    print(f"Average Baseline Latency: {avg_base} ms")
    print(f"Average Opt 1 Latency:    {avg_opt1} ms ({round((avg_base - avg_opt1)/avg_base * 100, 1)}% reduction)")
    print(f"Average Opt 2 Latency:    {avg_opt2} ms ({round((avg_base - avg_opt2)/avg_base * 100, 1)}% reduction)")
    print(f"Global Max Score Delta:   {max_delta_global:.2e}")
    print(f"All Top-5 Rankings Identical: {rankings_identical}")
    
    summary = {
        "queries_tested": len(test_queries),
        "rankings_100_percent_identical": rankings_identical,
        "global_max_score_delta": max_delta_global,
        "average_baseline_ms": avg_base,
        "average_opt1_ms": avg_opt1,
        "average_opt2_ms": avg_opt2,
        "improvement_opt1_pct": round((avg_base - avg_opt1)/avg_base * 100, 1),
        "improvement_opt2_pct": round((avg_base - avg_opt2)/avg_base * 100, 1),
        "query_details": query_results
    }
    
    out_path = "research/phase_6G_2_runtime_and_banglish/outputs/reranker_optimization_benchmark.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"Saved benchmark results to: {out_path}")
    return summary

if __name__ == "__main__":
    run_semantic_and_perf_test()
