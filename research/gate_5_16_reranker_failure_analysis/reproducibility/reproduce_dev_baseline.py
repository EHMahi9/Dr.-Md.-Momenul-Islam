"""
Gate 5.16 — Phase 1: DEV Baseline Reproduction & Verification
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
FROZEN_CONFIG_FILE = os.path.join(RESEARCH_DIR, "gate_5_14_reranker_optimization", "frozen_candidate", "frozen_candidate_configuration.json")
REPRO_OUT_FILE = os.path.join(BASE_DIR, "dev_reproduction_verification.json")

# Normalization mappings
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
    print("GATE 5.16 — PHASE 1: DEV BASELINE REPRODUCTION & VERIFICATION")
    print("="*80)

    with open(FROZEN_CONFIG_FILE, "r", encoding="utf-8") as f:
        frozen_config = json.load(f)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    dev_queries = [q for q in benchmark if q["benchmark_split"] == "DEV"]
    assert len(dev_queries) == 40, f"Expected 40 DEV queries, found {len(dev_queries)}"

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    print("Loading models...")
    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    query_results = []

    for q in dev_queries:
        qid = q["query_id"]
        raw_q = q["query_text"]
        norm_q = normalize_query_text(raw_q)
        gold = gold_labels[qid]
        acceptable_cids = gold["gold_chunk_ids"]
        expected_sid = q["expected_source_id"]

        # Dense retrieval
        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:15]
        dense_top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
        dense_top15_scores = [float(dense_scores[idx]) for idx in top15_indices]

        # Reranker scoring
        pairs = [(norm_q, chunks[idx]["text"]) for idx in top15_indices]
        raw_ce_scores = reranker.predict(pairs)

        # 0.85x Overview debiasing
        adj_scores = []
        for i, idx in enumerate(top15_indices):
            cid = dense_top15_cids[i]
            base_s = float(raw_ce_scores[i])
            if cid.endswith("-HYB-000"):
                adj_scores.append(base_s * 0.85)
            else:
                adj_scores.append(base_s)

        adj_scores = np.array(adj_scores)
        rerank_order = np.argsort(-adj_scores)

        rerank_cids = [dense_top15_cids[i] for i in rerank_order]
        rerank_scores = [float(adj_scores[i]) for i in rerank_order]

        top5_cids = rerank_cids[:5]
        top5_scores = rerank_scores[:5]

        # Hits
        dense_hits = [cid in acceptable_cids for cid in dense_top15_cids]
        dense_r15 = any(dense_hits)
        dense_rank = (dense_hits.index(True) + 1) if dense_r15 else 0

        r_hits = [cid in acceptable_cids for cid in top5_cids]
        r1 = r_hits[0]
        r3 = any(r_hits[:3])
        r5 = any(r_hits[:5])

        all_r_hits = [cid in acceptable_cids for cid in rerank_cids]
        rerank_rank = (all_r_hits.index(True) + 1) if any(all_r_hits) else 0

        query_results.append({
            "query_id": qid,
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "language_category": q["language_category"],
            "expected_source_id": expected_sid,
            "gold_chunk_ids": acceptable_cids,
            "dense_top15_cids": dense_top15_cids,
            "dense_top15_scores": dense_top15_scores,
            "rerank_top15_cids": rerank_cids,
            "rerank_top15_scores": rerank_scores,
            "final_top5_cids": top5_cids,
            "final_top5_scores": top5_scores,
            "dense_r15": dense_r15,
            "dense_rank": dense_rank,
            "rerank_r1": r1,
            "rerank_r3": r3,
            "rerank_r5": r5,
            "rerank_rank": rerank_rank
        })

    n = len(query_results)
    d_r15 = sum(1 for r in query_results if r["dense_r15"])
    r_r1 = sum(1 for r in query_results if r["rerank_r1"])
    r_r3 = sum(1 for r in query_results if r["rerank_r3"])
    r_r5 = sum(1 for r in query_results if r["rerank_r5"])
    mrr = sum(1.0 / r["rerank_rank"] for r in query_results if r["rerank_rank"] > 0) / n

    expected_metrics = frozen_config["dev_benchmark_metrics"]

    repro_checks = {
        "candidate_pool_r15": {
            "expected": expected_metrics["candidate_pool_r15"],
            "actual": f"{d_r15}/{n} ({d_r15/n*100:.2f}%)",
            "match": f"{d_r15}/{n} ({d_r15/n*100:.2f}%)" == expected_metrics["candidate_pool_r15"]
        },
        "chunk_recall_at_1": {
            "expected": expected_metrics["chunk_recall_at_1"],
            "actual": f"{r_r1}/{n} ({r_r1/n*100:.2f}%)",
            "match": f"{r_r1}/{n} ({r_r1/n*100:.2f}%)" == expected_metrics["chunk_recall_at_1"]
        },
        "chunk_recall_at_3": {
            "expected": expected_metrics["chunk_recall_at_3"],
            "actual": f"{r_r3}/{n} ({r_r3/n*100:.2f}%)",
            "match": f"{r_r3}/{n} ({r_r3/n*100:.2f}%)" == expected_metrics["chunk_recall_at_3"]
        },
        "chunk_recall_at_5": {
            "expected": expected_metrics["chunk_recall_at_5"],
            "actual": f"{r_r5}/{n} ({r_r5/n*100:.2f}%)",
            "match": f"{r_r5}/{n} ({r_r5/n*100:.2f}%)" == expected_metrics["chunk_recall_at_5"]
        },
        "mrr": {
            "expected": expected_metrics["mrr"],
            "actual": round(mrr, 4),
            "match": round(mrr, 4) == expected_metrics["mrr"]
        }
    }

    all_matched = all(v["match"] for v in repro_checks.values())
    status = "PASS" if all_matched else "FAIL"

    repro_output = {
        "gate": "GATE_5.16",
        "phase": "PHASE_1_DEV_REPRODUCIBILITY",
        "timestamp": "2026-08-22T20:50:00+06:00",
        "reproduction_status": status,
        "metrics_verification": repro_checks,
        "dev_queries_results": query_results
    }

    with open(REPRO_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(repro_output, f, indent=2, ensure_ascii=False)

    print(f"\nReproduction Status: {status}")
    for k, v in repro_checks.items():
        print(f"  {k}: Expected={v['expected']} | Actual={v['actual']} | Match={v['match']}")
    print(f"\nSaved reproduction verification to {REPRO_OUT_FILE}")

    if not all_matched:
        print("[FAIL] DEV baseline reproduction failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
