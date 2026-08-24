"""
Gate 5.14 — Phase 1: In-Depth Diagnostic Analysis of Cross-Encoder Reranker Behavior on DEV (N=40)
"""

import json
import os
import sys
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
import hashlib
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
BENCHMARK_FILE = os.path.join(ROOT_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
CHUNKS_FILE = os.path.join(ROOT_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(ROOT_DIR, "gate_5_9_optimization", "chunk_gold_labels.json")
DIAG_OUT_FILE = os.path.join(BASE_DIR, "dev_reranker_diagnostics.json")

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
    print("Loading DEV benchmark & models for Reranker Diagnostics...")
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]
    assert len(dev_queries) == 40, f"Expected 40 DEV queries, got {len(dev_queries)}"

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    diagnostics_list = []
    overview_demotion_count = 0
    raw_vs_norm_rerank_comparison = []

    for q in dev_queries:
        qid = q["query_id"]
        raw_q = q["query_text"]
        norm_q = normalize_query_text(raw_q)
        gold = gold_labels[qid]
        acceptable_cids = gold["gold_chunk_ids"]
        expected_sid = q["expected_source_id"]

        # Dense Top-15
        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-scores)[:15]
        dense_top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
        dense_hits = [cid in acceptable_cids for cid in dense_top15_cids]
        gold_in_dense15 = any(dense_hits)
        dense_gold_rank = (dense_hits.index(True) + 1) if gold_in_dense15 else 0

        # Rerank with Normalized Query
        pairs_norm = [(norm_q, chunks[idx]["text"]) for idx in top15_indices]
        scores_norm = reranker.predict(pairs_norm)
        order_norm = np.argsort(-scores_norm)
        rerank_norm_cids = [dense_top15_cids[i] for i in order_norm]
        rerank_norm_scores = [float(scores_norm[i]) for i in order_norm]
        r_hits_norm = [cid in acceptable_cids for cid in rerank_norm_cids]
        r_gold_rank_norm = (r_hits_norm.index(True) + 1) if any(r_hits_norm) else 0

        # Rerank with Raw Query
        pairs_raw = [(raw_q, chunks[idx]["text"]) for idx in top15_indices]
        scores_raw = reranker.predict(pairs_raw)
        order_raw = np.argsort(-scores_raw)
        rerank_raw_cids = [dense_top15_cids[i] for i in order_raw]
        rerank_raw_scores = [float(scores_raw[i]) for i in order_raw]
        r_hits_raw = [cid in acceptable_cids for cid in rerank_raw_cids]
        r_gold_rank_raw = (r_hits_raw.index(True) + 1) if any(r_hits_raw) else 0

        # Check if Overview Chunk (index 0) beat specific gold chunk
        overview_cid = f"{expected_sid}-HYB-000"
        overview_in_candidates = overview_cid in dense_top15_cids
        overview_rank = (rerank_norm_cids.index(overview_cid) + 1) if overview_cid in rerank_norm_cids else 0
        overview_score = rerank_norm_scores[rerank_norm_cids.index(overview_cid)] if overview_cid in rerank_norm_cids else None

        gold_cid = acceptable_cids[0]
        gold_score = rerank_norm_scores[rerank_norm_cids.index(gold_cid)] if gold_cid in rerank_norm_cids else None

        is_overview_demotion = False
        if gold_in_dense15 and gold_cid != overview_cid and overview_in_candidates:
            if overview_rank < r_gold_rank_norm:
                is_overview_demotion = True
                overview_demotion_count += 1

        diagnostics_list.append({
            "query_id": qid,
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "language_category": q["language_category"],
            "expected_source_id": expected_sid,
            "gold_chunk_ids": acceptable_cids,
            "gold_in_dense15": gold_in_dense15,
            "dense_gold_rank": dense_gold_rank,
            "rerank_norm": {
                "gold_rank": r_gold_rank_norm,
                "in_top5": (r_gold_rank_norm <= 5 and r_gold_rank_norm > 0),
                "gold_score": gold_score,
                "top1_cid": rerank_norm_cids[0],
                "top1_score": rerank_norm_scores[0],
                "top5_cids": rerank_norm_cids[:5]
            },
            "rerank_raw": {
                "gold_rank": r_gold_rank_raw,
                "in_top5": (r_gold_rank_raw <= 5 and r_gold_rank_raw > 0),
                "top1_cid": rerank_raw_cids[0],
                "top1_score": rerank_raw_scores[0]
            },
            "overview_analysis": {
                "overview_cid": overview_cid,
                "overview_in_candidates": overview_in_candidates,
                "overview_rank": overview_rank,
                "overview_score": overview_score,
                "is_overview_demotion": is_overview_demotion
            }
        })

    # Summary Statistics
    total_q = len(dev_queries)
    dense_r15_hits = sum(1 for d in diagnostics_list if d["gold_in_dense15"])
    norm_r5_hits = sum(1 for d in diagnostics_list if d["rerank_norm"]["in_top5"])
    raw_r5_hits = sum(1 for d in diagnostics_list if d["rerank_raw"]["in_top5"])

    summary = {
        "n_dev_queries": total_q,
        "dense_top15_recall": f"{dense_r15_hits}/{total_q} ({dense_r15_hits/total_q*100:.1f}%)",
        "norm_query_rerank_r5": f"{norm_r5_hits}/{total_q} ({norm_r5_hits/total_q*100:.1f}%)",
        "raw_query_rerank_r5": f"{raw_r5_hits}/{total_q} ({raw_r5_hits/total_q*100:.1f}%)",
        "overview_demotion_events": f"{overview_demotion_count}/{total_q} ({overview_demotion_count/total_q*100:.1f}%)",
        "diagnostics": diagnostics_list
    }

    with open(DIAG_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "="*80)
    print("GATE 5.14 PHASE 1: DEV RERANKER DIAGNOSTICS SUMMARY")
    print("="*80)
    print(f"Dense Candidate Recall@15: {summary['dense_top15_recall']}")
    print(f"Norm Query Rerank Recall@5: {summary['norm_query_rerank_r5']}")
    print(f"Raw Query Rerank Recall@5:  {summary['raw_query_rerank_r5']}")
    print(f"Overview Demotion Events:   {summary['overview_demotion_events']}")
    print(f"Saved diagnostics to {DIAG_OUT_FILE}")

if __name__ == "__main__":
    main()
