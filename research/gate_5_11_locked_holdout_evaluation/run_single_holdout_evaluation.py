"""
Gate 5.11 — Single Locked Holdout Re-Evaluation of the Frozen Evidence Retrieval Configuration
Executes the frozen K=15 pipeline once on the untouched 40 locked TEST queries.
"""

import json
import os
import sys
import time
import hashlib
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
FROZEN_CONFIG_FILE = os.path.join(ROOT_DIR, "gate_5_10_evidence_retrieval_improvement", "frozen_candidate", "frozen_candidate_configuration.json")
BENCHMARK_FILE = os.path.join(ROOT_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
CHUNKS_FILE = os.path.join(ROOT_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
GOLD_LABELS_FILE = os.path.join(ROOT_DIR, "gate_5_9_optimization", "chunk_gold_labels.json")
EVAL_OUT_FILE = os.path.join(BASE_DIR, "evaluations", "gate_5_11_locked_holdout_results.json")

EXPECTED_BENCHMARK_HASH = "7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81"
EXPECTED_CONFIG_HASH = "a58194bf0fd52871a3bdd10945609c4132c09a88fb8f6a0771ac294b30edaa1f"

def hash_file(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def hash_dict(d: dict) -> str:
    s = json.dumps(d, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def main():
    print("="*80)
    print("GATE 5.11 — VERIFYING FROZEN CONFIGURATION AND LOCKED HOLDOUT ARTIFACTS")
    print("="*80)

    # 1. Verify Benchmark Hash
    actual_benchmark_hash = hash_file(BENCHMARK_FILE)
    print(f"Benchmark File: {BENCHMARK_FILE}")
    print(f"Benchmark Hash: {actual_benchmark_hash}")
    if actual_benchmark_hash != EXPECTED_BENCHMARK_HASH:
        print(f"ERROR: Benchmark hash mismatch! Expected {EXPECTED_BENCHMARK_HASH}, got {actual_benchmark_hash}")
        sys.exit(1)
    print("[PASS] Benchmark hash verified.")

    # 2. Verify Frozen Configuration Hash
    with open(FROZEN_CONFIG_FILE, "r", encoding="utf-8") as f:
        frozen_config = json.load(f)
    actual_config_hash = frozen_config.get("configuration_hash")
    print(f"Frozen Config Hash: {actual_config_hash}")
    if actual_config_hash != EXPECTED_CONFIG_HASH:
        print(f"ERROR: Config hash mismatch! Expected {EXPECTED_CONFIG_HASH}, got {actual_config_hash}")
        sys.exit(1)
    print("[PASS] Frozen candidate configuration hash verified.")

    # Verify Configuration Parameters
    params = frozen_config["parameters"]
    assert params["embedding_model"] == "intfloat/multilingual-e5-small"
    assert params["reranker_model"] == "BAAI/bge-reranker-v2-m3"
    assert params["chunking_algorithm"] == "HYBRID_600"
    assert params["candidate_depth_k"] == 15
    assert params["use_bm25_rrf"] == False
    assert params["passage_representation"] == "standard"
    print("[PASS] All runtime parameters match frozen specification.")

    # Load artifacts
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunk_map = {c["chunk_id"]: c for c in chunks}

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    holdout_queries = [q for q in benchmark if q["benchmark_split"] == "TEST_HOLDOUT"]

    with open(GOLD_LABELS_FILE, "r", encoding="utf-8") as f:
        gold_labels = json.load(f)

    print(f"Total Chunks in Index: {len(chunks)}")
    print(f"Total TEST_HOLDOUT Queries: {len(holdout_queries)} (40 supported + 10 unsupported)")

    # Initialize models
    print("\nLoading models on CPU...")
    dense_model = SentenceTransformer(params["embedding_model"], device="cpu")
    reranker = CrossEncoder(params["reranker_model"], device="cpu")

    # Encode passages
    print("Encoding passages...")
    t0_enc_passages = time.time()
    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)
    t_enc_passages = time.time() - t0_enc_passages
    print(f"Passages encoded in {t_enc_passages:.2f}s")

    # Evaluate Holdout Queries
    print("\n" + "="*80)
    print("EXECUTING SINGLE LOCKED HOLDOUT EVALUATION (Candidate Depth K=15)")
    print("="*80)

    supported_eval_results = []
    unsupported_eval_results = []

    total_query_enc_time = 0.0
    total_dense_search_time = 0.0
    total_rerank_time = 0.0

    for q in holdout_queries:
        qid = q["query_id"]
        q_text = q["query_text"]
        lang = q["language_category"]
        expected_sid = q["expected_source_id"]
        is_supported = (expected_sid != "NONE")

        # 1. Query Encoding
        t0_q_enc = time.time()
        q_emb = dense_model.encode([f"query: {q_text}"], normalize_embeddings=True)
        t_q_enc = time.time() - t0_q_enc
        total_query_enc_time += t_q_enc

        # 2. Dense Search
        t0_dense = time.time()
        scores = np.dot(q_emb, chunk_embeddings.T)[0]
        ranked_indices = np.argsort(-scores)
        top15_indices = ranked_indices[:15]
        dense_top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
        dense_top15_sids = [chunks[idx]["parent_source_id"] for idx in top15_indices]
        t_dense = time.time() - t0_dense
        total_dense_search_time += t_dense

        # 3. Cross-Encoder Reranking of Top-15 candidates
        t0_rerank = time.time()
        pairs = [(q_text, chunks[idx]["text"]) for idx in top15_indices]
        r_scores = reranker.predict(pairs)
        r_order = np.argsort(-r_scores)
        r_top15_cids = [dense_top15_cids[idx] for idx in r_order]
        r_top15_sids = [dense_top15_sids[idx] for idx in r_order]
        r_top15_scores = [float(r_scores[idx]) for idx in r_order]
        t_rerank = time.time() - t0_rerank
        total_rerank_time += t_rerank

        # Final Top-5 context selection
        final_top5_cids = r_top15_cids[:5]
        final_top5_sids = r_top15_sids[:5]
        final_top5_scores = r_top15_scores[:5]

        if not is_supported:
            unsupported_eval_results.append({
                "query_id": qid,
                "query_text": q_text,
                "language_category": lang,
                "expected_source_id": expected_sid,
                "dense_top1_cid": dense_top15_cids[0],
                "dense_top1_sid": dense_top15_sids[0],
                "dense_top1_score": float(scores[top15_indices[0]]),
                "r_top1_cid": final_top5_cids[0],
                "r_top1_sid": final_top5_sids[0],
                "r_top1_score": final_top5_scores[0],
                "r_top5_cids": final_top5_cids,
                "r_top5_scores": final_top5_scores
            })
            continue

        # Supported query chunk evaluation
        gold = gold_labels[qid]
        acceptable_cids = gold["gold_chunk_ids"]
        target_topic = gold["target_topic"]

        # Dense candidate recall
        dense_hits = [cid in acceptable_cids for cid in dense_top15_cids]
        dense_r1 = dense_hits[0]
        dense_r3 = any(dense_hits[:3])
        dense_r5 = any(dense_hits[:5])
        dense_r10 = any(dense_hits[:10])
        dense_r15 = any(dense_hits[:15])
        dense_rank = (dense_hits.index(True) + 1) if any(dense_hits) else 0

        # Reranked evidence recall
        r_hits = [cid in acceptable_cids for cid in final_top5_cids]
        r_r1 = r_hits[0]
        r_r3 = any(r_hits[:3])
        r_r5 = any(r_hits[:5])
        r_rank = (r_hits.index(True) + 1) if any(r_hits) else 0

        # Source-level evaluation
        src_dense_hits = [sid == expected_sid for sid in dense_top15_sids]
        src_r_hits = [sid == expected_sid for sid in final_top5_sids]

        src_dense_r1 = src_dense_hits[0]
        src_dense_r3 = any(src_dense_hits[:3])
        src_dense_r5 = any(src_dense_hits[:5])
        src_dense_rank = (src_dense_hits.index(True) + 1) if any(src_dense_hits) else 0

        src_r_r1 = src_r_hits[0]
        src_r_r3 = any(src_r_hits[:3])
        src_r_r5 = any(src_r_hits[:5])
        src_r_rank = (src_r_hits.index(True) + 1) if any(src_r_hits) else 0

        # Evidence Availability Categorization
        if r_r1:
            avail_cat = "TOP1_CORRECT"
        elif r_r3:
            avail_cat = "TOP1_WRONG_BUT_TOP3_HAS_GOLD"
        elif r_r5:
            avail_cat = "TOP3_WRONG_BUT_TOP5_HAS_GOLD"
        else:
            avail_cat = "GOLD_ABSENT_FROM_TOP5"

        # Dense vs Reranker Loss Category
        if dense_r15 and not r_r5:
            loss_cat = "GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK"
        elif not dense_r15:
            loss_cat = "GOLD_OUTSIDE_DENSE15"
        else:
            loss_cat = "GOLD_RETAINED_IN_TOP5"

        supported_eval_results.append({
            "query_id": qid,
            "query_text": q_text,
            "target_topic": target_topic,
            "language_category": lang,
            "expected_source_id": expected_sid,
            "acceptable_gold_chunks": acceptable_cids,
            "dense_top15_cids": dense_top15_cids,
            "final_top5_cids": final_top5_cids,
            "final_top5_scores": final_top5_scores,
            "chunk_level": {
                "dense_r1": dense_r1,
                "dense_r3": dense_r3,
                "dense_r5": dense_r5,
                "dense_r10": dense_r10,
                "dense_r15": dense_r15,
                "dense_rank": dense_rank,
                "rerank_r1": r_r1,
                "rerank_r3": r_r3,
                "rerank_r5": r_r5,
                "rerank_rank": r_rank
            },
            "source_level": {
                "dense_r1": src_dense_r1,
                "dense_r3": src_dense_r3,
                "dense_r5": src_dense_r5,
                "dense_rank": src_dense_rank,
                "rerank_r1": src_r_r1,
                "rerank_r3": src_r_r3,
                "rerank_r5": src_r_r5,
                "rerank_rank": src_r_rank
            },
            "evidence_availability": avail_cat,
            "dense_vs_rerank_loss": loss_cat
        })

    n = len(supported_eval_results)
    assert n == 40, f"Expected 40 supported queries, got {n}"

    # Calculate Aggregate Metrics
    # Chunk-Level
    d_r1 = sum(1 for r in supported_eval_results if r["chunk_level"]["dense_r1"])
    d_r3 = sum(1 for r in supported_eval_results if r["chunk_level"]["dense_r3"])
    d_r5 = sum(1 for r in supported_eval_results if r["chunk_level"]["dense_r5"])
    d_r10 = sum(1 for r in supported_eval_results if r["chunk_level"]["dense_r10"])
    d_r15 = sum(1 for r in supported_eval_results if r["chunk_level"]["dense_r15"])
    d_mrr = sum(1.0 / r["chunk_level"]["dense_rank"] for r in supported_eval_results if r["chunk_level"]["dense_rank"] > 0) / n

    r_r1 = sum(1 for r in supported_eval_results if r["chunk_level"]["rerank_r1"])
    r_r3 = sum(1 for r in supported_eval_results if r["chunk_level"]["rerank_r3"])
    r_r5 = sum(1 for r in supported_eval_results if r["chunk_level"]["rerank_r5"])
    r_mrr = sum(1.0 / r["chunk_level"]["rerank_rank"] for r in supported_eval_results if r["chunk_level"]["rerank_rank"] > 0) / n

    # Source-Level
    src_d_r1 = sum(1 for r in supported_eval_results if r["source_level"]["dense_r1"])
    src_d_r3 = sum(1 for r in supported_eval_results if r["source_level"]["dense_r3"])
    src_d_r5 = sum(1 for r in supported_eval_results if r["source_level"]["dense_r5"])
    src_d_mrr = sum(1.0 / r["source_level"]["dense_rank"] for r in supported_eval_results if r["source_level"]["dense_rank"] > 0) / n

    src_r_r1 = sum(1 for r in supported_eval_results if r["source_level"]["rerank_r1"])
    src_r_r3 = sum(1 for r in supported_eval_results if r["source_level"]["rerank_r3"])
    src_r_r5 = sum(1 for r in supported_eval_results if r["source_level"]["rerank_r5"])
    src_r_mrr = sum(1.0 / r["source_level"]["rerank_rank"] for r in supported_eval_results if r["source_level"]["rerank_rank"] > 0) / n

    # Evidence Availability Counts
    avail_counts = {
        "TOP1_CORRECT": sum(1 for r in supported_eval_results if r["evidence_availability"] == "TOP1_CORRECT"),
        "TOP1_WRONG_BUT_TOP3_HAS_GOLD": sum(1 for r in supported_eval_results if r["evidence_availability"] == "TOP1_WRONG_BUT_TOP3_HAS_GOLD"),
        "TOP3_WRONG_BUT_TOP5_HAS_GOLD": sum(1 for r in supported_eval_results if r["evidence_availability"] == "TOP3_WRONG_BUT_TOP5_HAS_GOLD"),
        "GOLD_ABSENT_FROM_TOP5": sum(1 for r in supported_eval_results if r["evidence_availability"] == "GOLD_ABSENT_FROM_TOP5")
    }

    # Dense vs Rerank Loss Counts
    loss_counts = {
        "GOLD_RETAINED_IN_TOP5": sum(1 for r in supported_eval_results if r["dense_vs_rerank_loss"] == "GOLD_RETAINED_IN_TOP5"),
        "GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK": sum(1 for r in supported_eval_results if r["dense_vs_rerank_loss"] == "GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK"),
        "GOLD_OUTSIDE_DENSE15": sum(1 for r in supported_eval_results if r["dense_vs_rerank_loss"] == "GOLD_OUTSIDE_DENSE15")
    }

    # Language Breakdown
    language_breakdown = {}
    for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
        l_subs = [r for r in supported_eval_results if r["language_category"] == lang]
        ln = len(l_subs)
        l_d_r15 = sum(1 for r in l_subs if r["chunk_level"]["dense_r15"])
        l_r_r1 = sum(1 for r in l_subs if r["chunk_level"]["rerank_r1"])
        l_r_r3 = sum(1 for r in l_subs if r["chunk_level"]["rerank_r3"])
        l_r_r5 = sum(1 for r in l_subs if r["chunk_level"]["rerank_r5"])
        l_r_mrr = sum(1.0 / r["chunk_level"]["rerank_rank"] for r in l_subs if r["chunk_level"]["rerank_rank"] > 0) / ln

        language_breakdown[lang] = {
            "n": ln,
            "dense_top15_count": f"{l_d_r15}/{ln}",
            "dense_top15_pct": round(l_d_r15 / ln * 100, 2),
            "final_r1_count": f"{l_r_r1}/{ln}",
            "final_r1_pct": round(l_r_r1 / ln * 100, 2),
            "final_r3_count": f"{l_r_r3}/{ln}",
            "final_r3_pct": round(l_r_r3 / ln * 100, 2),
            "final_r5_count": f"{l_r_r5}/{ln}",
            "final_r5_pct": round(l_r_r5 / ln * 100, 2),
            "final_mrr": round(l_r_mrr, 4)
        }

    total_time_ms = (total_query_enc_time + total_dense_search_time + total_rerank_time) * 1000
    latency_summary = {
        "passage_encoding_time_s": round(t_enc_passages, 2),
        "total_query_eval_time_s": round(total_query_enc_time + total_dense_search_time + total_rerank_time, 2),
        "avg_query_encoding_ms": round(total_query_enc_time / len(holdout_queries) * 1000, 2),
        "avg_dense_search_ms": round(total_dense_search_time / len(holdout_queries) * 1000, 2),
        "avg_top15_rerank_ms": round(total_rerank_time / len(holdout_queries) * 1000, 2),
        "avg_end_to_end_per_query_ms": round(total_time_ms / len(holdout_queries), 2),
        "hardware_environment": "Intel/AMD CPU, torch multi-threading"
    }

    final_results = {
        "gate": "GATE_5.11",
        "frozen_configuration_hash": actual_config_hash,
        "frozen_benchmark_hash": actual_benchmark_hash,
        "sample_sizes": {
            "total_holdout_queries": len(holdout_queries),
            "supported_queries_n": n,
            "unsupported_queries_n": len(unsupported_eval_results)
        },
        "dense_candidate_recall": {
            "top5_count": f"{d_r5}/{n}",
            "top5_pct": round(d_r5 / n * 100, 2),
            "top10_count": f"{d_r10}/{n}",
            "top10_pct": round(d_r10 / n * 100, 2),
            "top15_count": f"{d_r15}/{n}",
            "top15_pct": round(d_r15 / n * 100, 2),
            "dense_mrr": round(d_mrr, 4)
        },
        "final_chunk_level_metrics": {
            "r1_count": f"{r_r1}/{n}",
            "r1_pct": round(r_r1 / n * 100, 2),
            "r3_count": f"{r_r3}/{n}",
            "r3_pct": round(r_r3 / n * 100, 2),
            "r5_count": f"{r_r5}/{n}",
            "r5_pct": round(r_r5 / n * 100, 2),
            "mrr": round(r_mrr, 4)
        },
        "source_level_metrics": {
            "dense_r1": f"{src_d_r1}/{n} ({round(src_d_r1/n*100,2)}%)",
            "dense_r3": f"{src_d_r3}/{n} ({round(src_d_r3/n*100,2)}%)",
            "dense_r5": f"{src_d_r5}/{n} ({round(src_d_r5/n*100,2)}%)",
            "dense_mrr": round(src_d_mrr, 4),
            "rerank_r1": f"{src_r_r1}/{n} ({round(src_r_r1/n*100,2)}%)",
            "rerank_r3": f"{src_r_r3}/{n} ({round(src_r_r3/n*100,2)}%)",
            "rerank_r5": f"{src_r_r5}/{n} ({round(src_r_r5/n*100,2)}%)",
            "rerank_mrr": round(src_r_mrr, 4)
        },
        "evidence_availability": {
            "TOP1_CORRECT": f"{avail_counts['TOP1_CORRECT']}/{n} ({round(avail_counts['TOP1_CORRECT']/n*100, 2)}%)",
            "TOP1_WRONG_BUT_TOP3_HAS_GOLD": f"{avail_counts['TOP1_WRONG_BUT_TOP3_HAS_GOLD']}/{n} ({round(avail_counts['TOP1_WRONG_BUT_TOP3_HAS_GOLD']/n*100, 2)}%)",
            "TOP3_WRONG_BUT_TOP5_HAS_GOLD": f"{avail_counts['TOP3_WRONG_BUT_TOP5_HAS_GOLD']}/{n} ({round(avail_counts['TOP3_WRONG_BUT_TOP5_HAS_GOLD']/n*100, 2)}%)",
            "GOLD_ABSENT_FROM_TOP5": f"{avail_counts['GOLD_ABSENT_FROM_TOP5']}/{n} ({round(avail_counts['GOLD_ABSENT_FROM_TOP5']/n*100, 2)}%)"
        },
        "dense_vs_reranker_analysis": {
            "GOLD_RETAINED_IN_TOP5": f"{loss_counts['GOLD_RETAINED_IN_TOP5']}/{n} ({round(loss_counts['GOLD_RETAINED_IN_TOP5']/n*100, 2)}%)",
            "GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK": f"{loss_counts['GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK']}/{n} ({round(loss_counts['GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK']/n*100, 2)}%)",
            "GOLD_OUTSIDE_DENSE15": f"{loss_counts['GOLD_OUTSIDE_DENSE15']}/{n} ({round(loss_counts['GOLD_OUTSIDE_DENSE15']/n*100, 2)}%)"
        },
        "language_breakdown": language_breakdown,
        "unsupported_queries_evaluation": {
            "total_unsupported_queries": len(unsupported_eval_results),
            "max_reranker_score": max(r["r_top1_score"] for r in unsupported_eval_results) if unsupported_eval_results else 0,
            "min_reranker_score": min(r["r_top1_score"] for r in unsupported_eval_results) if unsupported_eval_results else 0,
            "unsupported_queries": unsupported_eval_results
        },
        "latency_summary": latency_summary,
        "query_evaluations": supported_eval_results
    }

    with open(EVAL_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)

    print("\n" + "="*80)
    print("GATE 5.11 SINGLE LOCKED HOLDOUT RESULTS SUMMARY")
    print("="*80)
    print(f"Dense Candidate Recall@15: {final_results['dense_candidate_recall']['top15_count']} ({final_results['dense_candidate_recall']['top15_pct']}%)")
    print(f"Final Chunk Recall@1:      {final_results['final_chunk_level_metrics']['r1_count']} ({final_results['final_chunk_level_metrics']['r1_pct']}%)")
    print(f"Final Chunk Recall@3:      {final_results['final_chunk_level_metrics']['r3_count']} ({final_results['final_chunk_level_metrics']['r3_pct']}%)")
    print(f"Final Chunk Recall@5:      {final_results['final_chunk_level_metrics']['r5_count']} ({final_results['final_chunk_level_metrics']['r5_pct']}%)")
    print(f"Final Chunk MRR:           {final_results['final_chunk_level_metrics']['mrr']}")
    print(f"\nEvidence Availability Breakdown:")
    for k, v in final_results["evidence_availability"].items():
        print(f"  {k}: {v}")
    print(f"\nDense vs Rerank Loss:")
    for k, v in final_results["dense_vs_reranker_analysis"].items():
        print(f"  {k}: {v}")
    print(f"\nLanguage Breakdown:")
    for lang, lm in language_breakdown.items():
        print(f"  {lang} (N={lm['n']}): Dense Top-15={lm['dense_top15_count']} ({lm['dense_top15_pct']}%), Final R@1={lm['final_r1_count']} ({lm['final_r1_pct']}%), Final R@5={lm['final_r5_count']} ({lm['final_r5_pct']}%), MRR={lm['final_mrr']}")

    print(f"\nResults saved to {EVAL_OUT_FILE}")

if __name__ == "__main__":
    main()
