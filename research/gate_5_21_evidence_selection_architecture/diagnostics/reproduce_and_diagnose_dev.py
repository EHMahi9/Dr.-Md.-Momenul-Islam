"""
Gate 5.21 — Phase 1 & Phase 2: Baseline Reproduction & Detailed Failure Decomposition on DEV (N=40)
"""

import json
import os
import sys
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

BENCHMARK_FILE = os.path.join(RESEARCH_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
CHUNKS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunk_gold_labels.json")

BASE_OUT_FILE = os.path.join(RESEARCH_DIR, "gate_5_21_evidence_selection_architecture", "baseline", "dev_baseline_reproduction.json")
DIAG_OUT_FILE = os.path.join(BASE_DIR, "dev_reranker_failure_decomposition.json")

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

def normalize_query_base(query: str) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in BASE_MAPPINGS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        return f"{query} ({' '.join(norm_terms)})"
    return query

def main():
    print("="*80)
    print("GATE 5.21 — PHASE 1: DEV BASELINE REPRODUCTION (N=40)")
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

    dense_hits_15 = 0
    candidate_pools = []
    pairs_to_rerank = []

    for q in dev_queries:
        qid = q["query_id"]
        raw_q = q["query_text"]
        norm_q = normalize_query_base(raw_q)
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

    print(f"Reranking {len(pairs_to_rerank)} candidate pairs...")
    rerank_scores_flat = reranker.predict(pairs_to_rerank)

    query_evals = []
    offset = 0
    for cp in candidate_pools:
        qid = cp["query_id"]
        acceptable_cids = cp["gold_chunk_ids"]
        dense_cids = cp["dense_top15_cids"]
        n_c = len(dense_cids)

        raw_scores = [float(s) for s in rerank_scores_flat[offset : offset + n_c]]
        offset += n_c

        # Apply 0.85x overview debiasing
        adj_scores = [s * 0.85 if cid.endswith("-HYB-000") else s for cid, s in zip(dense_cids, raw_scores)]
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
        final_rank = (all_hits.index(True) + 1) if any(all_hits) else 0

        query_evals.append({
            "query_id": qid,
            "language_category": cp["language_category"],
            "raw_query": cp["raw_query"],
            "normalized_query": cp["normalized_query"],
            "expected_source_id": cp["expected_source_id"],
            "gold_chunk_ids": acceptable_cids,
            "dense_rank": cp["dense_rank"],
            "dense_hit_r15": cp["dense_hit_r15"],
            "final_rerank_rank": final_rank,
            "r1": r1,
            "r3": r3,
            "r5": r5,
            "gold_score": rerank_scores[final_rank - 1] if final_rank > 0 else 0.0,
            "rank1_cid": rerank_cids[0],
            "rank1_score": rerank_scores[0],
            "rank5_score": rerank_scores[4] if len(rerank_scores) >= 5 else 0.0,
            "final_top5_cids": top5_cids,
            "final_top5_scores": rerank_scores[:5],
            "rerank_top15_cids": rerank_cids,
            "rerank_top15_scores": rerank_scores
        })

    # Summary
    n = len(query_evals)
    r1_count = sum(1 for q in query_evals if q["r1"])
    r3_count = sum(1 for q in query_evals if q["r3"])
    r5_count = sum(1 for q in query_evals if q["r5"])
    mrr = sum(1.0 / q["final_rerank_rank"] for q in query_evals if q["final_rerank_rank"] > 0) / n

    baseline_report = {
        "gate": "GATE_5.21",
        "timestamp": "2026-08-28T19:42:00+06:00",
        "dense_r15_count": f"{dense_hits_15}/{n} ({round(dense_hits_15/n*100, 2)}%)",
        "chunk_r1_count": f"{r1_count}/{n} ({round(r1_count/n*100, 2)}%)",
        "chunk_r3_count": f"{r3_count}/{n} ({round(r3_count/n*100, 2)}%)",
        "chunk_r5_count": f"{r5_count}/{n} ({round(r5_count/n*100, 2)}%)",
        "chunk_mrr": round(mrr, 4),
        "reproduction_match": bool(dense_hits_15 == 37 and r1_count == 19 and r3_count == 27 and r5_count == 35 and round(mrr, 4) == 0.6150),
        "query_evaluations": query_evals
    }

    with open(BASE_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(baseline_report, f, indent=2, ensure_ascii=False)

    print("\nDEV BASELINE REPRODUCTION SUMMARY:")
    print(f"  Dense R@15: {baseline_report['dense_r15_count']} (Target: 37/40 = 92.5%)")
    print(f"  Chunk R@1:  {baseline_report['chunk_r1_count']} (Target: 19/40 = 47.5%)")
    print(f"  Chunk R@3:  {baseline_report['chunk_r3_count']} (Target: 27/40 = 67.5%)")
    print(f"  Chunk R@5:  {baseline_report['chunk_r5_count']} (Target: 35/40 = 87.5%)")
    print(f"  Chunk MRR:  {baseline_report['chunk_mrr']} (Target: 0.6150)")
    print(f"  Exact Match Status: {'PASS' if baseline_report['reproduction_match'] else 'FAIL'}")

    # Phase 2: Failure Decomposition for Reranker Demotions on DEV
    reranker_demoted_queries = [q for q in query_evals if q["dense_hit_r15"] and not q["r5"]]
    print(f"\n========================================================")
    print(f"PHASE 2: DEV RERANKER FAILURE DECOMPOSITION ({len(reranker_demoted_queries)} queries)")
    print(f"========================================================")

    detailed_demotions = []
    for dq in reranker_demoted_queries:
        qid = dq["query_id"]
        gold_cids = dq["gold_chunk_ids"]
        gold_rank = dq["final_rerank_rank"]
        gold_score = dq["gold_score"]
        rank1_score = dq["rank1_score"]
        rank5_score = dq["rank5_score"]
        score_margin = rank5_score - gold_score

        top5_cids = dq["final_top5_cids"]
        top5_scores = dq["final_top5_scores"]

        competitors = []
        for cid, sc in zip(top5_cids, top5_scores):
            chk = chunks_by_id.get(cid, {})
            sid = chk.get("parent_source_id")
            heading = chk.get("section_heading", "Unknown")
            same_doc = (sid == dq["expected_source_id"])
            competitors.append({
                "chunk_id": cid,
                "parent_source_id": sid,
                "section_heading": heading,
                "score": round(sc, 4),
                "is_same_document": same_doc,
                "is_overview": cid.endswith("-HYB-000"),
                "is_substantive": not cid.endswith("-HYB-000")
            })

        print(f"\n[{qid}] ({dq['language_category']}) {dq['raw_query']}")
        print(f"  Gold CIDs: {gold_cids} | Dense Rank: {dq['dense_rank']} -> Final Rerank Rank: {gold_rank}")
        print(f"  Gold Score: {gold_score:.4f} | Rank 1 Score: {rank1_score:.4f} | Rank 5 Score: {rank5_score:.4f} | Margin: {score_margin:.4f}")
        print(f"  Top 5 Competitors:")
        for c in competitors:
            print(f"    - {c['chunk_id']} ({'SAME-DOC' if c['is_same_document'] else 'CROSS-DOC'} | {c['section_heading']}): score={c['score']}")

        detailed_demotions.append({
            "query_id": qid,
            "language_category": dq["language_category"],
            "raw_query": dq["raw_query"],
            "normalized_query": dq["normalized_query"],
            "expected_source_id": dq["expected_source_id"],
            "gold_chunk_ids": gold_cids,
            "dense_rank": dq["dense_rank"],
            "final_rerank_rank": gold_rank,
            "gold_score": round(gold_score, 4),
            "rank1_score": round(rank1_score, 4),
            "rank5_score": round(rank5_score, 4),
            "score_margin_vs_rank5": round(score_margin, 4),
            "top5_competitors": competitors
        })

    with open(DIAG_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(detailed_demotions, f, indent=2, ensure_ascii=False)

    print(f"\nSaved DEV failure decomposition to {DIAG_OUT_FILE}")

if __name__ == "__main__":
    main()
