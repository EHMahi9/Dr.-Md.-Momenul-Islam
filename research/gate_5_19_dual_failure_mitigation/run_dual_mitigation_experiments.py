"""
Gate 5.19 — Development-Only Dual Failure Mitigation Study (DEV N=40)
Evaluates Track A (Dense Normalization), Track B (Reranker Mitigation), and Combined Strategies.
"""

import json
import os
import sys
import time
import re
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

BENCHMARK_FILE = os.path.join(RESEARCH_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
CHUNKS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunk_gold_labels.json")

# Baseline mappings (Gate 5.14 / Gate 5.15)
BASE_MAPPINGS = [
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

# Track A: Robust Unicode-aware procedural normalization dictionary
TRACK_A_MAPPINGS = [
    # Burns & Scalds (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(pura|pure|pora|pore|burn|burns|scald|scalds|blister)(?:\b|(?=$)|(?=\s|[.,?!]))|(পুড়ে|পোড়া|ফোস্কা)', 
     'burns scalds cool running water first aid'),
    
    # Cuts, Grazes & Bleeding (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(kete|kata|katse|rokt|rokto|bleeding|bleed|cut|cuts|graze|grazes|antiseptic)(?:\b|(?=$)|(?=\s|[.,?!]))|(কাটা|রক্ত|রক্তপাত|জীবাণুনাশক)', 
     'cuts grazes bleeding pressure clean dressing wound'),
    
    # Asthma & Breathing (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(shash|shash\s*kosto|shash\s*nite\s*kosto|inhaler|inhalers|asthma)(?:\b|(?=$)|(?=\s|[.,?!]))|(হাঁপানি|শ্বাসকষ্ট|ইনহেলার)', 
     'asthma attack inhaler spacer breathing difficulty'),
    
    # Dehydration & Fluids (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(pani\s*shunnota|pani\s*kom|shukay|dehydration|dehydrated)(?:\b|(?=$)|(?=\s|[.,?!]))|(ডিহাইড্রেশন|পানিশূন্যতা)', 
     'dehydration fluid rehydration oral fluids'),
    
    # Diarrhoea & Vomiting (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(bomi|patla\s*paykhana|diarrhoea|vomiting)(?:\b|(?=$)|(?=\s|[.,?!]))|(বমি|ডায়রিয়া|পাতলা\s*পায়খানা)', 
     'diarrhoea vomiting oral rehydration fluids'),
    
    # Headache & Painkillers (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(matha\s*betha|headache|painkiller|paracetamol)(?:\b|(?=$)|(?=\s|[.,?!]))|(মাথাব্যথা|প্যারাসিটামল)', 
     'headache pain relief painkillers paracetamol'),
    
    # Fever (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(jor|fever|temperature)(?:\b|(?=$)|(?=\s|[.,?!]))|(বাচ্চার\s*জ্বর|জ্বর)', 
     'fever high temperature children fluids paracetamol'),
    
    # Anaphylaxis & Severe Allergy
    (r'(?:\b|(?<=^)|(?<=\s))(allergy|anaphylaxis|shash\s*bondho)(?:\b|(?=$)|(?=\s|[.,?!]))|(অ্যালার্জি|অ্যানাফাইলাক্সিস)', 
     'anaphylaxis severe allergic reaction adrenaline 999'),
    
    # Emergency / Hospital / 999
    (r'(?:\b|(?<=^)|(?<=\s))(emergency|999|hospital|duto)(?:\b|(?=$)|(?=\s|[.,?!]))|(জরুরি|হাসপাতাল)', 
     'emergency call 999 go to A&E')
]

def normalize_query_base(query: str) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in BASE_MAPPINGS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        return f"{query} ({' '.join(norm_terms)})"
    return query

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

def main():
    print("="*80)
    print("GATE 5.19: DEVELOPMENT-ONLY DUAL FAILURE MITIGATION STUDY (N=40)")
    print("="*80)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]
    assert len(dev_queries) == 40, f"Expected 40 DEV queries, got {len(dev_queries)}"

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    print("Loading models on CPU...")
    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    # 1. EVALUATE STRATEGIES
    # Strategy 1: CONTROL BASELINE (Gate 5.14 / 5.15)
    # Strategy 2: TRACK A (Robust Procedural Normalization + 0.85x Debiasing)
    # Strategy 3: TRACK A + DENSE-RERANK FUSION (0.85x debias + 0.10x dense score)
    # Strategy 4: TRACK A + 0.75x OVERVIEW DEBIASING

    strategies = {
        "STRATEGY_1_CONTROL_BASELINE": {
            "norm_func": normalize_query_base,
            "overview_mult": 0.85,
            "dense_weight": 0.0
        },
        "STRATEGY_2_TRACK_A_ROBUST_NORM": {
            "norm_func": normalize_query_track_a,
            "overview_mult": 0.85,
            "dense_weight": 0.0
        },
        "STRATEGY_3_TRACK_A_PLUS_DENSE_FUSION": {
            "norm_func": normalize_query_track_a,
            "overview_mult": 0.85,
            "dense_weight": 0.10
        },
        "STRATEGY_4_TRACK_A_PLUS_075_DEBIASING": {
            "norm_func": normalize_query_track_a,
            "overview_mult": 0.75,
            "dense_weight": 0.0
        }
    }

    all_eval_results = {}

    for strat_name, strat_cfg in strategies.items():
        print("\n" + "="*80)
        print(f"RUNNING: {strat_name}")
        print("="*80)

        norm_fn = strat_cfg["norm_func"]
        overview_m = strat_cfg["overview_mult"]
        dense_w = strat_cfg["dense_weight"]

        # Step 1: Dense Retrieval
        dense_hits_15 = 0
        candidate_pools = []
        pairs_to_rerank = []

        for q in dev_queries:
            qid = q["query_id"]
            raw_q = q["query_text"]
            norm_q = norm_fn(raw_q)
            acceptable_cids = gold_labels[qid]["gold_chunk_ids"]

            q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
            dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
            top15_indices = np.argsort(-dense_scores)[:15]
            top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
            top15_scores = [float(dense_scores[idx]) for idx in top15_indices]

            if any(cid in acceptable_cids for cid in top15_cids):
                dense_hits_15 += 1

            candidate_pools.append({
                "query_id": qid,
                "language_category": q["language_category"],
                "raw_query": raw_q,
                "normalized_query": norm_q,
                "gold_chunk_ids": acceptable_cids,
                "top15_indices": top15_indices,
                "dense_top15_cids": top15_cids,
                "dense_top15_scores": top15_scores
            })

            for idx in top15_indices:
                pairs_to_rerank.append((norm_q, chunks[idx]["text"]))

        # Step 2: Cross-Encoder Reranking
        t0 = time.time()
        rerank_scores_flat = reranker.predict(pairs_to_rerank)
        latency = time.time() - t0

        # Step 3: Reranking & Evaluation
        query_evals = []
        offset = 0
        for cp in candidate_pools:
            qid = cp["query_id"]
            acceptable_cids = cp["gold_chunk_ids"]
            dense_cids = cp["dense_top15_cids"]
            dense_scores = cp["dense_top15_scores"]
            n_c = len(dense_cids)

            raw_scores = [float(s) for s in rerank_scores_flat[offset : offset + n_c]]
            offset += n_c

            adj_scores = []
            for i, cid in enumerate(dense_cids):
                s = raw_scores[i]
                if cid.endswith("-HYB-000"):
                    s = s * overview_m
                if dense_w > 0:
                    s = s * (1.0 - dense_w) + (dense_scores[i] * dense_w)
                adj_scores.append(s)

            adj_scores = np.array(adj_scores)
            rerank_order = np.argsort(-adj_scores)

            rerank_cids = [dense_cids[i] for i in rerank_order]
            rerank_scores = [float(adj_scores[i]) for i in rerank_order]

            top5_cids = rerank_cids[:5]
            hits = [cid in acceptable_cids for cid in top5_cids]
            r1 = hits[0]
            r3 = any(hits[:3])
            r5 = any(hits[:5])

            all_hits = [cid in acceptable_cids for cid in rerank_cids]
            rank = (all_hits.index(True) + 1) if any(all_hits) else 0

            query_evals.append({
                "query_id": qid,
                "language_category": cp["language_category"],
                "raw_query": cp["raw_query"],
                "gold_chunk_ids": acceptable_cids,
                "dense_top15_cids": dense_cids,
                "rerank_top15_cids": rerank_cids,
                "rerank_top15_scores": rerank_scores,
                "final_top5_cids": top5_cids,
                "r1": r1,
                "r3": r3,
                "r5": r5,
                "rank": rank
            })

        # Step 4: Summary Metrics
        n = len(query_evals)
        r1_count = sum(1 for q in query_evals if q["r1"])
        r3_count = sum(1 for q in query_evals if q["r3"])
        r5_count = sum(1 for q in query_evals if q["r5"])
        mrr = sum(1.0 / q["rank"] for q in query_evals if q["rank"] > 0) / n

        lang_breakdown = {}
        for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
            subs = [q for q in query_evals if q["language_category"] == lang]
            ln = len(subs)
            l_r1 = sum(1 for q in subs if q["r1"])
            l_r3 = sum(1 for q in subs if q["r3"])
            l_r5 = sum(1 for q in subs if q["r5"])
            l_mrr = sum(1.0 / q["rank"] for q in subs if q["rank"] > 0) / ln
            lang_breakdown[lang] = {
                "n": ln,
                "dense_r15": f"{sum(1 for q in subs if q['rank'] > 0)}/{ln}",
                "r1_count": f"{l_r1}/{ln}",
                "r1_pct": round(l_r1 / ln * 100, 2),
                "r3_count": f"{l_r3}/{ln}",
                "r3_pct": round(l_r3 / ln * 100, 2),
                "r5_count": f"{l_r5}/{ln}",
                "r5_pct": round(l_r5 / ln * 100, 2),
                "mrr": round(l_mrr, 4)
            }

        summary = {
            "strategy_name": strat_name,
            "dense_r15_count": f"{dense_hits_15}/{n}",
            "dense_r15_pct": round(dense_hits_15 / n * 100, 2),
            "chunk_r1_count": f"{r1_count}/{n}",
            "chunk_r1_pct": round(r1_count / n * 100, 2),
            "chunk_r3_count": f"{r3_count}/{n}",
            "chunk_r3_pct": round(r3_count / n * 100, 2),
            "chunk_r5_count": f"{r5_count}/{n}",
            "chunk_r5_pct": round(r5_count / n * 100, 2),
            "chunk_mrr": round(mrr, 4),
            "latency_seconds": round(latency, 2),
            "language_breakdown": lang_breakdown,
            "query_evaluations": query_evals
        }

        all_eval_results[strat_name] = summary

        print(f"Results for {strat_name}:")
        print(f"  Dense R@15: {summary['dense_r15_count']} ({summary['dense_r15_pct']}%)")
        print(f"  Chunk R@1:  {summary['chunk_r1_count']} ({summary['chunk_r1_pct']}%)")
        print(f"  Chunk R@3:  {summary['chunk_r3_count']} ({summary['chunk_r3_pct']}%)")
        print(f"  Chunk R@5:  {summary['chunk_r5_count']} ({summary['chunk_r5_pct']}%)")
        print(f"  Chunk MRR:  {summary['chunk_mrr']}")

    # Save Strategy Results
    out_file = os.path.join(BASE_DIR, "comparisons", "gate_5_19_mitigation_strategies_comparison.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_eval_results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved all strategy evaluations to {out_file}")

if __name__ == "__main__":
    main()
