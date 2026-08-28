"""
Gate 5.21 — Phase 6, 7, 8: Detailed Failure Movement & Language Analysis
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

COMP_FILE = os.path.join(RESEARCH_DIR, "gate_5_21_evidence_selection_architecture", "comparisons", "gate_5_21_strategy_comparison.json")
OUT_FILE = os.path.join(RESEARCH_DIR, "gate_5_21_evidence_selection_architecture", "diagnostics", "failure_movement_analysis.json")

def main():
    with open(COMP_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    strat1 = {q["query_id"]: q for q in data["STRATEGY_1_CONTROL_BASELINE"]["query_evaluations"]}
    strat2 = {q["query_id"]: q for q in data["STRATEGY_2_TRACK_A_NORM_ONLY"]["query_evaluations"]}
    strat3 = {q["query_id"]: q for q in data["STRATEGY_3_SAME_SOURCE_CAP_3"]["query_evaluations"]}
    strat4 = {q["query_id"]: q for q in data["STRATEGY_4_SAME_SOURCE_CAP_2"]["query_evaluations"]}
    strat5 = {q["query_id"]: q for q in data["STRATEGY_5_TRACK_A_PLUS_LEXICAL_SPECIFICITY"]["query_evaluations"]}

    movement_strat2_vs_1 = []
    movement_strat3_vs_2 = []
    movement_strat4_vs_2 = []
    movement_strat5_vs_2 = []

    for qid, q1 in strat1.items():
        q2 = strat2[qid]
        q3 = strat3[qid]
        q4 = strat4[qid]
        q5 = strat5[qid]

        # Strat 2 vs 1
        if q2["r5"] != q1["r5"] or q2["rank"] != q1["rank"]:
            if not q1["r5"] and q2["r5"]:
                cat = "GOLD_PROMOTED_INTO_TOP5"
            elif q1["r5"] and not q2["r5"]:
                cat = "GOLD_DEMOTED_OUT_OF_TOP5"
            elif q2["rank"] < q1["rank"]:
                cat = "GOLD_RANK_IMPROVED"
            else:
                cat = "GOLD_RANK_DROPPED"
            movement_strat2_vs_1.append({
                "query_id": qid,
                "category": cat,
                "strat1_rank": q1["rank"],
                "strat2_rank": q2["rank"],
                "raw_query": q1["raw_query"]
            })

        # Strat 3 vs 2
        if q3["r5"] != q2["r5"] or q3["rank"] != q2["rank"]:
            if not q2["r5"] and q3["r5"]:
                cat = "GOLD_PROMOTED_INTO_TOP5"
            elif q2["r5"] and not q3["r5"]:
                cat = "GOLD_DEMOTED_OUT_OF_TOP5"
            elif q3["rank"] < q2["rank"]:
                cat = "GOLD_RANK_IMPROVED"
            else:
                cat = "GOLD_RANK_DROPPED"
            movement_strat3_vs_2.append({
                "query_id": qid,
                "category": cat,
                "strat2_rank": q2["rank"],
                "strat3_rank": q3["rank"],
                "raw_query": q2["raw_query"]
            })

    output = {
        "strategy_2_vs_strategy_1_movement": {
            "total_changed": len(movement_strat2_vs_1),
            "promotions": sum(1 for m in movement_strat2_vs_1 if "PROMOTED" in m["category"] or "IMPROVED" in m["category"]),
            "demotions": sum(1 for m in movement_strat2_vs_1 if "DEMOTED" in m["category"] or "DROPPED" in m["category"]),
            "movements": movement_strat2_vs_1
        },
        "strategy_3_vs_strategy_2_movement": {
            "total_changed": len(movement_strat3_vs_2),
            "promotions": sum(1 for m in movement_strat3_vs_2 if "PROMOTED" in m["category"] or "IMPROVED" in m["category"]),
            "demotions": sum(1 for m in movement_strat3_vs_2 if "DEMOTED" in m["category"] or "DROPPED" in m["category"]),
            "movements": movement_strat3_vs_2
        }
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("Failure movement analysis written to:", OUT_FILE)
    print(f"Strat 2 vs 1: {output['strategy_2_vs_strategy_1_movement']['promotions']} improvements, {output['strategy_2_vs_strategy_1_movement']['demotions']} demotions")
    print(f"Strat 3 vs 2: {output['strategy_3_vs_strategy_2_movement']['promotions']} improvements, {output['strategy_3_vs_strategy_2_movement']['demotions']} demotions")

if __name__ == "__main__":
    main()
