"""
Gate 5.16 — Phases 2 to 7: Deep Failure Analysis on DEV (N=40)
Extracts detailed diagnostics, per-query profiles, comparative analysis between Gate 5.13 and Gate 5.15 on DEV.
"""

import json
import os
import sys
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

BENCHMARK_FILE = os.path.join(RESEARCH_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
CHUNKS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunk_gold_labels.json")
REPRO_FILE = os.path.join(RESEARCH_DIR, "gate_5_16_reranker_failure_analysis", "reproducibility", "dev_reproduction_verification.json")
GATE_5_14_EVAL_FILE = os.path.join(RESEARCH_DIR, "gate_5_14_reranker_optimization", "evaluations", "gate_5_14_dev_reranker_comparison.json")

DIAG_OUT_FILE = os.path.join(BASE_DIR, "gate_5_16_deep_failure_report.json")
PER_QUERY_DIR = os.path.join(RESEARCH_DIR, "gate_5_16_reranker_failure_analysis", "per_query")
COMP_DIR = os.path.join(RESEARCH_DIR, "gate_5_16_reranker_failure_analysis", "comparisons")

def main():
    print("="*80)
    print("GATE 5.16: DEEP FAILURE ANALYSIS ON DEV (N=40)")
    print("="*80)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunks_by_id = {c["chunk_id"]: c for c in chunks}

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    with open(REPRO_FILE, "r", encoding="utf-8") as f:
        repro_data = json.load(f)
    dev_results = repro_data["dev_queries_results"]

    with open(GATE_5_14_EVAL_FILE, "r", encoding="utf-8") as f:
        strat_data = json.load(f)
    baseline_evals = {q["query_id"]: q for q in strat_data["STRATEGY_1_CONTROL_BASELINE"]["query_evaluations"]}
    debiased_evals = {q["query_id"]: q for q in strat_data["STRATEGY_3_SAME_DOC_OVERVIEW_DEBIASING"]["query_evaluations"]}

    # Phase 2 & 3: Decompose All Failures and Reranker Dynamics
    all_query_profiles = []
    top5_failures = []
    top1_failures = []

    # Failure Taxonomy Tracking
    taxonomy_counts = {
        "GOLD_OUTSIDE_DENSE15": 0,
        "GOLD_IN_DENSE15_BUT_RERANKED_OUT": 0,
        "MULTIPLE_COMPETING_SUBSTANTIVE_CHUNKS": 0,
        "SAME_DOCUMENT_SECTION_CONFUSION": 0,
        "CROSS_DOCUMENT_CONFUSION": 0,
        "BANGLISH_OR_TRANSLITERATION_FAILURE": 0,
        "SUBSTANTIVE_CHUNK_COMPETITION": 0,
        "OVERVIEW_BIAS": 0
    }

    for r in dev_results:
        qid = r["query_id"]
        lang = r["language_category"]
        gold_cids = r["gold_chunk_ids"]
        expected_sid = r["expected_source_id"]
        dense_cids = r["dense_top15_cids"]
        dense_scores = r["dense_top15_scores"]
        rerank_cids = r["rerank_top15_cids"]
        rerank_scores = r["rerank_top15_scores"]
        top5_cids = r["final_top5_cids"]

        dense_r15 = r["dense_r15"]
        dense_rank = r["dense_rank"]
        rerank_rank = r["rerank_rank"]
        in_top5 = r["rerank_r5"]
        is_top1 = r["rerank_r1"]

        # Gold chunk characteristics
        gold_chunk_objs = [chunks_by_id.get(cid) for cid in gold_cids if cid in chunks_by_id]
        gold_headings = [c.get("heading", "") for c in gold_chunk_objs if c]
        gold_lengths = [len(c.get("text", "")) for c in gold_chunk_objs if c]

        # Rank 1 chunk characteristics
        rank1_cid = rerank_cids[0]
        rank1_obj = chunks_by_id.get(rank1_cid, {})
        rank1_sid = rank1_obj.get("parent_source_id", "")
        rank1_heading = rank1_obj.get("heading", "")
        rank1_len = len(rank1_obj.get("text", ""))
        rank1_score = rerank_scores[0]

        # Gold rerank score
        if rerank_rank > 0:
            gold_score = rerank_scores[rerank_rank - 1]
            score_margin = rank1_score - gold_score
        else:
            gold_score = 0.0
            score_margin = 1.0

        same_source_as_gold = (rank1_sid == expected_sid)
        is_overview_rank1 = rank1_cid.endswith("-HYB-000")

        # Determine Primary & Secondary Failure Causes
        primary_cause = "NONE_SUCCESS"
        secondary_cause = "NONE"

        if not in_top5:
            if not dense_r15:
                primary_cause = "GOLD_OUTSIDE_DENSE15"
                taxonomy_counts["GOLD_OUTSIDE_DENSE15"] += 1
                if "Banglish" in lang:
                    secondary_cause = "BANGLISH_OR_TRANSLITERATION_FAILURE"
                    taxonomy_counts["BANGLISH_OR_TRANSLITERATION_FAILURE"] += 1
                elif lang == "Native_Bangla":
                    secondary_cause = "QUERY_REPRESENTATION_FAILURE"
            else:
                primary_cause = "GOLD_IN_DENSE15_BUT_RERANKED_OUT"
                taxonomy_counts["GOLD_IN_DENSE15_BUT_RERANKED_OUT"] += 1
                if same_source_as_gold:
                    if is_overview_rank1:
                        secondary_cause = "OVERVIEW_BIAS"
                        taxonomy_counts["OVERVIEW_BIAS"] += 1
                    else:
                        secondary_cause = "SUBSTANTIVE_CHUNK_COMPETITION"
                        taxonomy_counts["SUBSTANTIVE_CHUNK_COMPETITION"] += 1
                        taxonomy_counts["SAME_DOCUMENT_SECTION_CONFUSION"] += 1
                else:
                    secondary_cause = "CROSS_DOCUMENT_CONFUSION"
                    taxonomy_counts["CROSS_DOCUMENT_CONFUSION"] += 1
        elif not is_top1:
            # Top-1 failure (but present in Top-5)
            if same_source_as_gold:
                if is_overview_rank1:
                    primary_cause = "SAME_DOC_OVERVIEW_COMPETITION"
                else:
                    primary_cause = "SAME_DOC_SUBSTANTIVE_SECTION_COMPETITION"
                    taxonomy_counts["SUBSTANTIVE_CHUNK_COMPETITION"] += 1
                    taxonomy_counts["SAME_DOCUMENT_SECTION_CONFUSION"] += 1
            else:
                primary_cause = "CROSS_DOCUMENT_COMPETITION"
                taxonomy_counts["CROSS_DOCUMENT_CONFUSION"] += 1

        profile = {
            "query_id": qid,
            "raw_query": r["raw_query"],
            "normalized_query": r["normalized_query"],
            "language_category": lang,
            "expected_source_id": expected_sid,
            "gold_chunk_ids": gold_cids,
            "gold_headings": gold_headings,
            "gold_avg_length": float(np.mean(gold_lengths)) if gold_lengths else 0,
            "dense_rank": dense_rank,
            "dense_r15": dense_r15,
            "rerank_rank": rerank_rank,
            "in_top5": in_top5,
            "is_top1": is_top1,
            "gold_rerank_score": gold_score,
            "rank1_chunk_id": rank1_cid,
            "rank1_source_id": rank1_sid,
            "rank1_heading": rank1_heading,
            "rank1_length": rank1_len,
            "rank1_score": rank1_score,
            "score_margin_vs_gold": score_margin,
            "same_source_as_gold": same_source_as_gold,
            "is_rank1_overview": is_overview_rank1,
            "primary_failure_cause": primary_cause,
            "secondary_failure_cause": secondary_cause,
            "top5_cids": top5_cids,
            "top5_details": [
                {
                    "rank": i+1,
                    "chunk_id": cid,
                    "source_id": chunks_by_id.get(cid, {}).get("parent_source_id", ""),
                    "heading": chunks_by_id.get(cid, {}).get("heading", ""),
                    "score": rerank_scores[i],
                    "is_gold": cid in gold_cids
                }
                for i, cid in enumerate(top5_cids)
            ]
        }

        all_query_profiles.append(profile)

        # Write per-query profile to disk
        pq_path = os.path.join(PER_QUERY_DIR, f"{qid}_profile.json")
        with open(pq_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

        if not in_top5:
            top5_failures.append(profile)
        if not is_top1:
            top1_failures.append(profile)

    # Phase 4: Investigate What 0.85x Debiasing Changed on DEV
    debiasing_effect_analysis = []
    for qid, b_eval in baseline_evals.items():
        d_eval = debiased_evals[qid]
        b_rank = b_eval["rank"]
        d_rank = d_eval["rank"]
        b_r1 = b_eval["r1"]
        d_r1 = d_eval["r1"]
        b_r5 = b_eval["r5"]
        d_r5 = d_eval["r5"]

        rank_changed = (b_rank != d_rank)
        gold_moved_up = (b_rank > d_rank) if (b_rank > 0 and d_rank > 0) else False
        gold_moved_down = (b_rank < d_rank) if (b_rank > 0 and d_rank > 0) else False

        # Top 5 context chunk differences
        b_top5 = b_eval["top5_cids"]
        d_top5 = d_eval["top5_cids"]
        context_diff = (b_top5 != d_top5)

        debiasing_effect_analysis.append({
            "query_id": qid,
            "language": b_eval["language_category"],
            "baseline_rank": b_rank,
            "debiased_rank": d_rank,
            "rank_changed": rank_changed,
            "gold_moved_up": gold_moved_up,
            "gold_moved_down": gold_moved_down,
            "context_changed": context_diff,
            "baseline_top5": b_top5,
            "debiased_top5": d_top5
        })

    # Save Comparison Report
    comp_path = os.path.join(COMP_DIR, "gate_5_13_vs_gate_5_15_dev_debiasing_impact.json")
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump(debiasing_effect_analysis, f, indent=2, ensure_ascii=False)

    # Phase 5: Competing Substantive Chunks Analysis
    substantive_comp_queries = [
        p for p in all_query_profiles
        if (not p["is_top1"] or not p["in_top5"]) and p["same_source_as_gold"] and not p["is_rank1_overview"]
    ]

    # Phase 6 & 7: Linguistic Breakdown of Failures
    lang_fail_breakdown = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        l_profiles = [p for p in all_query_profiles if p["language_category"] == lang]
        l_top5_fail = [p for p in l_profiles if not p["in_top5"]]
        l_top1_fail = [p for p in l_profiles if not p["is_top1"]]
        lang_fail_breakdown[lang] = {
            "n_total": len(l_profiles),
            "top5_failures_count": len(l_top5_fail),
            "top5_failures_qids": [p["query_id"] for p in l_top5_fail],
            "top1_failures_count": len(l_top1_fail),
            "primary_causes": {
                c: sum(1 for p in l_profiles if p["primary_failure_cause"] == c)
                for c in set(p["primary_failure_cause"] for p in l_profiles)
            }
        }

    full_report = {
        "gate": "GATE_5.16",
        "timestamp": "2026-08-22T21:05:00+06:00",
        "sample_size": len(dev_results),
        "total_top5_failures": len(top5_failures),
        "top5_failures_list": [
            {
                "query_id": p["query_id"],
                "language": p["language_category"],
                "raw_query": p["raw_query"],
                "gold_chunk_ids": p["gold_chunk_ids"],
                "dense_rank": p["dense_rank"],
                "rerank_rank": p["rerank_rank"],
                "primary_cause": p["primary_failure_cause"],
                "secondary_cause": p["secondary_failure_cause"]
            }
            for p in top5_failures
        ],
        "failure_taxonomy_summary": taxonomy_counts,
        "debiasing_085_effect_summary": {
            "total_queries_with_rank_change": sum(1 for d in debiasing_effect_analysis if d["rank_changed"]),
            "total_queries_with_context_change": sum(1 for d in debiasing_effect_analysis if d["context_changed"]),
            "queries_with_gold_moved_up": [d["query_id"] for d in debiasing_effect_analysis if d["gold_moved_up"]],
            "queries_with_gold_moved_down": [d["query_id"] for d in debiasing_effect_analysis if d["gold_moved_down"]]
        },
        "substantive_chunk_competition": {
            "count": len(substantive_comp_queries),
            "query_ids": [p["query_id"] for p in substantive_comp_queries],
            "case_studies": [
                {
                    "query_id": p["query_id"],
                    "query": p["raw_query"],
                    "gold_heading": p["gold_headings"],
                    "rank1_heading": p["rank1_heading"],
                    "gold_score": p["gold_rerank_score"],
                    "rank1_score": p["rank1_score"],
                    "score_margin": p["score_margin_vs_gold"]
                }
                for p in substantive_comp_queries[:5]
            ]
        },
        "language_failure_breakdown": lang_fail_breakdown
    }

    with open(DIAG_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)

    print(f"\nPhase 2 to 7 Analysis complete!")
    print(f"Total DEV Top-5 Failures: {len(top5_failures)}/40")
    print(f"Total DEV Top-1 Non-Gold: {len(top1_failures)}/40")
    print(f"Saved full diagnostic report to {DIAG_OUT_FILE}")

if __name__ == "__main__":
    main()
