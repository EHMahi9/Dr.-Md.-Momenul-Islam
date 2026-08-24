"""
Gate 5.14 — Phase 2 & 3: Systematic Controlled Evaluation of 6 Reranker Optimization Strategies on DEV (N=40)
Efficient cached scoring implementation.
"""

import json
import os
import sys
import time
import re
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
BENCHMARK_FILE = os.path.join(ROOT_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
CHUNKS_FILE = os.path.join(ROOT_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(ROOT_DIR, "gate_5_9_optimization", "chunk_gold_labels.json")
EVAL_OUT_FILE = os.path.join(BASE_DIR, "..", "evaluations", "gate_5_14_dev_reranker_comparison.json")

# Gate 5.12 Normalization Rules
BANGLA_BANGLISH_MAPPINGS = [
    (r'\b(pani\s*shunnota|pani\s*kom|dehydration|ডিহাইড্রেশন|পানিশূন্যতা)\b', 'dehydration fluid rehydration oral fluids'),
    (r'\b(shash\s*kosto|shash\s*nite\s*kosto|inhaler|asthma|হাঁপানি|শ্বাসকষ্ট|ইনহেলার)\b', 'asthma attack inhaler spacer breathing difficulty'),
    (r'\b(pura|pure\s*geche|burn|scald|blister|পুড়ে\s*গেলে|পোড়া|ফোস্কা)\b', 'burns scalds cold water cool running water blister first aid'),
    (r'\b(kete\s*geche|rokto|bleeding|cut|graze|antiseptic|কাটা|রক্তপাত|জীবাণুনাশক)\b', 'cuts grazes bleeding pressure clean dressing wound'),
    (r'\b(bomi|patla\s*paykhana|diarrhoea|vomiting|বমি|ডায়রিয়া|পাতলা\s*পায়খানা)\b', 'diarrhoea vomiting oral rehydration fluids'),
    (r'\b(matha\s*betha|headache|painkiller|paracetamol|মাথাব্যথা|প্যারাসিটামল)\b', 'headache pain relief painkillers paracetamol'),
    (r'\b(jor|fever|temperature|বাচ্চার\s*জ্বর|জ্বর)\b', 'fever high temperature children fluids paracetamol'),
    (r'\b(allergy|anaphylaxis|shash\s*bondho|অ্যালার্জি|অ্যানাফাইলাক্সিস)\b', 'anaphylaxis severe allergic reaction adrenaline 999'),
    (r'\b(emergency|999|hospital|duto|জরুরি|হাসপাতাল)\b', 'emergency call 999 go to A&E')
]

def normalize_query_text(query: str) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in BANGLA_BANGLISH_MAPPINGS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        return f"{query} ({' '.join(norm_terms)})"
    return query

def main():
    print("="*80)
    print("GATE 5.14: EVALUATING 6 CONTROLLED RERANKING STRATEGIES ON DEV (N=40)")
    print("="*80)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]
    assert len(dev_queries) == 40

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    # Encode standard passages for dense retrieval
    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    # Precompute Candidate Pools and Cross-Encoder Scores for all 40 queries
    print("Precomputing Dense candidate pools and Cross-Encoder scores...")
    query_candidates_data = []

    for q in dev_queries:
        qid = q["query_id"]
        raw_q = q["query_text"]
        norm_q = normalize_query_text(raw_q)
        gold = gold_labels[qid]
        acceptable_cids = gold["gold_chunk_ids"]

        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:15]
        dense_top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
        dense_top15_dense_scores = [float(dense_scores[idx]) for idx in top15_indices]

        # Standard CE Pairs
        pairs_std = [(norm_q, chunks[idx]["text"]) for idx in top15_indices]
        ce_std_scores = [float(s) for s in reranker.predict(pairs_std)]

        # Section-Header CE Pairs
        pairs_hdr = []
        for idx in top15_indices:
            c = chunks[idx]
            heading = c.get("heading") or c.get("title") or "General"
            txt = f"Section: {heading}\n{c['text']}"
            pairs_hdr.append((norm_q, txt))
        ce_hdr_scores = [float(s) for s in reranker.predict(pairs_hdr)]

        query_candidates_data.append({
            "query_id": qid,
            "raw_q": raw_q,
            "norm_q": norm_q,
            "language_category": q["language_category"],
            "expected_source_id": q["expected_source_id"],
            "acceptable_cids": acceptable_cids,
            "top15_indices": top15_indices,
            "top15_cids": dense_top15_cids,
            "dense_scores": dense_top15_dense_scores,
            "ce_std_scores": ce_std_scores,
            "ce_hdr_scores": ce_hdr_scores
        })

    # Strategies Definition
    strategy_configs = [
        {
            "name": "STRATEGY_1_CONTROL_BASELINE",
            "ce_source": "std",
            "debias_overview": False,
            "score_fusion": False,
            "k_context": 5
        },
        {
            "name": "STRATEGY_2_SECTION_HEADER_CROSS_ENCODER",
            "ce_source": "hdr",
            "debias_overview": False,
            "score_fusion": False,
            "k_context": 5
        },
        {
            "name": "STRATEGY_3_SAME_DOC_OVERVIEW_DEBIASING",
            "ce_source": "std",
            "debias_overview": True,
            "score_fusion": False,
            "k_context": 5
        },
        {
            "name": "STRATEGY_4_DENSE_CROSSENCODER_SCORE_FUSION",
            "ce_source": "std",
            "debias_overview": False,
            "score_fusion": True,
            "k_context": 5
        },
        {
            "name": "STRATEGY_5_CONTEXT_EXPANSION_TOP7",
            "ce_source": "std",
            "debias_overview": False,
            "score_fusion": False,
            "k_context": 7
        },
        {
            "name": "STRATEGY_6_SYNERGISTIC_SECTION_AWARE_DIVERSIFICATION",
            "ce_source": "hdr",
            "debias_overview": True,
            "score_fusion": False,
            "k_context": 5
        }
    ]

    all_strategy_results = {}

    for strat in strategy_configs:
        s_name = strat["name"]
        print(f"\nEvaluating: {s_name}...")
        query_evals = []

        for qdata in query_candidates_data:
            base_scores = qdata["ce_hdr_scores"] if strat["ce_source"] == "hdr" else qdata["ce_std_scores"]
            cids = qdata["top15_cids"]
            dense_s = qdata["dense_scores"]
            acceptable_cids = qdata["acceptable_cids"]

            adj_scores = []
            for i, cid in enumerate(cids):
                score = base_scores[i]
                if strat["debias_overview"] and cid.endswith("-HYB-000"):
                    score = score * 0.85
                if strat["score_fusion"]:
                    score = 0.7 * score + 0.3 * dense_s[i]
                adj_scores.append(score)

            adj_scores = np.array(adj_scores)
            final_order = np.argsort(-adj_scores)
            rerank_cids = [cids[i] for i in final_order]
            rerank_scores = [float(adj_scores[i]) for i in final_order]

            k_ctx = strat["k_context"]
            final_context_cids = rerank_cids[:k_ctx]

            hits = [cid in acceptable_cids for cid in final_context_cids]
            r1 = hits[0] if len(hits) > 0 else False
            r3 = any(hits[:3]) if len(hits) >= 3 else any(hits)
            r5 = any(hits[:5]) if len(hits) >= 5 else any(hits)
            r_ctx = any(hits)

            all_hits = [cid in acceptable_cids for cid in rerank_cids]
            rank = (all_hits.index(True) + 1) if any(all_hits) else 0

            query_evals.append({
                "query_id": qdata["query_id"],
                "language_category": qdata["language_category"],
                "r1": r1,
                "r3": r3,
                "r5": r5,
                "r_context": r_ctx,
                "rank": rank,
                "top1_cid": rerank_cids[0],
                "top5_cids": final_context_cids[:5]
            })

        n = len(query_evals)
        total_r1 = sum(1 for q in query_evals if q["r1"])
        total_r3 = sum(1 for q in query_evals if q["r3"])
        total_r5 = sum(1 for q in query_evals if q["r5"])
        total_r_ctx = sum(1 for q in query_evals if q["r_context"])
        mrr = sum(1.0 / q["rank"] for q in query_evals if q["rank"] > 0) / n

        # Linguistic breakdown
        lang_breakdown = {}
        for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
            l_subs = [q for q in query_evals if q["language_category"] == lang]
            ln = len(l_subs)
            l_r1 = sum(1 for q in l_subs if q["r1"])
            l_r3 = sum(1 for q in l_subs if q["r3"])
            l_r5 = sum(1 for q in l_subs if q["r5"])
            l_mrr = sum(1.0 / q["rank"] for q in l_subs if q["rank"] > 0) / ln
            lang_breakdown[lang] = {
                "n": ln,
                "r1": f"{l_r1}/{ln} ({l_r1/ln*100:.1f}%)",
                "r3": f"{l_r3}/{ln} ({l_r3/ln*100:.1f}%)",
                "r5": f"{l_r5}/{ln} ({l_r5/ln*100:.1f}%)",
                "mrr": round(l_mrr, 4)
            }

        all_strategy_results[s_name] = {
            "strategy_name": s_name,
            "final_chunk_r1": f"{total_r1}/{n} ({total_r1/n*100:.2f}%)",
            "final_chunk_r3": f"{total_r3}/{n} ({total_r3/n*100:.2f}%)",
            "final_chunk_r5": f"{total_r5}/{n} ({total_r5/n*100:.2f}%)",
            "final_context_recall": f"{total_r_ctx}/{n} ({total_r_ctx/n*100:.2f}%)",
            "mrr": round(mrr, 4),
            "language_breakdown": lang_breakdown,
            "query_evaluations": query_evals
        }

        print(f"  R@1: {total_r1}/{n} ({total_r1/n*100:.1f}%) | R@3: {total_r3}/{n} ({total_r3/n*100:.1f}%) | R@5: {total_r5}/{n} ({total_r5/n*100:.1f}%) | MRR: {mrr:.4f}")

    with open(EVAL_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_strategy_results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved all DEV strategy comparisons to {EVAL_OUT_FILE}")

if __name__ == "__main__":
    main()
