"""
Gate 5.24 — Phase 4: Baseline Diagnostics on DEV-24 Benchmark
Evaluates baseline configuration and performs deep diagnostic analysis of reranker behavior.
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
FROZEN_CONFIG_FILE = os.path.join(RESEARCH_DIR, "gate_5_21_evidence_selection_architecture", "candidate", "frozen_candidate_configuration.json")

RESULTS_FILE = os.path.join(GATE_DIR, "diagnostics", "baseline_dev24_results.json")
DIAGNOSTICS_FILE = os.path.join(GATE_DIR, "diagnostics", "reranker_diagnostic_breakdown.json")

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

def compute_lexical_overlap(q_text: str, chunk_text: str) -> float:
    # simple word-level Jaccard overlap
    q_tokens = set(re.findall(r'\w+', q_text.lower()))
    c_tokens = set(re.findall(r'\w+', chunk_text.lower()))
    if not q_tokens or not c_tokens:
        return 0.0
    return len(q_tokens.intersection(c_tokens)) / len(q_tokens)

def main():
    print("=" * 80)
    print("GATE 5.24 — BASELINE EVALUATION & RERANKER DIAGNOSTICS (DEV-24)")
    print("=" * 80)

    # 1. Load Data
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    queries = benchmark["queries"]

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunks_by_id = {c["chunk_id"]: c for c in chunks}

    # 2. Load Models
    print("Loading models (CPU)...")
    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    k_depth = 15
    overview_mult = 0.85

    query_evaluations = []
    diagnostic_cases = []

    print(f"Evaluating {len(queries)} DEV-24 Queries...")

    for q in queries:
        qid = q["query_id"]
        raw_q = q["query_text"]
        lang = q["language"]
        expected_sid = q["expected_source_id"]
        gold_cids = q["gold_chunk_ids"]
        qtype = q["query_type"]
        intent_cat = q["intent_category"]

        # Step 1: Normalization
        norm_q = normalize_query_track_a(raw_q)

        # Step 2: Dense Retrieval
        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:k_depth]
        top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
        top15_scores = [float(dense_scores[idx]) for idx in top15_indices]

        dense_ranks = []
        for gc in gold_cids:
            if gc in top15_cids:
                dense_ranks.append(top15_cids.index(gc) + 1)
        best_dense_rank = min(dense_ranks) if dense_ranks else None
        dense_hit_r15 = best_dense_rank is not None and best_dense_rank <= 15

        # Step 3: Cross-Encoder Reranking
        pairs = [[raw_q, chunks_by_id[cid]["text"]] for cid in top15_cids]
        raw_rerank_scores = reranker.predict(pairs)

        # Step 4: Overview Debiasing (0.85x for -HYB-000)
        adjusted_scores = []
        for cid, score in zip(top15_cids, raw_rerank_scores):
            adj = float(score)
            if cid.endswith("-HYB-000"):
                adj *= overview_mult
            adjusted_scores.append(adj)

        rerank_order = np.argsort(-np.array(adjusted_scores))
        final_ranked_cids = [top15_cids[i] for i in rerank_order]
        final_ranked_scores = [adjusted_scores[i] for i in rerank_order]
        final_top5_cids = final_ranked_cids[:5]
        final_top5_scores = final_ranked_scores[:5]

        final_ranks = []
        for gc in gold_cids:
            if gc in final_ranked_cids:
                final_ranks.append(final_ranked_cids.index(gc) + 1)
        best_final_rank = min(final_ranks) if final_ranks else None

        r1 = best_final_rank is not None and best_final_rank == 1
        r3 = best_final_rank is not None and best_final_rank <= 3
        r5 = best_final_rank is not None and best_final_rank <= 5
        rr = (1.0 / best_final_rank) if best_final_rank is not None else 0.0

        retrieved_sids = [chunks_by_id[cid]["parent_source_id"] for cid in final_ranked_cids]
        source_r1 = retrieved_sids[0] == expected_sid if retrieved_sids else False
        source_r5 = expected_sid in retrieved_sids[:5]

        # Detailed Diagnostic Case Profile
        rank1_cid = final_ranked_cids[0]
        rank1_score = final_ranked_scores[0]
        rank1_sid = chunks_by_id[rank1_cid]["parent_source_id"]

        gold_in_top15_cids = [gc for gc in gold_cids if gc in top15_cids]
        best_gold_cid = gold_in_top15_cids[0] if gold_in_top15_cids else gold_cids[0]
        best_gold_score = final_ranked_scores[final_ranked_cids.index(best_gold_cid)] if best_gold_cid in final_ranked_cids else None
        
        score_margin = (rank1_score - best_gold_score) if best_gold_score is not None else None

        competitors_top5 = []
        for rank_idx, (cid, score) in enumerate(zip(final_top5_cids, final_top5_scores), start=1):
            c_info = chunks_by_id[cid]
            is_gold = cid in gold_cids
            is_same_doc = c_info["parent_source_id"] == expected_sid
            lex_overlap = compute_lexical_overlap(raw_q, c_info["text"])
            competitors_top5.append({
                "rank": rank_idx,
                "chunk_id": cid,
                "score": float(score),
                "is_gold": is_gold,
                "parent_source_id": c_info["parent_source_id"],
                "is_same_doc": is_same_doc,
                "char_length": c_info["char_length"],
                "lexical_overlap": round(lex_overlap, 3),
                "text_snippet": c_info["text"].replace('\n', ' ')[:100]
            })

        diag_case = {
            "query_id": qid,
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "language": lang,
            "expected_source_id": expected_sid,
            "gold_chunk_ids": gold_cids,
            "query_type": qtype,
            "intent_category": intent_cat,
            "best_dense_rank": best_dense_rank,
            "best_final_rank": best_final_rank,
            "r1": r1,
            "r3": r3,
            "r5": r5,
            "reciprocal_rank": rr,
            "rank1_chunk_id": rank1_cid,
            "rank1_score": float(rank1_score),
            "rank1_is_same_doc": rank1_sid == expected_sid,
            "best_gold_score": float(best_gold_score) if best_gold_score is not None else None,
            "score_margin_vs_rank1": float(score_margin) if score_margin is not None else None,
            "top5_competitors": competitors_top5,
            "dense_hit_r15": dense_hit_r15,
            "status": "PASS_TOP1" if r1 else "PASS_TOP3" if r3 else "PASS_TOP5" if r5 else "FAIL_RERANKED_OUT" if dense_hit_r15 else "FAIL_DENSE_MISS"
        }
        diagnostic_cases.append(diag_case)

        query_evaluations.append({
            "query_id": qid,
            "language": lang,
            "expected_source_id": expected_sid,
            "gold_chunk_ids": gold_cids,
            "best_dense_rank": best_dense_rank,
            "best_final_rank": best_final_rank,
            "r1": r1,
            "r3": r3,
            "r5": r5,
            "reciprocal_rank": rr,
            "source_r1": source_r1,
            "source_r5": source_r5,
            "dense_hit_r15": dense_hit_r15
        })

    # Summary Metrics
    n = len(query_evaluations)
    r1_cnt = sum(1 for e in query_evaluations if e["r1"])
    r3_cnt = sum(1 for e in query_evaluations if e["r3"])
    r5_cnt = sum(1 for e in query_evaluations if e["r5"])
    mrr = float(np.mean([e["reciprocal_rank"] for e in query_evaluations]))
    dense15_cnt = sum(1 for e in query_evaluations if e["dense_hit_r15"])

    # Language Breakdown
    lang_breakdown = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        l_evals = [e for e in query_evaluations if e["language"] == lang]
        if l_evals:
            n_l = len(l_evals)
            lang_breakdown[lang] = {
                "n": n_l,
                "dense_r15": sum(1 for e in l_evals if e["dense_hit_r15"]),
                "dense_r15_pct": round(sum(1 for e in l_evals if e["dense_hit_r15"]) / n_l * 100, 1),
                "r1": sum(1 for e in l_evals if e["r1"]),
                "r1_pct": round(sum(1 for e in l_evals if e["r1"]) / n_l * 100, 1),
                "r3": sum(1 for e in l_evals if e["r3"]),
                "r3_pct": round(sum(1 for e in l_evals if e["r3"]) / n_l * 100, 1),
                "r5": sum(1 for e in l_evals if e["r5"]),
                "r5_pct": round(sum(1 for e in l_evals if e["r5"]) / n_l * 100, 1),
                "mrr": round(float(np.mean([e["reciprocal_rank"] for e in l_evals])), 4)
            }

    # Document Breakdown
    doc_breakdown = {}
    for sid in sorted(list(set(e["expected_source_id"] for e in query_evaluations))):
        d_evals = [e for e in query_evaluations if e["expected_source_id"] == sid]
        n_d = len(d_evals)
        doc_breakdown[sid] = {
            "n": n_d,
            "dense_r15": sum(1 for e in d_evals if e["dense_hit_r15"]),
            "dense_r15_pct": round(sum(1 for e in d_evals if e["dense_hit_r15"]) / n_d * 100, 1),
            "r5": sum(1 for e in d_evals if e["r5"]),
            "r5_pct": round(sum(1 for e in d_evals if e["r5"]) / n_d * 100, 1),
            "mrr": round(float(np.mean([e["reciprocal_rank"] for e in d_evals])), 4)
        }

    results = {
        "gate": "GATE_5.24",
        "benchmark": "DEV_24",
        "total_queries": n,
        "primary_metrics": {
            "chunk_r1_count": r1_cnt,
            "chunk_r1_pct": round(r1_cnt / n * 100, 2),
            "chunk_r3_count": r3_cnt,
            "chunk_r3_pct": round(r3_cnt / n * 100, 2),
            "chunk_r5_count": r5_cnt,
            "chunk_r5_pct": round(r5_cnt / n * 100, 2),
            "chunk_mrr": round(mrr, 4),
            "dense_r15_count": dense15_cnt,
            "dense_r15_pct": round(dense15_cnt / n * 100, 2)
        },
        "language_breakdown": lang_breakdown,
        "document_breakdown": doc_breakdown,
        "query_evaluations": query_evaluations
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    with open(DIAGNOSTICS_FILE, "w", encoding="utf-8") as f:
        json.dump({"total_queries": n, "cases": diagnostic_cases}, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("DEV-24 BASELINE RESULTS")
    print("=" * 80)
    print(f"Dense Recall@15:      {dense15_cnt}/{n} ({dense15_cnt/n*100:.1f}%)")
    print(f"Final Chunk Recall@1: {r1_cnt}/{n} ({r1_cnt/n*100:.1f}%)")
    print(f"Final Chunk Recall@3: {r3_cnt}/{n} ({r3_cnt/n*100:.1f}%)")
    print(f"Final Chunk Recall@5: {r5_cnt}/{n} ({r5_cnt/n*100:.1f}%)")
    print(f"Final Chunk MRR:      {mrr:.4f}")

    print("\nLanguage Breakdown:")
    for l, m in lang_breakdown.items():
        print(f"  {l:22s}: Dense={m['dense_r15_pct']}% | R@1={m['r1_pct']}% | R@3={m['r3_pct']}% | R@5={m['r5_pct']}% | MRR={m['mrr']:.4f}")

    print("\nDocument Breakdown:")
    for s, m in doc_breakdown.items():
        print(f"  {s:14s}: Dense={m['dense_r15_pct']}% | R@5={m['r5_pct']}% | MRR={m['mrr']:.4f}")

    # Inspect Failures / Demotions
    failures = [c for c in diagnostic_cases if not c["r5"]]
    print(f"\nFailures on DEV-24 (N={len(failures)}):")
    for f_case in failures:
        print(f"\n[{f_case['query_id']}] ({f_case['language']}) Status: {f_case['status']}")
        print(f"  Q: {f_case['raw_query']}")
        print(f"  Expected Gold: {f_case['gold_chunk_ids']} (Dense Rank: {f_case['best_dense_rank']} -> Final Rank: {f_case['best_final_rank']})")
        print(f"  Gold Score: {f_case['best_gold_score']}, Rank-1 Competitor Score: {f_case['rank1_score']} (Margin: {f_case['score_margin_vs_rank1']})")
        print("  Top-5 Competitors:")
        for comp in f_case["top5_competitors"]:
            same_doc_tag = "[SAME-DOC]" if comp["is_same_doc"] else "[CROSS-DOC]"
            gold_tag = "[GOLD]" if comp["is_gold"] else ""
            print(f"    #{comp['rank']}: {comp['chunk_id']} ({comp['score']:.4f}) {same_doc_tag} {gold_tag} - {comp['text_snippet'][:60]}")

if __name__ == "__main__":
    main()
