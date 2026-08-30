"""
Phase 6I: Candidate B Reproducibility Test.
Runs Candidate B twice on the SAME corrected development challenge dataset
and verifies deterministic output (normalized queries, dense candidates,
reranked IDs, final Top-5 IDs, and scores within documented tolerance).
"""
import json
import os
import sys
import re
import time
import hashlib
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.services.retrieval_service import get_retrieval_service, normalize_query_track_a, compute_token_overlap
from app.core.config import settings

# Candidate B normalization (exact copy from run_banglish_experiment.py L74-L112)
def normalize_candidate_b(query: str) -> str:
    q = normalize_query_track_a(query)
    lower_q = q.lower()
    
    if re.search(r'\b(nak|nose)\b', lower_q) and re.search(r'\b(rokt|rokto|bleeding|porche|pora)\b', lower_q):
        lower_q += " nosebleed epistaxis pinch soft part of nose lean forward bleed from nose"
    elif re.search(r'\b(kete|chole|keteche|injury|khoto|wound)\b', lower_q) and re.search(r'\b(rokt|rokto|bleeding|blood)\b', lower_q):
        lower_q += " cuts and grazes cut wound bleeding pressure clean dressing bandage stop bleeding"
    
    if re.search(r'\b(buk|chest)\b', lower_q) and re.search(r'\b(jala|pora|betha|burning|pain)\b', lower_q):
        lower_q += " heartburn acid reflux indigestion chest burning sensation antacids stomach acid"
    elif re.search(r'\b(agune|gorom pani|tel|chayer pani|hot water|fire|steam)\b', lower_q) and re.search(r'\b(pora|pure|burn|scald)\b', lower_q):
        lower_q += " burns and scalds cool tap water 20 minutes remove jewellery cling film thermal burn"
    
    if re.search(r'\b(baccha|bacchar|shishu|baby|child|children)\b', lower_q) and re.search(r'\b(jor|fever|tapmatra|temperature)\b', lower_q):
        lower_q += " high temperature fever in children paracetamol plenty of fluids signs of serious illness"
    
    if re.search(r'\b(poka|pokar|insect|wasp|bee)\b', lower_q) and re.search(r'\b(kamor|khel|sting|bite|fule)\b', lower_q):
        lower_q += " insect bites and stings redness swelling itching remove sting cold compress"
    
    if re.search(r'\b(matha|head)\b', lower_q) and re.search(r'\b(ekpashe|unilateral|one side|throbbing)\b', lower_q):
        lower_q += " migraine severe throbbing headache dark quiet room nausea visual disturbance"
    
    return lower_q.strip()


def execute_retrieval_with_normalizer(svc, query, normalizer_fn, top_k=5):
    norm_query = normalizer_fn(query)
    q_emb = svc.dense_model.encode([f"query: {norm_query}"], normalize_embeddings=True)
    dense_scores = np.dot(q_emb, svc.chunk_embeddings.T)[0]
    top_k_indices = np.argsort(-dense_scores)[:settings.DENSE_K]
    candidate_cids = [svc.chunks[idx]["chunk_id"] for idx in top_k_indices]
    candidate_dense_scores = [float(dense_scores[idx]) for idx in top_k_indices]
    
    pairs = [[query, svc.chunks_by_id[cid]["text"]] for cid in candidate_cids]
    raw_rerank_scores = svc.reranker.predict(pairs, batch_size=8, max_length=512)
    
    adjusted_scores = []
    for cid, r_score, d_score in zip(candidate_cids, raw_rerank_scores, candidate_dense_scores):
        score = float(r_score)
        if cid.endswith("-HYB-000"):
            score *= settings.OVERVIEW_DEBIAS_MULTIPLIER
        overlap = compute_token_overlap(query, svc.chunks_by_id[cid]["text"])
        final_score = score + (settings.LAMBDA_DENSE_FUSION * d_score) + (settings.ALPHA_LEXICAL_OVERLAP * overlap)
        adjusted_scores.append(final_score)
    
    ranked_order = np.argsort(-np.array(adjusted_scores))
    final_top_indices = ranked_order[:top_k]
    
    return {
        "norm_query": norm_query,
        "dense_top15_cids": candidate_cids,
        "dense_top15_scores": [round(s, 6) for s in candidate_dense_scores],
        "top5_cids": [candidate_cids[i] for i in final_top_indices],
        "top5_scores": [round(float(adjusted_scores[i]), 6) for i in final_top_indices]
    }


def main():
    print("=" * 80)
    print("PHASE 6I: CANDIDATE B REPRODUCIBILITY TEST")
    print("=" * 80)
    
    # Load challenge queries
    ds_path = "research/phase_6H_1_benchmark_integrity/corrected_banglish_challenge_dataset.json"
    with open(ds_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
    queries = [(c["case_id"], c["query"]) for c in cases]
    
    svc = get_retrieval_service()
    
    SCORE_TOLERANCE = 1e-5
    
    # Run 1
    print("\n--- Run 1 ---")
    run1_results = {}
    for cid, query in queries:
        res = execute_retrieval_with_normalizer(svc, query, normalize_candidate_b, top_k=5)
        run1_results[cid] = res
        print(f"  [{cid}] top1={res['top5_cids'][0][:15]}...")
    
    # Run 2
    print("\n--- Run 2 ---")
    run2_results = {}
    for cid, query in queries:
        res = execute_retrieval_with_normalizer(svc, query, normalize_candidate_b, top_k=5)
        run2_results[cid] = res
        print(f"  [{cid}] top1={res['top5_cids'][0][:15]}...")
    
    # Compare
    print("\n--- Reproducibility Comparison ---")
    all_pass = True
    case_reports = []
    
    for cid, query in queries:
        r1 = run1_results[cid]
        r2 = run2_results[cid]
        
        norm_match = (r1["norm_query"] == r2["norm_query"])
        dense_id_match = (r1["dense_top15_cids"] == r2["dense_top15_cids"])
        top5_id_match = (r1["top5_cids"] == r2["top5_cids"])
        
        max_score_delta = 0.0
        for s1, s2 in zip(r1["top5_scores"], r2["top5_scores"]):
            max_score_delta = max(max_score_delta, abs(s1 - s2))
        
        score_match = (max_score_delta <= SCORE_TOLERANCE)
        case_pass = norm_match and dense_id_match and top5_id_match and score_match
        
        if not case_pass:
            all_pass = False
        
        status = "PASS" if case_pass else "FAIL"
        print(f"  [{cid}] {status} | norm={norm_match} | dense_ids={dense_id_match} | top5_ids={top5_id_match} | max_score_delta={max_score_delta:.2e}")
        
        case_reports.append({
            "case_id": cid,
            "query": query,
            "pass": case_pass,
            "norm_query_match": norm_match,
            "dense_top15_id_match": dense_id_match,
            "top5_id_match": top5_id_match,
            "max_score_delta": max_score_delta,
            "score_within_tolerance": score_match,
            "run1_top5_cids": r1["top5_cids"],
            "run2_top5_cids": r2["top5_cids"],
            "run1_top5_scores": r1["top5_scores"],
            "run2_top5_scores": r2["top5_scores"]
        })
    
    overall_verdict = "ALL_CASES_REPRODUCIBLE" if all_pass else "REPRODUCIBILITY_FAILURE_DETECTED"
    print(f"\nOVERALL VERDICT: {overall_verdict}")
    
    report = {
        "phase": "6I",
        "test": "Candidate B Reproducibility",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidate": "Candidate B (Context-Aware Compound Disambiguation)",
        "dataset": ds_path,
        "score_tolerance": SCORE_TOLERANCE,
        "overall_verdict": overall_verdict,
        "total_cases": len(case_reports),
        "passed_cases": sum(1 for c in case_reports if c["pass"]),
        "failed_cases": sum(1 for c in case_reports if not c["pass"]),
        "case_details": case_reports
    }
    
    out_path = "research/phase_6I_candidate_freeze/reproducibility_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Saved report to: {out_path}")


if __name__ == "__main__":
    main()
