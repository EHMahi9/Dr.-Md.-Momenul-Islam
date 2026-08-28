"""
Gate 5.21 — Phase 4 & Phase 5: Controlled Evidence-Selection Architecture Experiments on DEV (N=40)
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

COMPARISONS_OUT_FILE = os.path.join(RESEARCH_DIR, "gate_5_21_evidence_selection_architecture", "comparisons", "gate_5_21_strategy_comparison.json")

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

# Track A Unicode-Safe Procedural Normalization (Gate 5.19)
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

def compute_lexical_specificity_bonus(query_str: str, chunk_text: str) -> float:
    """Computes exact lexical and numeric token overlap between query and chunk."""
    q_tokens = set(re.findall(r'\w+', query_str.lower()))
    c_tokens = set(re.findall(r'\w+', chunk_text.lower()))
    if not q_tokens:
        return 0.0
    # Filter stopwords
    common_stops = {'is', 'are', 'the', 'a', 'an', 'to', 'for', 'in', 'on', 'of', 'and', 'or', 'how', 'what', 'when', 'should', 'you', 'if', 'ki', 'kivabe', 'koto', 'hole', 'ba', 'ar', 'er', 'te'}
    content_q = q_tokens - common_stops
    if not content_q:
        return 0.0
    overlap = content_q.intersection(c_tokens)
    return len(overlap) / len(content_q)

def select_with_per_source_cap(ranked_cids, ranked_scores, chunks_by_id, top_k=5, max_per_doc=3):
    """Greedy selection of top chunks subject to a maximum chunk quota per parent source document."""
    selected_cids = []
    selected_scores = []
    source_counts = {}

    for cid, score in zip(ranked_cids, ranked_scores):
        chk = chunks_by_id.get(cid, {})
        sid = chk.get("parent_source_id", "UNKNOWN")
        curr_count = source_counts.get(sid, 0)

        if curr_count < max_per_doc:
            selected_cids.append(cid)
            selected_scores.append(score)
            source_counts[sid] = curr_count + 1

        if len(selected_cids) == top_k:
            break

    # If quota prevented filling top_k slots, fill from remaining
    if len(selected_cids) < top_k:
        for cid, score in zip(ranked_cids, ranked_scores):
            if cid not in selected_cids:
                selected_cids.append(cid)
                selected_scores.append(score)
            if len(selected_cids) == top_k:
                break

    return selected_cids, selected_scores

def evaluate_strategy(strat_name, strat_cfg, dev_queries, chunks, chunks_by_id, gold_labels, dense_model, reranker, chunk_embeddings):
    print(f"\nEvaluating: {strat_name}...")
    norm_fn = strat_cfg["norm_fn"]
    overview_mult = strat_cfg.get("overview_mult", 0.85)
    use_lexical_bonus = strat_cfg.get("use_lexical_bonus", False)
    lexical_weight = strat_cfg.get("lexical_weight", 0.05)
    max_per_doc = strat_cfg.get("max_per_doc", 999) # 999 = unconstrained

    # Step 1: Dense Retrieval
    dense_hits_15 = 0
    candidate_pools = []
    pairs_to_rerank = []

    for q in dev_queries:
        qid = q["query_id"]
        raw_q = q["query_text"]
        norm_q = norm_fn(raw_q)
        acceptable_cids = gold_labels[qid]["gold_chunk_ids"]
        expected_sid = q["expected_source_id"]

        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:15]
        top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]

        all_indices = np.argsort(-dense_scores)
        all_cids = [chunks[idx]["chunk_id"] for idx in all_indices]
        dense_rank = min([all_cids.index(cid) + 1 for cid in acceptable_cids if cid in all_cids])
        dense_hit = (dense_rank <= 15)

        if dense_hit:
            dense_hits_15 += 1

        candidate_pools.append({
            "query_id": qid,
            "language_category": q["language_category"],
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "expected_source_id": expected_sid,
            "gold_chunk_ids": acceptable_cids,
            "dense_rank": dense_rank,
            "dense_hit_r15": dense_hit,
            "top15_indices": top15_indices,
            "dense_top15_cids": top15_cids
        })

        for idx in top15_indices:
            pairs_to_rerank.append((norm_q, chunks[idx]["text"]))

    # Step 2: Cross-Encoder Inference
    t0 = time.time()
    rerank_scores_flat = reranker.predict(pairs_to_rerank)
    latency = time.time() - t0

    # Step 3: Scoring & Context Selection
    query_evals = []
    offset = 0
    for cp in candidate_pools:
        qid = cp["query_id"]
        raw_q = cp["raw_query"]
        norm_q = cp["normalized_query"]
        acceptable_cids = cp["gold_chunk_ids"]
        dense_cids = cp["dense_top15_cids"]
        n_c = len(dense_cids)

        raw_scores = [float(s) for s in rerank_scores_flat[offset : offset + n_c]]
        offset += n_c

        adj_scores = []
        for i, cid in enumerate(dense_cids):
            s = raw_scores[i]
            if cid.endswith("-HYB-000"):
                s = s * overview_mult
            if use_lexical_bonus:
                chk_txt = chunks_by_id[cid]["text"]
                bonus = compute_lexical_specificity_bonus(norm_q, chk_txt)
                s = s + (bonus * lexical_weight)
            adj_scores.append(s)

        adj_scores = np.array(adj_scores)
        rerank_order = np.argsort(-adj_scores)

        full_ranked_cids = [dense_cids[i] for i in rerank_order]
        full_ranked_scores = [float(adj_scores[i]) for i in rerank_order]

        # Apply Per-Source Diversification Cap if active
        if max_per_doc < 999:
            final_top5_cids, final_top5_scores = select_with_per_source_cap(
                full_ranked_cids, full_ranked_scores, chunks_by_id, top_k=5, max_per_doc=max_per_doc
            )
        else:
            final_top5_cids = full_ranked_cids[:5]
            final_top5_scores = full_ranked_scores[:5]

        # Metrics for query
        hits_5 = [cid in acceptable_cids for cid in final_top5_cids]
        r1 = hits_5[0]
        r3 = any(hits_5[:3])
        r5 = any(hits_5[:5])

        # Rank in delivered context vs full ranked list
        if r5:
            rank_in_top5 = hits_5.index(True) + 1
        else:
            all_hits = [cid in acceptable_cids for cid in full_ranked_cids]
            rank_in_top5 = (all_hits.index(True) + 1) if any(all_hits) else 0

        query_evals.append({
            "query_id": qid,
            "language_category": cp["language_category"],
            "raw_query": raw_q,
            "gold_chunk_ids": acceptable_cids,
            "dense_rank": cp["dense_rank"],
            "dense_hit_r15": cp["dense_hit_r15"],
            "final_top5_cids": final_top5_cids,
            "final_top5_scores": final_top5_scores,
            "r1": r1,
            "r3": r3,
            "r5": r5,
            "rank": rank_in_top5
        })

    n = len(query_evals)
    r1_cnt = sum(1 for q in query_evals if q["r1"])
    r3_cnt = sum(1 for q in query_evals if q["r3"])
    r5_cnt = sum(1 for q in query_evals if q["r5"])
    mrr = sum(1.0 / q["rank"] for q in query_evals if q["rank"] > 0) / n

    # Language Breakdown
    lang_breakdown = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        subs = [q for q in query_evals if q["language_category"] == lang]
        ln = len(subs)
        l_dense_r15 = sum(1 for q in subs if q["dense_hit_r15"])
        l_r1 = sum(1 for q in subs if q["r1"])
        l_r3 = sum(1 for q in subs if q["r3"])
        l_r5 = sum(1 for q in subs if q["r5"])
        l_mrr = sum(1.0 / q["rank"] for q in subs if q["rank"] > 0) / ln
        lang_breakdown[lang] = {
            "n": ln,
            "dense_r15": f"{l_dense_r15}/{ln}",
            "r1_count": f"{l_r1}/{ln}",
            "r1_pct": round(l_r1 / ln * 100, 2),
            "r3_count": f"{l_r3}/{ln}",
            "r3_pct": round(l_r3 / ln * 100, 2),
            "r5_count": f"{l_r5}/{ln}",
            "r5_pct": round(l_r5 / ln * 100, 2),
            "mrr": round(l_mrr, 4)
        }

    return {
        "strategy_name": strat_name,
        "dense_r15_count": f"{dense_hits_15}/{n}",
        "dense_r15_pct": round(dense_hits_15 / n * 100, 2),
        "chunk_r1_count": f"{r1_cnt}/{n}",
        "chunk_r1_pct": round(r1_cnt / n * 100, 2),
        "chunk_r3_count": f"{r3_cnt}/{n}",
        "chunk_r3_pct": round(r3_cnt / n * 100, 2),
        "chunk_r5_count": f"{r5_cnt}/{n}",
        "chunk_r5_pct": round(r5_cnt / n * 100, 2),
        "chunk_mrr": round(mrr, 4),
        "latency_seconds": round(latency, 2),
        "language_breakdown": lang_breakdown,
        "query_evaluations": query_evals
    }

def main():
    print("="*80)
    print("GATE 5.21: EVIDENCE-SELECTION ARCHITECTURE STUDY ON DEV (N=40)")
    print("="*80)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]
    assert len(dev_queries) == 40, f"Expected 40 DEV queries, got {len(dev_queries)}"

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunks_by_id = {c["chunk_id"]: c for c in chunks}

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    print("Loading models on CPU...")
    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    strategies_to_test = {
        "STRATEGY_1_CONTROL_BASELINE": {
            "norm_fn": normalize_query_base,
            "overview_mult": 0.85,
            "max_per_doc": 999
        },
        "STRATEGY_2_TRACK_A_NORM_ONLY": {
            "norm_fn": normalize_query_track_a,
            "overview_mult": 0.85,
            "max_per_doc": 999
        },
        "STRATEGY_3_SAME_SOURCE_CAP_3": {
            "norm_fn": normalize_query_track_a,
            "overview_mult": 0.85,
            "max_per_doc": 3
        },
        "STRATEGY_4_SAME_SOURCE_CAP_2": {
            "norm_fn": normalize_query_track_a,
            "overview_mult": 0.85,
            "max_per_doc": 2
        },
        "STRATEGY_5_TRACK_A_PLUS_LEXICAL_SPECIFICITY": {
            "norm_fn": normalize_query_track_a,
            "overview_mult": 0.85,
            "use_lexical_bonus": True,
            "lexical_weight": 0.05,
            "max_per_doc": 999
        }
    }

    all_results = {}
    for s_name, s_cfg in strategies_to_test.items():
        res = evaluate_strategy(s_name, s_cfg, dev_queries, chunks, chunks_by_id, gold_labels, dense_model, reranker, chunk_embeddings)
        all_results[s_name] = res

        print(f"\nSummary for {s_name}:")
        print(f"  Dense R@15: {res['dense_r15_count']} ({res['dense_r15_pct']}%)")
        print(f"  Chunk R@1:  {res['chunk_r1_count']} ({res['chunk_r1_pct']}%)")
        print(f"  Chunk R@3:  {res['chunk_r3_count']} ({res['chunk_r3_pct']}%)")
        print(f"  Chunk R@5:  {res['chunk_r5_count']} ({res['chunk_r5_pct']}%)")
        print(f"  Chunk MRR:  {res['chunk_mrr']}")

    # Save Results
    with open(COMPARISONS_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved all strategy comparisons to {COMPARISONS_OUT_FILE}")

if __name__ == "__main__":
    main()
