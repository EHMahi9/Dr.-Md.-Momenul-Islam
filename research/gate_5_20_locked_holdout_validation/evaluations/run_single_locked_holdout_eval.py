"""
Gate 5.20 — Phase 2 to 6: Single Locked Holdout Evaluation
Executes the frozen Dual-Mitigation Retrieval Pipeline exactly once on the untouched holdout.
"""

import json
import os
import sys
import time
import re
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

BENCHMARK_FILE = os.path.join(RESEARCH_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
CHUNKS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunk_gold_labels.json")
FROZEN_CONFIG_FILE = os.path.join(RESEARCH_DIR, "gate_5_19_dual_failure_mitigation", "candidate", "frozen_candidate_configuration.json")

HOLDOUT_RESULTS_FILE = os.path.join(BASE_DIR, "gate_5_20_locked_holdout_results.json")
UNSUPPORTED_RESULTS_FILE = os.path.join(BASE_DIR, "gate_5_20_unsupported_query_results.json")
DIAGNOSTICS_FILE = os.path.join(RESEARCH_DIR, "gate_5_20_locked_holdout_validation", "diagnostics", "gate_5_20_failure_decomposition.json")

def load_normalization_rules(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    rules = []
    for r in config["normalization_rules"]:
        rules.append((r["pattern"], r["expansion"]))
    return rules

def normalize_query_text(query: str, rules) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in rules:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        unique_terms = []
        for term in norm_terms:
            if term not in unique_terms:
                unique_terms.append(term)
        return f"{query} ({' '.join(unique_terms)})"
    return query

def main():
    print("="*80)
    print("GATE 5.20 — SINGLE LOCKED HOLDOUT EVALUATION")
    print("="*80)

    # 1. Load Frozen Artifacts
    with open(FROZEN_CONFIG_FILE, "r", encoding="utf-8") as f:
        frozen_config = json.load(f)
    rules = load_normalization_rules(FROZEN_CONFIG_FILE)
    overview_mult = frozen_config["overview_debiasing_multiplier"]
    k_depth = frozen_config["dense_candidate_depth_k"]

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    test_queries = [q for q in benchmark if q.get("benchmark_split") == "TEST_HOLDOUT"]
    unsupported_queries = [q for q in benchmark if q.get("benchmark_split") in ("HARD_NEGATIVE", "OUT_OF_CORPUS")]

    assert len(test_queries) == 40, f"Expected 40 TEST queries, found {len(test_queries)}"
    assert len(unsupported_queries) == 20, f"Expected 20 unsupported queries, found {len(unsupported_queries)}"

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunks_by_id = {c["chunk_id"]: c for c in chunks}

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    # 2. Load Models on CPU
    print("Loading models on CPU...")
    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    # 3. Process 40 Supported Holdout Queries
    print(f"\nEvaluating {len(test_queries)} Supported Locked Holdout Queries...")
    test_candidates = []
    pairs_to_rerank = []

    for q in test_queries:
        qid = q["query_id"]
        raw_q = q["query_text"]
        norm_q = normalize_query_text(raw_q, rules)
        gold = gold_labels[qid]
        acceptable_cids = gold["gold_chunk_ids"]
        expected_sid = q["expected_source_id"]

        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:k_depth]
        top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
        top15_scores = [float(dense_scores[idx]) for idx in top15_indices]

        all_dense_indices = np.argsort(-dense_scores)
        all_dense_cids = [chunks[idx]["chunk_id"] for idx in all_dense_indices]
        dense_rank = min([all_dense_cids.index(cid) + 1 for cid in acceptable_cids if cid in all_dense_cids])
        dense_hit = (dense_rank <= k_depth)

        test_candidates.append({
            "query_id": qid,
            "language_category": q["language_category"],
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "expected_source_id": expected_sid,
            "gold_chunk_ids": acceptable_cids,
            "dense_rank": dense_rank,
            "dense_hit_r15": dense_hit,
            "top15_indices": top15_indices,
            "dense_top15_cids": top15_cids,
            "dense_top15_scores": top15_scores
        })

        for idx in top15_indices:
            pairs_to_rerank.append((norm_q, chunks[idx]["text"]))

    # 4. Cross-Encoder Inference for Supported Queries
    print(f"Reranking {len(pairs_to_rerank)} pairs with bge-reranker-v2-m3...")
    t0 = time.time()
    rerank_scores_flat = reranker.predict(pairs_to_rerank)
    latency_supported = time.time() - t0
    print(f"Supported queries rerank completed in {latency_supported:.2f}s ({latency_supported/40:.2f}s/query)")

    # 5. Evaluate Supported Queries Rankings & Metrics
    supported_query_evals = []
    offset = 0
    availability_counts = {
        "TOP1_CORRECT": 0,
        "TOP1_WRONG_BUT_TOP3_HAS_GOLD": 0,
        "TOP3_WRONG_BUT_TOP5_HAS_GOLD": 0,
        "GOLD_ABSENT_FROM_TOP5": 0
    }

    for tc in test_candidates:
        qid = tc["query_id"]
        acceptable_cids = tc["gold_chunk_ids"]
        expected_sid = tc["expected_source_id"]
        dense_cids = tc["dense_top15_cids"]
        n_c = len(dense_cids)

        raw_scores = [float(s) for s in rerank_scores_flat[offset : offset + n_c]]
        offset += n_c

        # Apply Overview Debiasing (0.85x)
        adj_scores = []
        for i, cid in enumerate(dense_cids):
            s = raw_scores[i]
            if cid.endswith("-HYB-000"):
                adj_scores.append(s * overview_mult)
            else:
                adj_scores.append(s)

        adj_scores = np.array(adj_scores)
        rerank_order = np.argsort(-adj_scores)

        rerank_cids = [dense_cids[i] for i in rerank_order]
        rerank_scores = [float(adj_scores[i]) for i in rerank_order]

        top5_cids = rerank_cids[:5]
        top5_scores = rerank_scores[:5]

        # Chunk-level hits
        hits_5 = [cid in acceptable_cids for cid in top5_cids]
        r1 = hits_5[0]
        r3 = any(hits_5[:3])
        r5 = any(hits_5[:5])

        all_hits = [cid in acceptable_cids for cid in rerank_cids]
        final_rank = (all_hits.index(True) + 1) if any(all_hits) else 0

        # Source-level hits
        top5_sids = [chunks_by_id.get(cid, {}).get("parent_source_id") for cid in top5_cids]
        src_r1 = (top5_sids[0] == expected_sid)
        src_r5 = (expected_sid in top5_sids)

        # Availability category
        if r1:
            avail_cat = "TOP1_CORRECT"
            availability_counts["TOP1_CORRECT"] += 1
        elif r3:
            avail_cat = "TOP1_WRONG_BUT_TOP3_HAS_GOLD"
            availability_counts["TOP1_WRONG_BUT_TOP3_HAS_GOLD"] += 1
        elif r5:
            avail_cat = "TOP3_WRONG_BUT_TOP5_HAS_GOLD"
            availability_counts["TOP3_WRONG_BUT_TOP5_HAS_GOLD"] += 1
        else:
            avail_cat = "GOLD_ABSENT_FROM_TOP5"
            availability_counts["GOLD_ABSENT_FROM_TOP5"] += 1

        supported_query_evals.append({
            "query_id": qid,
            "language_category": tc["language_category"],
            "raw_query": tc["raw_query"],
            "normalized_query": tc["normalized_query"],
            "expected_source_id": expected_sid,
            "gold_chunk_ids": acceptable_cids,
            "dense_rank": tc["dense_rank"],
            "dense_hit_r15": tc["dense_hit_r15"],
            "final_rerank_rank": final_rank,
            "r1": r1,
            "r3": r3,
            "r5": r5,
            "source_r1": src_r1,
            "source_r5": src_r5,
            "availability_category": avail_cat,
            "top1_chunk_id": rerank_cids[0],
            "top1_score": rerank_scores[0],
            "gold_score": rerank_scores[final_rank - 1] if final_rank > 0 else 0.0,
            "final_top5_cids": top5_cids,
            "final_top5_scores": top5_scores,
            "final_top5_sources": top5_sids
        })

    # Summary Metrics Calculation
    n_test = len(supported_query_evals)
    dense_r15_cnt = sum(1 for q in supported_query_evals if q["dense_hit_r15"])
    chunk_r1_cnt = sum(1 for q in supported_query_evals if q["r1"])
    chunk_r3_cnt = sum(1 for q in supported_query_evals if q["r3"])
    chunk_r5_cnt = sum(1 for q in supported_query_evals if q["r5"])
    src_r1_cnt = sum(1 for q in supported_query_evals if q["source_r1"])
    src_r5_cnt = sum(1 for q in supported_query_evals if q["source_r5"])
    chunk_mrr = sum(1.0 / q["final_rerank_rank"] for q in supported_query_evals if q["final_rerank_rank"] > 0) / n_test

    # Language Breakdown
    lang_breakdown = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        subs = [q for q in supported_query_evals if q["language_category"] == lang]
        ln = len(subs)
        l_dense_r15 = sum(1 for q in subs if q["dense_hit_r15"])
        l_r1 = sum(1 for q in subs if q["r1"])
        l_r3 = sum(1 for q in subs if q["r3"])
        l_r5 = sum(1 for q in subs if q["r5"])
        l_mrr = sum(1.0 / q["final_rerank_rank"] for q in subs if q["final_rerank_rank"] > 0) / ln
        lang_breakdown[lang] = {
            "n": ln,
            "dense_r15_count": f"{l_dense_r15}/{ln}",
            "dense_r15_pct": round(l_dense_r15 / ln * 100, 2),
            "chunk_r1_count": f"{l_r1}/{ln}",
            "chunk_r1_pct": round(l_r1 / ln * 100, 2),
            "chunk_r3_count": f"{l_r3}/{ln}",
            "chunk_r3_pct": round(l_r3 / ln * 100, 2),
            "chunk_r5_count": f"{l_r5}/{ln}",
            "chunk_r5_pct": round(l_r5 / ln * 100, 2),
            "mrr": round(l_mrr, 4)
        }

    # 6. Failure Decomposition on Failed Holdout Queries
    failed_queries = [q for q in supported_query_evals if not q["r5"]]
    failure_decomposition = []
    dense_miss_cnt = 0
    rerank_miss_cnt = 0

    for fq in failed_queries:
        qid = fq["query_id"]
        dense_rank = fq["dense_rank"]
        rerank_rank = fq["final_rerank_rank"]
        top1_cid = fq["top1_chunk_id"]
        top1_chunk = chunks_by_id.get(top1_cid, {})
        top1_sid = top1_chunk.get("parent_source_id")

        same_doc = (top1_sid == fq["expected_source_id"])
        is_overview = top1_cid.endswith("-HYB-000")
        is_substantive = not is_overview

        if dense_rank > k_depth or dense_rank == 0:
            failure_type = "GOLD_OUTSIDE_DENSE15"
            dense_miss_cnt += 1
        else:
            failure_type = "GOLD_IN_DENSE15_BUT_RERANKED_OUT"
            rerank_miss_cnt += 1

        failure_decomposition.append({
            "query_id": qid,
            "language_category": fq["language_category"],
            "raw_query": fq["raw_query"],
            "gold_chunk_ids": fq["gold_chunk_ids"],
            "expected_source_id": fq["expected_source_id"],
            "dense_rank": dense_rank,
            "final_rerank_rank": rerank_rank,
            "failure_type": failure_type,
            "competing_top1_chunk_id": top1_cid,
            "competing_top1_source_id": top1_sid,
            "competing_top1_score": fq["top1_score"],
            "competitor_is_same_document": same_doc,
            "competitor_is_overview": is_overview,
            "competitor_is_substantive_section": is_substantive
        })

    # 7. Evaluate Unsupported Queries (12 Hard Negatives + 8 Out-of-Corpus)
    print(f"\nEvaluating {len(unsupported_queries)} Unsupported Queries for safety baseline...")
    unsupported_candidates = []
    unsupported_pairs = []

    for q in unsupported_queries:
        qid = q["query_id"]
        raw_q = q["query_text"]
        norm_q = normalize_query_text(raw_q, rules)

        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:k_depth]
        top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]

        unsupported_candidates.append((qid, raw_q, norm_q, q.get("benchmark_split"), top15_cids))
        for idx in top15_indices:
            unsupported_pairs.append((norm_q, chunks[idx]["text"]))

    unsupported_scores_flat = reranker.predict(unsupported_pairs)
    unsupported_evals = []
    offset = 0
    all_unsupported_max_scores = []

    for qid, raw_q, norm_q, split, top15_cids in unsupported_candidates:
        raw_scores = [float(s) for s in unsupported_scores_flat[offset : offset + k_depth]]
        offset += k_depth

        adj_scores = [s * overview_mult if cid.endswith("-HYB-000") else s for cid, s in zip(top15_cids, raw_scores)]
        max_s = max(adj_scores)
        mean_s = float(np.mean(adj_scores))
        all_unsupported_max_scores.append(max_s)

        unsupported_evals.append({
            "query_id": qid,
            "benchmark_split": split,
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "max_rerank_score": round(max_s, 4),
            "mean_rerank_score": round(mean_s, 4),
            "score_min": round(float(np.min(adj_scores)), 4),
            "score_max": round(max_s, 4),
            "top1_chunk_id": top15_cids[np.argmax(adj_scores)]
        })

    max_unsupported_score = float(np.max(all_unsupported_max_scores))
    mean_unsupported_score = float(np.mean(all_unsupported_max_scores))
    min_unsupported_score = float(np.min(all_unsupported_max_scores))

    # 8. Save All Evaluation Output Artifacts
    holdout_results = {
        "gate": "GATE_5.20",
        "timestamp": "2026-08-28T19:03:00+06:00",
        "configuration_sha256": frozen_config["configuration_sha256"],
        "n_supported_queries": n_test,
        "primary_metrics": {
            "dense_candidate_recall_at_15": f"{dense_r15_cnt}/{n_test} ({round(dense_r15_cnt/n_test*100, 2)}%)",
            "chunk_recall_at_1": f"{chunk_r1_cnt}/{n_test} ({round(chunk_r1_cnt/n_test*100, 2)}%)",
            "chunk_recall_at_3": f"{chunk_r3_cnt}/{n_test} ({round(chunk_r3_cnt/n_test*100, 2)}%)",
            "chunk_recall_at_5 (PRIMARY)": f"{chunk_r5_cnt}/{n_test} ({round(chunk_r5_cnt/n_test*100, 2)}%)",
            "chunk_mrr": round(chunk_mrr, 4)
        },
        "secondary_source_metrics": {
            "source_recall_at_1": f"{src_r1_cnt}/{n_test} ({round(src_r1_cnt/n_test*100, 2)}%)",
            "source_recall_at_5": f"{src_r5_cnt}/{n_test} ({round(src_r5_cnt/n_test*100, 2)}%)"
        },
        "evidence_availability_categories": {
            "TOP1_CORRECT": f"{availability_counts['TOP1_CORRECT']}/{n_test} ({round(availability_counts['TOP1_CORRECT']/n_test*100, 2)}%)",
            "TOP1_WRONG_BUT_TOP3_HAS_GOLD": f"{availability_counts['TOP1_WRONG_BUT_TOP3_HAS_GOLD']}/{n_test} ({round(availability_counts['TOP1_WRONG_BUT_TOP3_HAS_GOLD']/n_test*100, 2)}%)",
            "TOP3_WRONG_BUT_TOP5_HAS_GOLD": f"{availability_counts['TOP3_WRONG_BUT_TOP5_HAS_GOLD']}/{n_test} ({round(availability_counts['TOP3_WRONG_BUT_TOP5_HAS_GOLD']/n_test*100, 2)}%)",
            "GOLD_ABSENT_FROM_TOP5": f"{availability_counts['GOLD_ABSENT_FROM_TOP5']}/{n_test} ({round(availability_counts['GOLD_ABSENT_FROM_TOP5']/n_test*100, 2)}%)"
        },
        "language_breakdown": lang_breakdown,
        "query_evaluations": supported_query_evals
    }

    with open(HOLDOUT_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(holdout_results, f, indent=2, ensure_ascii=False)

    diagnostics_data = {
        "gate": "GATE_5.20",
        "total_failures_count": len(failed_queries),
        "failures_percentage": round(len(failed_queries) / n_test * 100, 2),
        "failure_taxonomy_counts": {
            "GOLD_OUTSIDE_DENSE15": dense_miss_cnt,
            "GOLD_IN_DENSE15_BUT_RERANKED_OUT": rerank_miss_cnt
        },
        "failure_decomposition": failure_decomposition
    }

    with open(DIAGNOSTICS_FILE, "w", encoding="utf-8") as f:
        json.dump(diagnostics_data, f, indent=2, ensure_ascii=False)

    unsupported_results = {
        "gate": "GATE_5.20",
        "n_unsupported_queries": len(unsupported_queries),
        "score_statistics": {
            "max_score": round(max_unsupported_score, 4),
            "mean_score": round(mean_unsupported_score, 4),
            "min_score": round(min_unsupported_score, 4),
            "score_range": f"[{round(min_unsupported_score, 4)}, {round(max_unsupported_score, 4)}]"
        },
        "observation": "Observed score separation in this benchmark. Production rejection threshold is UNKNOWN.",
        "evaluations": unsupported_evals
    }

    with open(UNSUPPORTED_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(unsupported_results, f, indent=2, ensure_ascii=False)

    print("\n" + "="*80)
    print("GATE 5.20 SINGLE LOCKED HOLDOUT EVALUATION SUMMARY")
    print("="*80)
    print(f"Dense Candidate Recall@15: {holdout_results['primary_metrics']['dense_candidate_recall_at_15']}")
    print(f"Final Chunk Recall@1:      {holdout_results['primary_metrics']['chunk_recall_at_1']}")
    print(f"Final Chunk Recall@3:      {holdout_results['primary_metrics']['chunk_recall_at_3']}")
    print(f"Final Chunk Recall@5:      {holdout_results['primary_metrics']['chunk_recall_at_5 (PRIMARY)']}")
    print(f"Final Chunk MRR:           {holdout_results['primary_metrics']['chunk_mrr']}")
    print(f"Source Recall@1:           {holdout_results['secondary_source_metrics']['source_recall_at_1']}")
    print(f"Source Recall@5:           {holdout_results['secondary_source_metrics']['source_recall_at_5']}")
    print(f"GOLD_ABSENT_FROM_TOP5:     {holdout_results['evidence_availability_categories']['GOLD_ABSENT_FROM_TOP5']}")
    print(f"Unsupported Max Score:     {unsupported_results['score_statistics']['max_score']}")

if __name__ == "__main__":
    main()
