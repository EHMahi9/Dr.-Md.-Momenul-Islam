"""
Gate 5.10 — Phase 2 & 3: DEV Failure Taxonomy and Diagnostic Analysis
Classifies each of the 40 DEV queries and determines the exact rank of the gold chunk.
"""

import json
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASELINE_FILE = os.path.join(BASE_DIR, "..", "baseline", "dev_baseline_reproduced.json")
OUT_FILE = os.path.join(BASE_DIR, "dev_failure_taxonomy.json")

def main():
    if not os.path.exists(BASELINE_FILE):
        print(f"Waiting for {BASELINE_FILE}...")
        return

    with open(BASELINE_FILE, "r", encoding="utf-8") as f:
        dev_results = json.load(f)

    taxonomy = {
        "GOLD_TOP1": [],
        "GOLD_TOPK_NOT_TOP1": [],
        "GOLD_NOT_IN_DENSE_TOP5": [],
        "GOLD_PRESENT_BUT_RERANK_DEMOTED": [],
        "expanded_pool_depths": {
            "top5": 0,
            "top10": 0,
            "top15": 0,
            "top20": 0,
            "top30": 0,
            "outside_top30": 0
        }
    }

    query_classifications = []

    for q in dev_results:
        qid = q["query_id"]
        q_text = q["query_text"]
        lang = q["language_category"]
        gold_cids = q["acceptable_gold_chunks"]
        dense_top5 = q["dense_top5_chunk_ids"]
        r5_top5 = q["r5_top5_chunk_ids"]
        all_ranked = q["all_ranked_chunk_ids"]

        # Find gold ranks in full dense ranking
        dense_gold_ranks = [all_ranked.index(cid) + 1 for cid in gold_cids if cid in all_ranked]
        min_dense_rank = min(dense_gold_ranks) if dense_gold_ranks else 999

        # Check where it appears in expanded depths
        if min_dense_rank <= 5:
            taxonomy["expanded_pool_depths"]["top5"] += 1
        elif min_dense_rank <= 10:
            taxonomy["expanded_pool_depths"]["top10"] += 1
        elif min_dense_rank <= 15:
            taxonomy["expanded_pool_depths"]["top15"] += 1
        elif min_dense_rank <= 20:
            taxonomy["expanded_pool_depths"]["top20"] += 1
        elif min_dense_rank <= 30:
            taxonomy["expanded_pool_depths"]["top30"] += 1
        else:
            taxonomy["expanded_pool_depths"]["outside_top30"] += 1

        # Rerank rank
        r5_gold_ranks = [r5_top5.index(cid) + 1 for cid in gold_cids if cid in r5_top5]
        min_r5_rank = min(r5_gold_ranks) if r5_gold_ranks else 0

        # Classify
        if min_r5_rank == 1:
            cat = "GOLD_TOP1"
            taxonomy["GOLD_TOP1"].append(qid)
        elif min_r5_rank > 1:
            cat = "GOLD_TOPK_NOT_TOP1"
            taxonomy["GOLD_TOPK_NOT_TOP1"].append({"query_id": qid, "rerank_rank": min_r5_rank})
            if min_dense_rank == 1:
                taxonomy["GOLD_PRESENT_BUT_RERANK_DEMOTED"].append({"query_id": qid, "dense_rank": 1, "rerank_rank": min_r5_rank})
        else:
            cat = "GOLD_NOT_IN_DENSE_TOP5"
            taxonomy["GOLD_NOT_IN_DENSE_TOP5"].append({"query_id": qid, "min_dense_rank": min_dense_rank})

        query_classifications.append({
            "query_id": qid,
            "query_text": q_text,
            "language": lang,
            "acceptable_gold_chunks": gold_cids,
            "min_dense_rank": min_dense_rank,
            "min_r5_rank": min_r5_rank,
            "classification": cat,
            "dense_top5": dense_top5,
            "r5_top5": r5_top5
        })

    summary = {
        "total_dev_queries": len(dev_results),
        "gold_top1_count": len(taxonomy["GOLD_TOP1"]),
        "gold_topk_not_top1_count": len(taxonomy["GOLD_TOPK_NOT_TOP1"]),
        "gold_not_in_dense_top5_count": len(taxonomy["GOLD_NOT_IN_DENSE_TOP5"]),
        "rerank_demotions_count": len(taxonomy["GOLD_PRESENT_BUT_RERANK_DEMOTED"]),
        "expanded_pool_cumulative_dense_recall": {
            "Top-5": f"{taxonomy['expanded_pool_depths']['top5']}/40 ({taxonomy['expanded_pool_depths']['top5']/40*100:.2f}%)",
            "Top-10": f"{(taxonomy['expanded_pool_depths']['top5'] + taxonomy['expanded_pool_depths']['top10'])}/40 ({(taxonomy['expanded_pool_depths']['top5'] + taxonomy['expanded_pool_depths']['top10'])/40*100:.2f}%)",
            "Top-15": f"{(taxonomy['expanded_pool_depths']['top5'] + taxonomy['expanded_pool_depths']['top10'] + taxonomy['expanded_pool_depths']['top15'])}/40 ({(taxonomy['expanded_pool_depths']['top5'] + taxonomy['expanded_pool_depths']['top10'] + taxonomy['expanded_pool_depths']['top15'])/40*100:.2f}%)",
            "Top-20": f"{(taxonomy['expanded_pool_depths']['top5'] + taxonomy['expanded_pool_depths']['top10'] + taxonomy['expanded_pool_depths']['top15'] + taxonomy['expanded_pool_depths']['top20'])}/40 ({(taxonomy['expanded_pool_depths']['top5'] + taxonomy['expanded_pool_depths']['top10'] + taxonomy['expanded_pool_depths']['top15'] + taxonomy['expanded_pool_depths']['top20'])/40*100:.2f}%)"
        },
        "taxonomy": taxonomy,
        "query_classifications": query_classifications
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n=== DEV FAILURE TAXONOMY SUMMARY ===")
    print(f"Total DEV Queries: {summary['total_dev_queries']}")
    print(f"  GOLD_TOP1 (Success at Rank 1):                 {summary['gold_top1_count']} ({summary['gold_top1_count']/40*100:.2f}%)")
    print(f"  GOLD_TOPK_NOT_TOP1 (Present in Top-5, not R1): {summary['gold_topk_not_top1_count']} ({summary['gold_topk_not_top1_count']/40*100:.2f}%)")
    print(f"  GOLD_NOT_IN_DENSE_TOP5 (Missed by Dense Top-5): {summary['gold_not_in_dense_top5_count']} ({summary['gold_not_in_dense_top5_count']/40*100:.2f}%)")
    print(f"\nExpanded Candidate Pool Dense Recall:")
    for k, v in summary["expanded_pool_cumulative_dense_recall"].items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
