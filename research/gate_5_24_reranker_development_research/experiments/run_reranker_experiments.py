"""
Gate 5.24 — Phase 5 & 6: Controlled Reranker Experiments on DEV-24 (N=40)
Tests principled evidence-selection and reranking strategies to address identified failure modes:
1. Strategy 1: Control Baseline (Track A + 0.85x overview debias)
2. Strategy 2: Dense-Reranker Score Fusion (Anchored Semantic Fusion, lambda=0.15)
3. Strategy 3: Dominant-Source Topical Gating (Source-Gated Affinity Boost, beta=1.20)
4. Strategy 4: Exact-Entity Lexical Overlap Anchoring (additive weight=0.05)
5. Strategy 5: Dual Topical-Lexical Anchoring (Dense Anchor + Lexical Boost)
"""

import json
import os
import sys
import time
import re
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
RESEARCH_DIR = os.path.abspath(os.path.join(GATE_DIR, ".."))

BENCHMARK_FILE = os.path.join(GATE_DIR, "benchmark", "dev24_benchmark.json")
CHUNKS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
COMPARISONS_OUT_FILE = os.path.join(GATE_DIR, "comparisons", "gate_5_24_strategy_comparison.json")

# Track A Unicode-Safe Procedural Normalization (Frozen in Gate 5.21)
TRACK_A_MAPPINGS = [
    (r'(?:\b|(?<=^)|(?<=\s))(pura|pure|pora|pore|burn|burns|scald|scalds|blister)(?:\b|(?=$)|(?=\s|[.,?!]))|(পুড়ে|পোড়া|ফোস্কা)', 
     'burns scalds cool running water first aid'),
    (r'(?:\b|(?<=^)|(?<=\s))(kete|kata|katse|rokt|rokto|bleeding|bleed|cut|cuts|graze|grazes|antiseptic)(?:\b|(?=$)|(?=\s|[.,?!]))|(কাটা|রক্ত|রক্তপাত|জীবাণুনাশক)', 
     'cuts grazes bleeding pressure clean dressing wound'),
    (r'(?:\b|(?<=^)|(?<=\s))(shash|shash\s*kosto|shash\s*nite\s*kosto|inhaler|inhalers|asthma)(?:\b|(?=$)|(?=\s|[.,?!]))|(হাঁপানি|শ্বাসকষ্ট|ইনহেলার)', 
     'asthma attack inhaler spacer breathing difficulty'),
    (r'(?:\b|(?<=^)|(?<=\s))(pani\s*shunnota|pani\s*kom|shukay|dehydration|dehydrated)(?:\b|(?=$)|(?=\s|[.,?!]))|(ডিহাইড্রেশন|পানিশূন্যতা)', 
     'dehydration fluid rehydration oral fluids'),
    (r'(?:\b|(?<=^)|(?<=\s))(bomi|patla\s*paykhana|diarrhoea|vomiting)(?:\b|(?=$)|(?=\s|[.,?!]))|(বমি|ডায়রিয়া|পাতলা\s*পায়খানা)', 
     'diarrhoea vomiting oral rehydration fluids'),
    (r'(?:\b|(?<=^)|(?<=\s))(matha\s*betha|headache|painkiller|paracetamol)(?:\b|(?=$)|(?=\s|[.,?!]))|(মাথাব্যথা|প্যারাসিটামল)', 
     'headache pain relief painkillers paracetamol'),
    (r'(?:\b|(?<=^)|(?<=\s))(jor|fever|temperature)(?:\b|(?=$)|(?=\s|[.,?!]))|(বাচ্চার\s*জ্বর|জ্বর)', 
     'fever high temperature children fluids paracetamol'),
    (r'(?:\b|(?<=^)|(?<=\s))(allergy|anaphylaxis|shash\s*bondho)(?:\b|(?=$)|(?=\s|[.,?!]))|(অ্যালার্জি|অ্যানাফাইলাক্সিস)', 
     'anaphylaxis severe allergic reaction adrenaline 999'),
    (r'(?:\b|(?<=^)|(?<=\s))(emergency|999|hospital|duto)(?:\b|(?=$)|(?=\s|[.,?!]))|(জরুরি|হাসপাতাল)', 
     'emergency call 999 go to A&E')
]

def normalize_query_track_a(query: str) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in TRACK_A_MAPPINGS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        unique_terms = []
        for term in norm_terms:
            if term not in unique_terms:
                unique_terms.append(term)
        return f"{query} ({' '.join(unique_terms)})"
    return query

def compute_token_overlap(q_text: str, chunk_text: str) -> float:
    q_tokens = set(re.findall(r'\w+', q_text.lower()))
    c_tokens = set(re.findall(r'\w+', chunk_text.lower()))
    if not q_tokens or not c_tokens:
        return 0.0
    return len(q_tokens.intersection(c_tokens)) / len(q_tokens)

def main():
    print("=" * 80)
    print("GATE 5.24 — CONTROLLED RERANKER EXPERIMENTS ON DEV-24 (N=40)")
    print("=" * 80)

    # 1. Load Data
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    queries = benchmark["queries"]

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunks_by_id = {c["chunk_id"]: c for c in chunks}

    # 2. Load Models
    print("Loading models on CPU...")
    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    k_depth = 15
    overview_mult = 0.85
    n_queries = len(queries)

    # Pre-compute Dense candidates and Cross-Encoder raw predictions for all 40 queries
    print(f"Pre-computing Dense Top-15 and Cross-Encoder pairs for {n_queries} queries...")
    cached_query_data = []

    for q in queries:
        qid = q["query_id"]
        raw_q = q["query_text"]
        norm_q = normalize_query_track_a(raw_q)
        gold_cids = q["gold_chunk_ids"]
        expected_sid = q["expected_source_id"]

        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:k_depth]
        top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
        top15_dense_scores = [float(dense_scores[idx]) for idx in top15_indices]

        # Cross-encoder raw predictions
        pairs = [[raw_q, chunks_by_id[cid]["text"]] for cid in top15_cids]
        raw_rerank_scores = reranker.predict(pairs)

        cached_query_data.append({
            "query_id": qid,
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "language": q["language"],
            "expected_source_id": expected_sid,
            "gold_chunk_ids": gold_cids,
            "query_type": q["query_type"],
            "top15_cids": top15_cids,
            "top15_dense_scores": top15_dense_scores,
            "raw_rerank_scores": [float(s) for s in raw_rerank_scores]
        })

    print("✓ Candidate pairs and scores pre-computed.")

    # Define Strategies
    strategies = [
        {
            "id": "STRATEGY_1_CONTROL_BASELINE",
            "name": "Control Baseline (Track A + 0.85x Overview Debiasing)",
            "description": "Standard frozen Gate 5.21 candidate: raw BGE reranker logits with 0.85x multiplier for -HYB-000 overview chunks."
        },
        {
            "id": "STRATEGY_2_DENSE_RERANK_FUSION",
            "name": "Dense-Reranker Score Fusion (Lambda=0.15)",
            "description": "Blends normalized dense similarity with cross-encoder score to anchor topical document identity: final_score = rerank_score + 0.15 * dense_score."
        },
        {
            "id": "STRATEGY_3_DOMINANT_SOURCE_GATING",
            "name": "Dominant-Source Topical Gating (Beta=1.20)",
            "description": "Identifies the consensus source document from the Dense Top-3 candidates. Applies a 1.20x affinity boost to chunks originating from the dominant document."
        },
        {
            "id": "STRATEGY_4_LEXICAL_ENTITY_ANCHOR",
            "name": "Exact-Entity Lexical Overlap Anchoring (Alpha=0.05)",
            "description": "Adds a small token-overlap bonus (0.05 * Jaccard overlap) to cross-encoder score to reward exact keyword presence over generic urgency language."
        },
        {
            "id": "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR",
            "name": "Dual Topical-Lexical Anchor (Dense Fusion + Lexical Boost)",
            "description": "Combines dense-reranker score fusion (lambda=0.10) with exact-entity lexical anchoring (alpha=0.03)."
        }
    ]

    all_strategy_results = {}

    for strat in strategies:
        strat_id = strat["id"]
        strat_name = strat["name"]
        print(f"\nEvaluating: {strat_name}...")

        query_evals = []

        for qdata in cached_query_data:
            qid = qdata["query_id"]
            raw_q = qdata["raw_query"]
            top15_cids = qdata["top15_cids"]
            top15_dense = qdata["top15_dense_scores"]
            raw_rerank = qdata["raw_rerank_scores"]
            gold_cids = qdata["gold_chunk_ids"]
            expected_sid = qdata["expected_source_id"]

            adjusted_scores = []

            if strat_id == "STRATEGY_1_CONTROL_BASELINE":
                for cid, r_score in zip(top15_cids, raw_rerank):
                    score = r_score
                    if cid.endswith("-HYB-000"):
                        score *= overview_mult
                    adjusted_scores.append(score)

            elif strat_id == "STRATEGY_2_DENSE_RERANK_FUSION":
                for cid, r_score, d_score in zip(top15_cids, raw_rerank, top15_dense):
                    score = r_score
                    if cid.endswith("-HYB-000"):
                        score *= overview_mult
                    # Additive blend with dense cosine score (dense scores in ~0.6-0.8 range)
                    score = score + 0.15 * d_score
                    adjusted_scores.append(score)

            elif strat_id == "STRATEGY_3_DOMINANT_SOURCE_GATING":
                # Find dominant source in Top-3 dense
                top3_sids = [chunks_by_id[cid]["parent_source_id"] for cid in top15_cids[:3]]
                dominant_sid = max(set(top3_sids), key=top3_sids.count)
                for cid, r_score in zip(top15_cids, raw_rerank):
                    score = r_score
                    if cid.endswith("-HYB-000"):
                        score *= overview_mult
                    if chunks_by_id[cid]["parent_source_id"] == dominant_sid:
                        score *= 1.20
                    adjusted_scores.append(score)

            elif strat_id == "STRATEGY_4_LEXICAL_ENTITY_ANCHOR":
                for cid, r_score in zip(top15_cids, raw_rerank):
                    score = r_score
                    if cid.endswith("-HYB-000"):
                        score *= overview_mult
                    overlap = compute_token_overlap(raw_q, chunks_by_id[cid]["text"])
                    score = score + 0.05 * overlap
                    adjusted_scores.append(score)

            elif strat_id == "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR":
                for cid, r_score, d_score in zip(top15_cids, raw_rerank, top15_dense):
                    score = r_score
                    if cid.endswith("-HYB-000"):
                        score *= overview_mult
                    overlap = compute_token_overlap(raw_q, chunks_by_id[cid]["text"])
                    score = score + 0.10 * d_score + 0.03 * overlap
                    adjusted_scores.append(score)

            # Sort by final score
            ranked_indices = np.argsort(-np.array(adjusted_scores))
            final_cids = [top15_cids[i] for i in ranked_indices]
            final_scores = [adjusted_scores[i] for i in ranked_indices]

            final_ranks = [final_cids.index(gc) + 1 for gc in gold_cids if gc in final_cids]
            best_rank = min(final_ranks) if final_ranks else None

            r1 = best_rank is not None and best_rank == 1
            r3 = best_rank is not None and best_rank <= 3
            r5 = best_rank is not None and best_rank <= 5
            rr = (1.0 / best_rank) if best_rank is not None else 0.0

            dense_ranks = [top15_cids.index(gc) + 1 for gc in gold_cids if gc in top15_cids]
            best_dense = min(dense_ranks) if dense_ranks else None

            query_evals.append({
                "query_id": qid,
                "language": qdata["language"],
                "expected_source_id": expected_sid,
                "gold_chunk_ids": gold_cids,
                "best_dense_rank": best_dense,
                "best_final_rank": best_rank,
                "r1": r1,
                "r3": r3,
                "r5": r5,
                "reciprocal_rank": rr,
                "final_top5_cids": final_cids[:5],
                "final_top5_scores": final_scores[:5]
            })

        # Calculate summary metrics
        r1_cnt = sum(1 for e in query_evals if e["r1"])
        r3_cnt = sum(1 for e in query_evals if e["r3"])
        r5_cnt = sum(1 for e in query_evals if e["r5"])
        mrr = float(np.mean([e["reciprocal_rank"] for e in query_evals]))

        # Language breakdown
        lang_breakdown = {}
        for l in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
            l_evals = [e for e in query_evals if e["language"] == l]
            if l_evals:
                lang_breakdown[l] = {
                    "n": len(l_evals),
                    "r1": sum(1 for e in l_evals if e["r1"]),
                    "r3": sum(1 for e in l_evals if e["r3"]),
                    "r5": sum(1 for e in l_evals if e["r5"]),
                    "mrr": round(float(np.mean([e["reciprocal_rank"] for e in l_evals])), 4)
                }

        # Compare vs Baseline (Strategy 1)
        promotions_into_top5 = []
        demotions_out_of_top5 = []
        rank_improvements = []
        rank_degradations = []

        if strat_id != "STRATEGY_1_CONTROL_BASELINE":
            base_evals = all_strategy_results["STRATEGY_1_CONTROL_BASELINE"]["query_evaluations"]
            for cur_e, b_e in zip(query_evals, base_evals):
                qid = cur_e["query_id"]
                cur_r = cur_e["best_final_rank"]
                base_r = b_e["best_final_rank"]

                # Movement relative to Top-5
                if not b_e["r5"] and cur_e["r5"]:
                    promotions_into_top5.append({"query_id": qid, "from_rank": base_r, "to_rank": cur_r})
                elif b_e["r5"] and not cur_e["r5"]:
                    demotions_out_of_top5.append({"query_id": qid, "from_rank": base_r, "to_rank": cur_r})

                # General rank movement
                if cur_r is not None and base_r is not None:
                    if cur_r < base_r:
                        rank_improvements.append({"query_id": qid, "from_rank": base_r, "to_rank": cur_r})
                    elif cur_r > base_r:
                        rank_degradations.append({"query_id": qid, "from_rank": base_r, "to_rank": cur_r})

        all_strategy_results[strat_id] = {
            "strategy_id": strat_id,
            "strategy_name": strat_name,
            "description": strat["description"],
            "metrics": {
                "chunk_r1_count": r1_cnt,
                "chunk_r1_pct": round(r1_cnt / n_queries * 100, 2),
                "chunk_r3_count": r3_cnt,
                "chunk_r3_pct": round(r3_cnt / n_queries * 100, 2),
                "chunk_r5_count": r5_cnt,
                "chunk_r5_pct": round(r5_cnt / n_queries * 100, 2),
                "chunk_mrr": round(mrr, 4)
            },
            "language_breakdown": lang_breakdown,
            "movement_vs_baseline": {
                "promotions_into_top5_count": len(promotions_into_top5),
                "promotions_into_top5": promotions_into_top5,
                "demotions_out_of_top5_count": len(demotions_out_of_top5),
                "demotions_out_of_top5": demotions_out_of_top5,
                "rank_improvements_count": len(rank_improvements),
                "rank_degradations_count": len(rank_degradations)
            },
            "query_evaluations": query_evals
        }

    # Save Comparison Report
    with open(COMPARISONS_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_strategy_results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("GATE 5.24 STRATEGY COMPARISON SUMMARY ON DEV-24 (N=40)")
    print("=" * 80)
    print(f"{'Strategy':<42s} | {'R@1':<12s} | {'R@3':<12s} | {'R@5':<12s} | {'MRR':<8s} | {'Prom / Dem':<10s}")
    print("-" * 105)

    for strat in strategies:
        sid = strat["id"]
        res = all_strategy_results[sid]
        m = res["metrics"]
        mov = res["movement_vs_baseline"]
        prom_dem_str = f"+{mov['promotions_into_top5_count']} / -{mov['demotions_out_of_top5_count']}" if sid != "STRATEGY_1_CONTROL_BASELINE" else "BASELINE"
        r1_str = f"{m['chunk_r1_count']}/40 ({m['chunk_r1_pct']}%)"
        r3_str = f"{m['chunk_r3_count']}/40 ({m['chunk_r3_pct']}%)"
        r5_str = f"{m['chunk_r5_count']}/40 ({m['chunk_r5_pct']}%)"
        print(f"{sid:<42s} | {r1_str:<12s} | {r3_str:<12s} | {r5_str:<12s} | {m['chunk_mrr']:<8.4f} | {prom_dem_str:<10s}")

    print("\nDetailed Failure Movement vs Baseline:")
    for strat in strategies[1:]:
        sid = strat["id"]
        res = all_strategy_results[sid]
        mov = res["movement_vs_baseline"]
        print(f"\n--- {sid} ---")
        if mov["promotions_into_top5"]:
            print("  Promotions into Top-5:")
            for p in mov["promotions_into_top5"]:
                print(f"    + {p['query_id']}: Rank {p['from_rank']} -> Rank {p['to_rank']}")
        if mov["demotions_out_of_top5"]:
            print("  Demotions OUT of Top-5 (Regressions):")
            for d in mov["demotions_out_of_top5"]:
                print(f"    - {d['query_id']}: Rank {d['from_rank']} -> Rank {d['to_rank']}")
        if not mov["promotions_into_top5"] and not mov["demotions_out_of_top5"]:
            print("  No net Top-5 movement.")

if __name__ == "__main__":
    main()
