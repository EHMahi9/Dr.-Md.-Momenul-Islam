"""
Phase 6I: Future Single-Shot Locked Validation Runner.

*** DO NOT EXECUTE THIS SCRIPT YET ***

This runner is prepared but must NOT be run until:
1. The validation benchmark is reviewed and locked
2. Independent approval is obtained
3. All preflight checks pass

The runner will:
1. Verify hashes (candidate, corpus, benchmark)
2. Verify benchmark lock
3. Verify candidate freeze
4. Verify corpus identity
5. Disable tuning hooks
6. Execute exactly once
7. Save complete per-query rankings
8. Save exact configuration hashes
9. Save an immutable integrity report

If preflight fails: ABORT before model inference.
"""

import json
import os
import sys
import re
import time
import hashlib
import numpy as np
from typing import Dict, Any, List

# ==============================================================================
# CONFIGURATION — SET BEFORE EXECUTION
# ==============================================================================

CANDIDATE_CONFIG_PATH = "research/phase_6I_candidate_freeze/frozen_candidate_B_configuration.json"
CORPUS_MANIFEST_PATH = "research/phase_6C/promoted_corpus_manifest.json"
BENCHMARK_PATH = "research/phase_6I_candidate_freeze/independent_validation_benchmark_design.json"
OUTPUT_DIR = "research/phase_6I_candidate_freeze/validation_outputs"

# Expected hashes — MUST be set before execution
EXPECTED_CANDIDATE_SHA256 = "92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A"
EXPECTED_CORPUS_SHA256 = "44D0602F730D6460E6FEFA431BD5C09005B48CE92B47D02832532E5868D4AA58"
EXPECTED_BENCHMARK_SHA256 = "TO_BE_SET_AFTER_BENCHMARK_LOCK"

# ==============================================================================
# SAFETY GUARD — DO NOT REMOVE
# ==============================================================================

EXECUTION_ENABLED = False  # Must be explicitly set to True after approval

def compute_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest().upper()


def run_preflight() -> Dict[str, Any]:
    """Execute all preflight checks. Raises if any fail."""
    from preflight_firewall import run_preflight as firewall_check
    return firewall_check(
        candidate_config_path=CANDIDATE_CONFIG_PATH,
        corpus_manifest_path=CORPUS_MANIFEST_PATH,
        benchmark_path=BENCHMARK_PATH,
        expected_candidate_sha256=EXPECTED_CANDIDATE_SHA256,
        expected_corpus_sha256=EXPECTED_CORPUS_SHA256,
        expected_benchmark_sha256=EXPECTED_BENCHMARK_SHA256,
        evaluation_mode="single_shot",
        allow_development_data=False
    )


def main():
    print("=" * 80)
    print("PHASE 6I: SINGLE-SHOT LOCKED VALIDATION RUNNER")
    print("=" * 80)

    # Safety gate
    if not EXECUTION_ENABLED:
        print("\n*** EXECUTION IS DISABLED ***")
        print("Set EXECUTION_ENABLED = True only after:")
        print("  1. Validation benchmark is reviewed and locked")
        print("  2. Independent approval is obtained")
        print("  3. EXPECTED_BENCHMARK_SHA256 is set to the locked benchmark hash")
        print("\nABORTING — No model inference executed.")
        sys.exit(0)

    # Step 1: Preflight
    print("\n[STEP 1] Running preflight checks...")
    try:
        preflight_report = run_preflight()
        print("  ALL PREFLIGHT CHECKS PASSED.")
    except Exception as e:
        print(f"\n  PREFLIGHT FAILED: {e}")
        print("  ABORTING — No model inference executed.")
        sys.exit(1)

    # Step 2: Load resources
    print("\n[STEP 2] Loading resources...")
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))
    from app.services.retrieval_service import get_retrieval_service, normalize_query_track_a, compute_token_overlap
    from app.core.config import settings

    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    svc = get_retrieval_service()

    # Step 3: Load Candidate B normalization
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

    # Step 4: Execute single-shot evaluation
    print("\n[STEP 4] Executing single-shot evaluation...")
    cases = benchmark["validation_cases"]
    results = []

    for case in cases:
        cid = case["case_id"]
        query = case["query"]
        target = case.get("target_source")
        is_ooc = (target is None)

        norm_query = normalize_candidate_b(query)
        q_emb = svc.dense_model.encode([f"query: {norm_query}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, svc.chunk_embeddings.T)[0]
        top_k_indices = np.argsort(-dense_scores)[:settings.DENSE_K]
        dense_cids = [svc.chunks[idx]["chunk_id"] for idx in top_k_indices]
        dense_scores_list = [float(dense_scores[idx]) for idx in top_k_indices]

        pairs = [[query, svc.chunks_by_id[cid_chunk]["text"]] for cid_chunk in dense_cids]
        raw_rerank = svc.reranker.predict(pairs, batch_size=8, max_length=512)

        adjusted = []
        for cid_chunk, r_s, d_s in zip(dense_cids, raw_rerank, dense_scores_list):
            s = float(r_s)
            if cid_chunk.endswith("-HYB-000"):
                s *= settings.OVERVIEW_DEBIAS_MULTIPLIER
            olap = compute_token_overlap(query, svc.chunks_by_id[cid_chunk]["text"])
            final = s + (settings.LAMBDA_DENSE_FUSION * d_s) + (settings.ALPHA_LEXICAL_OVERLAP * olap)
            adjusted.append(final)

        ranked = np.argsort(-np.array(adjusted))
        top5_idx = ranked[:5]
        top5_cids = [dense_cids[i] for i in top5_idx]
        top5_scores = [round(float(adjusted[i]), 6) for i in top5_idx]
        top5_sids = [c[:11] for c in top5_cids]
        dense_sids = [c[:11] for c in dense_cids]

        if is_ooc:
            results.append({
                "case_id": cid, "lang": case["lang"], "query": query,
                "is_ooc": True, "condition": case["condition"],
                "top5_cids": top5_cids, "top5_scores": top5_scores, "top5_sids": top5_sids,
                "dense_top15_sids": dense_sids, "norm_query": norm_query
            })
        else:
            r5 = target in top5_sids
            r3 = target in top5_sids[:3]
            r1 = target in top5_sids[:1]
            rank = (top5_sids.index(target) + 1) if target in top5_sids else None
            dense_hit = target in dense_sids
            rr = (1.0 / rank) if rank else 0.0
            results.append({
                "case_id": cid, "lang": case["lang"], "query": query,
                "is_ooc": False, "condition": case["condition"],
                "target_source": target, "dense_hit": dense_hit,
                "r5_hit": r5, "r3_hit": r3, "r1_hit": r1,
                "rank": rank, "reciprocal_rank": rr,
                "top5_cids": top5_cids, "top5_scores": top5_scores, "top5_sids": top5_sids,
                "dense_top15_sids": dense_sids, "norm_query": norm_query
            })
        print(f"  [{cid}] {'OOC' if is_ooc else f'rank={rank}'} top1={top5_sids[0]}")

    # Step 5: Compute aggregate metrics
    in_corpus = [r for r in results if not r["is_ooc"]]
    n = len(in_corpus)
    r5 = sum(1 for r in in_corpus if r["r5_hit"]) / n * 100
    r3 = sum(1 for r in in_corpus if r["r3_hit"]) / n * 100
    r1 = sum(1 for r in in_corpus if r["r1_hit"]) / n * 100
    mrr = sum(r["reciprocal_rank"] for r in in_corpus) / n
    dr15 = sum(1 for r in in_corpus if r["dense_hit"]) / n * 100

    # Step 6: Save immutable output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output = {
        "phase": "6I",
        "evaluation_type": "SINGLE_SHOT_LOCKED_VALIDATION",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "preflight_report": preflight_report,
        "hashes": {
            "candidate_sha256": compute_file_sha256(CANDIDATE_CONFIG_PATH),
            "corpus_sha256": compute_file_sha256(CORPUS_MANIFEST_PATH),
            "benchmark_sha256": compute_file_sha256(BENCHMARK_PATH)
        },
        "aggregate_metrics": {
            "in_corpus_N": n,
            "recall_at_5": round(r5, 2),
            "recall_at_3": round(r3, 2),
            "top_1_accuracy": round(r1, 2),
            "mrr_at_5": round(mrr, 4),
            "dense_recall_at_15": round(dr15, 2)
        },
        "per_query_results": results
    }

    out_path = os.path.join(OUTPUT_DIR, "validation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved validation results to: {out_path}")
    print(f"R@5={r5:.1f}% | R@3={r3:.1f}% | Top-1={r1:.1f}% | MRR={mrr:.4f} | Dense R@15={dr15:.1f}%")


if __name__ == "__main__":
    main()
