"""
Gate 5.15 — Exact Single Locked Holdout Validation of the Overview-Debiased Retrieval Pipeline
Frozen Configuration: a79e7a0eca3e7617d2e87ef920ef916edfa680011ae3e8bbc906f29dfcb4f79e
"""

import json
import os
import sys
import time
import re
import hashlib
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

FROZEN_CONFIG_FILE = os.path.join(ROOT_DIR, "research", "gate_5_14_reranker_optimization", "frozen_candidate", "frozen_candidate_configuration.json")
BENCHMARK_FILE = os.path.join(ROOT_DIR, "research", "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
CHUNKS_FILE = os.path.join(ROOT_DIR, "research", "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(ROOT_DIR, "research", "gate_5_9_optimization", "chunk_gold_labels.json")

RESULTS_OUT_FILE = os.path.join(BASE_DIR, "evaluations", "gate_5_15_locked_holdout_results.json")
RANKINGS_OUT_FILE = os.path.join(BASE_DIR, "evaluations", "gate_5_15_exact_rankings.json")
UNSUPPORTED_OUT_FILE = os.path.join(BASE_DIR, "evaluations", "gate_5_15_unsupported_query_results.json")

EXPECTED_BENCHMARK_HASH = "7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81"
EXPECTED_CONFIG_HASH = "a79e7a0eca3e7617d2e87ef920ef916edfa680011ae3e8bbc906f29dfcb4f79e"

# Exact Frozen Normalization Rules from Gate 5.12 & Gate 5.14
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

def hash_file(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    print("="*80)
    print("GATE 5.15: SINGLE LOCKED HOLDOUT VALIDATION OF OVERVIEW-DEBIASED PIPELINE")
    print("="*80)

    # 1. Integrity Verification
    with open(FROZEN_CONFIG_FILE, "r", encoding="utf-8") as f:
        frozen_config = json.load(f)
    assert frozen_config.get("configuration_hash") == EXPECTED_CONFIG_HASH, "Config hash mismatch!"
    assert hash_file(BENCHMARK_FILE) == EXPECTED_BENCHMARK_HASH, "Benchmark hash mismatch!"
    print("[PASS] Configuration and Benchmark hashes verified.")

    # Parameters
    params = frozen_config["parameters"]
    assert params["query_normalization"]["enabled"] == True
    assert params["embedding_model"] == "intfloat/multilingual-e5-small"
    assert params["candidate_depth_k"] == 15
    assert params["reranker_model"] == "BAAI/bge-reranker-v2-m3"
    assert params["reranker_post_processing"]["overview_debiasing_enabled"] == True
    assert params["reranker_post_processing"]["overview_chunk_suffix"] == "-HYB-000"
    assert params["reranker_post_processing"]["overview_score_multiplier"] == 0.85
    assert params["final_top_k_context"] == 5
    print("[PASS] All runtime parameters match frozen specification exactly.")

    # Load Data
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    holdout_supported = [q for q in benchmark if q["benchmark_split"] == "TEST_HOLDOUT"]
    holdout_unsupported = [q for q in benchmark if q["benchmark_split"] in ("HARD_NEGATIVE", "OUT_OF_CORPUS")]

    assert len(holdout_supported) == 40, f"Expected 40 supported test queries, got {len(holdout_supported)}"
    assert len(holdout_unsupported) == 20, f"Expected 20 unsupported queries, got {len(holdout_unsupported)}"

    print(f"Loaded {len(chunks)} Chunks across Corpus.")
    print(f"Loaded {len(holdout_supported)} Supported TEST Queries and {len(holdout_unsupported)} Unsupported Queries.")

    # Initialize Models
    print("\nLoading models on CPU...")
    t0_load = time.time()
    dense_model = SentenceTransformer(params["embedding_model"], device="cpu")
    reranker = CrossEncoder(params["reranker_model"], device="cpu")
    print(f"Models loaded in {time.time() - t0_load:.2f}s")

    # Encode Passages
    print("Encoding passages for dense index...")
    t0_enc = time.time()
    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)
    print(f"68 Passages encoded in {time.time() - t0_enc:.2f}s")

    # Execute Holdout Evaluation for Supported Queries
    print("\n" + "="*80)
    print("EXECUTING EXACT SINGLE LOCKED HOLDOUT EVALUATION (N=40)")
    print("="*80)

    supported_eval_results = []
    exact_rankings_list = []

    for q in holdout_supported:
        qid = q["query_id"]
        raw_q = q["query_text"]
        norm_q = normalize_query_text(raw_q)
        lang = q["language_category"]
        expected_sid = q["expected_source_id"]
        gold = gold_labels[qid]
        acceptable_cids = gold["gold_chunk_ids"]
        target_topic = gold["target_topic"]

        # 1. Dense Query Encoding & Top-15 Retrieval
        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:15]
        dense_top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
        dense_top15_sids = [chunks[idx]["parent_source_id"] for idx in top15_indices]
        dense_top15_scores = [float(dense_scores[idx]) for idx in top15_indices]

        # 2. Cross-Encoder Scoring of Top-15 Candidate Pairs
        pairs = [(norm_q, chunks[idx]["text"]) for idx in top15_indices]
        raw_ce_scores = reranker.predict(pairs)

        # 3. Same-Document Overview Debiasing (0.85x factor on overview chunk 000)
        adj_scores = []
        for i, idx in enumerate(top15_indices):
            cid = dense_top15_cids[i]
            base_score = float(raw_ce_scores[i])
            if cid.endswith("-HYB-000"):
                final_s = base_score * 0.85
            else:
                final_s = base_score
            adj_scores.append(final_s)

        adj_scores = np.array(adj_scores)
        rerank_order = np.argsort(-adj_scores)

        rerank_top15_cids = [dense_top15_cids[i] for i in rerank_order]
        rerank_top15_sids = [dense_top15_sids[i] for i in rerank_order]
        rerank_top15_raw_ce = [float(raw_ce_scores[i]) for i in rerank_order]
        rerank_top15_adj_scores = [float(adj_scores[i]) for i in rerank_order]

        final_top5_cids = rerank_top15_cids[:5]
        final_top5_sids = rerank_top15_sids[:5]
        final_top5_scores = rerank_top15_adj_scores[:5]

        # Metric evaluations
        # Dense candidate recall
        dense_hits = [cid in acceptable_cids for cid in dense_top15_cids]
        dense_r1 = dense_hits[0]
        dense_r3 = any(dense_hits[:3])
        dense_r5 = any(dense_hits[:5])
        dense_r10 = any(dense_hits[:10])
        dense_r15 = any(dense_hits[:15])
        dense_rank = (dense_hits.index(True) + 1) if any(dense_hits) else 0

        # Final chunk-level recall
        r_hits = [cid in acceptable_cids for cid in final_top5_cids]
        r_r1 = r_hits[0]
        r_r3 = any(r_hits[:3])
        r_r5 = any(r_hits[:5])

        all_r_hits = [cid in acceptable_cids for cid in rerank_top15_cids]
        r_rank = (all_r_hits.index(True) + 1) if any(all_r_hits) else 0

        # Source-level recall
        src_dense_hits = [sid == expected_sid for sid in dense_top15_sids]
        src_r_hits = [sid == expected_sid for sid in final_top5_sids]

        src_dense_r1 = src_dense_hits[0]
        src_dense_r5 = any(src_dense_hits[:5])
        src_r_r1 = src_r_hits[0]
        src_r_r5 = any(src_r_hits[:5])

        # Evidence Availability Category
        if r_r1:
            avail_cat = "TOP1_CORRECT"
        elif r_r3:
            avail_cat = "TOP1_WRONG_BUT_TOP3_HAS_GOLD"
        elif r_r5:
            avail_cat = "TOP3_WRONG_BUT_TOP5_HAS_GOLD"
        else:
            avail_cat = "GOLD_ABSENT_FROM_TOP5"

        # Failure Taxonomy Category
        if not r_r5:
            if dense_r15:
                fail_cat = "GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK"
            else:
                fail_cat = "GOLD_OUTSIDE_DENSE15"
        else:
            fail_cat = "NONE_SUCCESS"

        eval_record = {
            "query_id": qid,
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "target_topic": target_topic,
            "language_category": lang,
            "expected_source_id": expected_sid,
            "gold_chunk_ids": acceptable_cids,
            "dense_top15_cids": dense_top15_cids,
            "final_top5_cids": final_top5_cids,
            "final_top5_scores": final_top5_scores,
            "chunk_level": {
                "dense_r15": dense_r15,
                "dense_rank": dense_rank,
                "rerank_r1": r_r1,
                "rerank_r3": r_r3,
                "rerank_r5": r_r5,
                "rerank_rank": r_rank
            },
            "source_level": {
                "dense_r1": src_dense_r1,
                "dense_r5": src_dense_r5,
                "rerank_r1": src_r_r1,
                "rerank_r5": src_r_r5
            },
            "evidence_availability": avail_cat,
            "failure_category": fail_cat
        }
        supported_eval_results.append(eval_record)

        exact_rankings_list.append({
            "query_id": qid,
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "language_category": lang,
            "expected_source_id": expected_sid,
            "gold_chunk_ids": acceptable_cids,
            "dense_top15_ranking": [
                {"rank": i+1, "chunk_id": dense_top15_cids[i], "score": dense_top15_scores[i], "is_gold": dense_top15_cids[i] in acceptable_cids}
                for i in range(15)
            ],
            "rerank_top15_ranking": [
                {"rank": i+1, "chunk_id": rerank_top15_cids[i], "raw_ce_score": rerank_top15_raw_ce[i], "debiased_score": rerank_top15_adj_scores[i], "is_gold": rerank_top15_cids[i] in acceptable_cids}
                for i in range(15)
            ],
            "final_top5_context": final_top5_cids,
            "gold_in_top5": r_r5,
            "gold_rank_final": r_rank,
            "evidence_availability": avail_cat,
            "failure_category": fail_cat
        })

    # Evaluate Unsupported Queries (12 HN + 8 OOC)
    print("\nExecuting Unsupported Query Safety Evaluation (N=20)...")
    unsupported_eval_results = []
    for q in holdout_unsupported:
        qid = q["query_id"]
        raw_q = q["query_text"]
        norm_q = normalize_query_text(raw_q)
        lang = q["language_category"]
        q_type = q["query_type"]
        split = q["benchmark_split"]

        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:15]
        dense_top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]

        pairs = [(norm_q, chunks[idx]["text"]) for idx in top15_indices]
        raw_ce_scores = reranker.predict(pairs)

        adj_scores = []
        for i, idx in enumerate(top15_indices):
            cid = dense_top15_cids[i]
            base_score = float(raw_ce_scores[i])
            if cid.endswith("-HYB-000"):
                final_s = base_score * 0.85
            else:
                final_s = base_score
            adj_scores.append(final_s)

        adj_scores = np.array(adj_scores)
        rerank_order = np.argsort(-adj_scores)

        unsupported_eval_results.append({
            "query_id": qid,
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "language_category": lang,
            "query_type": q_type,
            "benchmark_split": split,
            "dense_top1_cid": dense_top15_cids[0],
            "dense_top1_score": float(dense_scores[top15_indices[0]]),
            "rerank_top1_cid": dense_top15_cids[rerank_order[0]],
            "rerank_top1_score": float(adj_scores[rerank_order[0]]),
            "rerank_top5_cids": [dense_top15_cids[i] for i in rerank_order[:5]],
            "rerank_top5_scores": [float(adj_scores[i]) for i in rerank_order[:5]]
        })

    # Aggregate Computations
    n = len(supported_eval_results)
    d_r15 = sum(1 for r in supported_eval_results if r["chunk_level"]["dense_r15"])
    r_r1 = sum(1 for r in supported_eval_results if r["chunk_level"]["rerank_r1"])
    r_r3 = sum(1 for r in supported_eval_results if r["chunk_level"]["rerank_r3"])
    r_r5 = sum(1 for r in supported_eval_results if r["chunk_level"]["rerank_r5"])
    r_mrr = sum(1.0 / r["chunk_level"]["rerank_rank"] for r in supported_eval_results if r["chunk_level"]["rerank_rank"] > 0) / n

    src_r1 = sum(1 for r in supported_eval_results if r["source_level"]["rerank_r1"])
    src_r5 = sum(1 for r in supported_eval_results if r["source_level"]["rerank_r5"])

    avail_counts = {
        "TOP1_CORRECT": sum(1 for r in supported_eval_results if r["evidence_availability"] == "TOP1_CORRECT"),
        "TOP1_WRONG_BUT_TOP3_HAS_GOLD": sum(1 for r in supported_eval_results if r["evidence_availability"] == "TOP1_WRONG_BUT_TOP3_HAS_GOLD"),
        "TOP3_WRONG_BUT_TOP5_HAS_GOLD": sum(1 for r in supported_eval_results if r["evidence_availability"] == "TOP3_WRONG_BUT_TOP5_HAS_GOLD"),
        "GOLD_ABSENT_FROM_TOP5": sum(1 for r in supported_eval_results if r["evidence_availability"] == "GOLD_ABSENT_FROM_TOP5")
    }

    fail_counts = {
        "GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK": sum(1 for r in supported_eval_results if r["failure_category"] == "GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK"),
        "GOLD_OUTSIDE_DENSE15": sum(1 for r in supported_eval_results if r["failure_category"] == "GOLD_OUTSIDE_DENSE15")
    }

    language_breakdown = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        l_subs = [r for r in supported_eval_results if r["language_category"] == lang]
        ln = len(l_subs)
        l_d_r15 = sum(1 for r in l_subs if r["chunk_level"]["dense_r15"])
        l_r1 = sum(1 for r in l_subs if r["chunk_level"]["rerank_r1"])
        l_r3 = sum(1 for r in l_subs if r["chunk_level"]["rerank_r3"])
        l_r5 = sum(1 for r in l_subs if r["chunk_level"]["rerank_r5"])
        l_mrr = sum(1.0 / r["chunk_level"]["rerank_rank"] for r in l_subs if r["chunk_level"]["rerank_rank"] > 0) / ln

        language_breakdown[lang] = {
            "n": ln,
            "dense_top15_count": f"{l_d_r15}/{ln}",
            "dense_top15_pct": round(l_d_r15 / ln * 100, 2),
            "final_chunk_r1_count": f"{l_r1}/{ln}",
            "final_chunk_r1_pct": round(l_r1 / ln * 100, 2),
            "final_chunk_r3_count": f"{l_r3}/{ln}",
            "final_chunk_r3_pct": round(l_r3 / ln * 100, 2),
            "final_chunk_r5_count": f"{l_r5}/{ln}",
            "final_chunk_r5_pct": round(l_r5 / ln * 100, 2),
            "final_chunk_mrr": round(l_mrr, 4)
        }

    # Save Exact Rankings
    with open(RANKINGS_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(exact_rankings_list, f, indent=2, ensure_ascii=False)

    # Save Unsupported Results
    unsupported_summary = {
        "total_unsupported_queries": len(unsupported_eval_results),
        "hard_negatives_count": len([r for r in unsupported_eval_results if r["benchmark_split"] == "HARD_NEGATIVE"]),
        "out_of_corpus_count": len([r for r in unsupported_eval_results if r["benchmark_split"] == "OUT_OF_CORPUS"]),
        "max_reranker_score": max(r["rerank_top1_score"] for r in unsupported_eval_results),
        "min_reranker_score": min(r["rerank_top1_score"] for r in unsupported_eval_results),
        "mean_reranker_score": sum(r["rerank_top1_score"] for r in unsupported_eval_results) / len(unsupported_eval_results),
        "queries": unsupported_eval_results
    }
    with open(UNSUPPORTED_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(unsupported_summary, f, indent=2, ensure_ascii=False)

    # Compile Final Results
    final_results = {
        "gate": "GATE_5.15",
        "frozen_configuration_hash": EXPECTED_CONFIG_HASH,
        "frozen_benchmark_hash": EXPECTED_BENCHMARK_HASH,
        "strategy_name": "STRATEGY_3_SAME_DOC_OVERVIEW_DEBIASING",
        "sample_sizes": {
            "supported_holdout_queries_n": n,
            "unsupported_queries_n": len(unsupported_eval_results)
        },
        "candidate_retrieval": {
            "dense_top15_count": f"{d_r15}/{n}",
            "dense_top15_pct": round(d_r15 / n * 100, 2),
            "gold_present_in_dense15": d_r15,
            "gold_absent_from_dense15": n - d_r15
        },
        "final_chunk_retrieval": {
            "r1_count": f"{r_r1}/{n}",
            "r1_pct": round(r_r1 / n * 100, 2),
            "r3_count": f"{r_r3}/{n}",
            "r3_pct": round(r_r3 / n * 100, 2),
            "r5_count": f"{r_r5}/{n}",
            "r5_pct": round(r_r5 / n * 100, 2),
            "mrr": round(r_mrr, 4)
        },
        "source_level_retrieval": {
            "source_r1_count": f"{src_r1}/{n}",
            "source_r1_pct": round(src_r1 / n * 100, 2),
            "source_r5_count": f"{src_r5}/{n}",
            "source_r5_pct": round(src_r5 / n * 100, 2)
        },
        "evidence_availability_categories": {
            "TOP1_CORRECT": f"{avail_counts['TOP1_CORRECT']}/{n} ({round(avail_counts['TOP1_CORRECT']/n*100, 2)}%)",
            "TOP1_WRONG_BUT_TOP3_HAS_GOLD": f"{avail_counts['TOP1_WRONG_BUT_TOP3_HAS_GOLD']}/{n} ({round(avail_counts['TOP1_WRONG_BUT_TOP3_HAS_GOLD']/n*100, 2)}%)",
            "TOP3_WRONG_BUT_TOP5_HAS_GOLD": f"{avail_counts['TOP3_WRONG_BUT_TOP5_HAS_GOLD']}/{n} ({round(avail_counts['TOP3_WRONG_BUT_TOP5_HAS_GOLD']/n*100, 2)}%)",
            "GOLD_ABSENT_FROM_TOP5": f"{avail_counts['GOLD_ABSENT_FROM_TOP5']}/{n} ({round(avail_counts['GOLD_ABSENT_FROM_TOP5']/n*100, 2)}%)"
        },
        "failure_decomposition": {
            "GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK": f"{fail_counts['GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK']}/{n} ({round(fail_counts['GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK']/n*100, 2)}%)",
            "GOLD_OUTSIDE_DENSE15": f"{fail_counts['GOLD_OUTSIDE_DENSE15']}/{n} ({round(fail_counts['GOLD_OUTSIDE_DENSE15']/n*100, 2)}%)"
        },
        "language_breakdown": language_breakdown,
        "unsupported_queries_safety": {
            "total_unsupported_queries": len(unsupported_eval_results),
            "max_reranker_score": unsupported_summary["max_reranker_score"],
            "min_reranker_score": unsupported_summary["min_reranker_score"],
            "mean_reranker_score": unsupported_summary["mean_reranker_score"]
        }
    }

    with open(RESULTS_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)

    print("\n" + "="*80)
    print("GATE 5.15 SINGLE LOCKED HOLDOUT RESULTS SUMMARY")
    print("="*80)
    print(f"Dense Candidate Recall@15: {final_results['candidate_retrieval']['dense_top15_count']} ({final_results['candidate_retrieval']['dense_top15_pct']}%)")
    print(f"Final Chunk Recall@1:      {final_results['final_chunk_retrieval']['r1_count']} ({final_results['final_chunk_retrieval']['r1_pct']}%)")
    print(f"Final Chunk Recall@3:      {final_results['final_chunk_retrieval']['r3_count']} ({final_results['final_chunk_retrieval']['r3_pct']}%)")
    print(f"Final Chunk Recall@5:      {final_results['final_chunk_retrieval']['r5_count']} ({final_results['final_chunk_retrieval']['r5_pct']}%)")
    print(f"Final Chunk MRR:           {final_results['final_chunk_retrieval']['mrr']}")
    print(f"Source-Level Recall@1:     {final_results['source_level_retrieval']['source_r1_count']} ({final_results['source_level_retrieval']['source_r1_pct']}%)")
    print(f"Source-Level Recall@5:     {final_results['source_level_retrieval']['source_r5_count']} ({final_results['source_level_retrieval']['source_r5_pct']}%)")

    print("\nEvidence Availability Breakdown:")
    for k, v in final_results["evidence_availability_categories"].items():
        print(f"  {k}: {v}")

    print("\nFailure Decomposition:")
    for k, v in final_results["failure_decomposition"].items():
        print(f"  {k}: {v}")

    print("\nLanguage Breakdown:")
    for lang, lm in language_breakdown.items():
        print(f"  {lang} (N={lm['n']}): Dense Top-15={lm['dense_top15_count']}, Final R@1={lm['final_chunk_r1_count']}, Final R@5={lm['final_chunk_r5_count']}, MRR={lm['final_chunk_mrr']}")

    print(f"\nArtifacts Saved:")
    print(f"  - {RESULTS_OUT_FILE}")
    print(f"  - {RANKINGS_OUT_FILE}")
    print(f"  - {UNSUPPORTED_OUT_FILE}")

if __name__ == "__main__":
    main()
