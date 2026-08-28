"""
Gate 5.23 — Single-Shot Evaluation on the Fresh Locked Benchmark
Executes the frozen retrieval candidate configuration EXACTLY ONCE on the fresh locked benchmark.
"""

import json
import os
import sys
import time
import re
import hashlib
import datetime
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

BENCHMARK_FILE = os.path.join(RESEARCH_DIR, "gate_5_22_fresh_benchmark", "benchmark", "fresh_locked_benchmark.json")
CHUNKS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
FROZEN_CONFIG_FILE = os.path.join(RESEARCH_DIR, "gate_5_21_evidence_selection_architecture", "candidate", "frozen_candidate_configuration.json")

EVAL_OUT_DIR = os.path.join(BASE_DIR, "..", "evaluations")
INTEGRITY_OUT_DIR = os.path.join(BASE_DIR, "..", "integrity")
DIAG_OUT_DIR = os.path.join(BASE_DIR, "..", "diagnostics")
PER_QUERY_OUT_DIR = os.path.join(BASE_DIR, "..", "per_query")

os.makedirs(EVAL_OUT_DIR, exist_ok=True)
os.makedirs(INTEGRITY_OUT_DIR, exist_ok=True)
os.makedirs(DIAG_OUT_DIR, exist_ok=True)
os.makedirs(PER_QUERY_OUT_DIR, exist_ok=True)

EXPECTED_BENCHMARK_HASH = "a0267355615d9094fd9698ff0bbb5d9aa69311a9c822e1cd47ac12fc08573ef6"
EXPECTED_CONFIG_HASH = "07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736"

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

def main():
    print("=" * 80)
    print("GATE 5.23 — SINGLE-SHOT EVALUATION ON FRESH LOCKED BENCHMARK")
    print("=" * 80)

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 1: INTEGRITY VERIFICATION
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- PHASE 1: INTEGRITY VERIFICATION ---")
    
    # 1. Benchmark Hash
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        bm_text = f.read()
    computed_bm_hash = hashlib.sha256(bm_text.replace('\r\n', '\n').encode('utf-8')).hexdigest()
    assert computed_bm_hash == EXPECTED_BENCHMARK_HASH, f"Benchmark hash mismatch! Expected {EXPECTED_BENCHMARK_HASH}, got {computed_bm_hash}"
    print(f"✓ Fresh Benchmark SHA-256 Verified: {computed_bm_hash}")

    # 2. Config Hash
    with open(FROZEN_CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg_copy = dict(cfg)
    cfg_copy.pop('configuration_sha256', None)
    cfg_json = json.dumps(cfg_copy, indent=2, sort_keys=True, ensure_ascii=False)
    computed_cfg_hash = hashlib.sha256(cfg_json.encode('utf-8')).hexdigest()
    assert computed_cfg_hash == EXPECTED_CONFIG_HASH, f"Config hash mismatch! Expected {EXPECTED_CONFIG_HASH}, got {computed_cfg_hash}"
    print(f"✓ Frozen Candidate SHA-256 Verified: {computed_cfg_hash}")

    # 3. Load Benchmark and Chunks
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        benchmark_data = json.load(f)
    queries = benchmark_data["queries"]
    
    supported_queries = [q for q in queries if q["expected_source_id"] != "NONE"]
    hard_negatives = [q for q in queries if q["query_type"] == "Hard_Negative"]
    out_of_corpus = [q for q in queries if q["query_type"] == "Out_Of_Corpus"]

    assert len(queries) == 50, f"Expected 50 queries, found {len(queries)}"
    assert len(supported_queries) == 40, f"Expected 40 supported queries, found {len(supported_queries)}"
    assert len(hard_negatives) == 5, f"Expected 5 hard negatives, found {len(hard_negatives)}"
    assert len(out_of_corpus) == 5, f"Expected 5 out of corpus, found {len(out_of_corpus)}"
    print(f"✓ Query counts verified: {len(supported_queries)} supported, {len(hard_negatives)} HN, {len(out_of_corpus)} OOC")

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunks_by_id = {c["chunk_id"]: c for c in chunks}
    assert len(chunks) == 68, f"Expected 68 chunks, found {len(chunks)}"
    print(f"✓ Corpus chunks verified: {len(chunks)} chunks across 8 documents")

    # Save integrity verification record
    integrity_record = {
        "gate": "GATE_5.23",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "benchmark_file": BENCHMARK_FILE,
        "benchmark_sha256": computed_bm_hash,
        "benchmark_hash_match": True,
        "configuration_file": FROZEN_CONFIG_FILE,
        "configuration_sha256": computed_cfg_hash,
        "configuration_hash_match": True,
        "total_queries": len(queries),
        "supported_queries": len(supported_queries),
        "hard_negatives": len(hard_negatives),
        "out_of_corpus": len(out_of_corpus),
        "corpus_chunks": len(chunks),
        "execution_policy": "SINGLE_SHOT_ONLY",
        "prior_evaluations_on_fresh_benchmark": 0,
        "integrity_status": "ALL_INTEGRITY_CHECKS_PASSED"
    }
    with open(os.path.join(INTEGRITY_OUT_DIR, "gate_5_23_integrity_verification.json"), "w", encoding="utf-8") as f:
        json.dump(integrity_record, f, indent=2, ensure_ascii=False)

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 2: SINGLE FRESH BENCHMARK EVALUATION
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- PHASE 2: LOADING MODELS (CPU) ---")
    start_load = time.time()
    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")
    print(f"✓ Models loaded in {time.time() - start_load:.2f}s")

    # Pre-encode all 68 corpus passages
    print("Encoding 68 corpus passages with passage: prefix...")
    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)
    print("✓ Chunk embeddings ready.")

    k_depth = 15
    overview_mult = 0.85

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 3 & 4: EVALUATE SUPPORTED QUERIES (N=40)
    # ──────────────────────────────────────────────────────────────────────────
    print(f"\n--- EVALUATING {len(supported_queries)} SUPPORTED QUERIES ---")
    supported_evaluations = []
    
    for q in supported_queries:
        qid = q["query_id"]
        raw_q = q["query_text"]
        lang = q["language"]
        expected_sid = q["expected_source_id"]
        gold_cids = q["gold_chunk_ids"]
        qtype = q["query_type"]
        intent_cat = q["intent_category"]

        # Step 1: Normalization
        norm_q = normalize_query_track_a(raw_q)

        # Step 2: Dense retrieval (Top-15)
        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:k_depth]
        top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
        top15_scores = [float(dense_scores[idx]) for idx in top15_indices]

        # Dense rank & hit
        dense_ranks = []
        for gc in gold_cids:
            if gc in top15_cids:
                dense_ranks.append(top15_cids.index(gc) + 1)
        best_dense_rank = min(dense_ranks) if dense_ranks else None
        dense_hit_r5 = best_dense_rank is not None and best_dense_rank <= 5
        dense_hit_r10 = best_dense_rank is not None and best_dense_rank <= 10
        dense_hit_r15 = best_dense_rank is not None and best_dense_rank <= 15

        # Step 3: Cross-encoder reranking
        pairs = [[raw_q, chunks_by_id[cid]["text"]] for cid in top15_cids]
        raw_rerank_scores = reranker.predict(pairs)

        # Step 4: Overview debiasing (0.85x for -HYB-000 chunks)
        adjusted_scores = []
        for cid, score in zip(top15_cids, raw_rerank_scores):
            adj = float(score)
            if cid.endswith("-HYB-000"):
                adj *= overview_mult
            adjusted_scores.append(adj)

        # Step 5: Sort final top-15 / select Top-5
        rerank_order = np.argsort(-np.array(adjusted_scores))
        final_ranked_cids = [top15_cids[i] for i in rerank_order]
        final_ranked_scores = [adjusted_scores[i] for i in rerank_order]
        final_top5_cids = final_ranked_cids[:5]
        final_top5_scores = final_ranked_scores[:5]

        # Chunk-level metrics
        final_ranks = []
        for gc in gold_cids:
            if gc in final_ranked_cids:
                final_ranks.append(final_ranked_cids.index(gc) + 1)
        best_final_rank = min(final_ranks) if final_ranks else None

        r1 = best_final_rank is not None and best_final_rank == 1
        r3 = best_final_rank is not None and best_final_rank <= 3
        r5 = best_final_rank is not None and best_final_rank <= 5
        rr = (1.0 / best_final_rank) if best_final_rank is not None else 0.0

        # Source-level metrics
        retrieved_sids = [chunks_by_id[cid]["parent_source_id"] for cid in final_ranked_cids]
        source_r1 = retrieved_sids[0] == expected_sid if retrieved_sids else False
        source_r5 = expected_sid in retrieved_sids[:5]

        # Evidence availability category
        if r1:
            evidence_cat = "TOP1_CORRECT"
        elif r3:
            evidence_cat = "TOP1_WRONG_BUT_TOP3_HAS_GOLD"
        elif r5:
            evidence_cat = "TOP3_WRONG_BUT_TOP5_HAS_GOLD"
        else:
            evidence_cat = "GOLD_ABSENT_FROM_TOP5"

        # Failure mechanism classification
        if not dense_hit_r15:
            failure_mech = "GOLD_OUTSIDE_DENSE15"
        elif not r5:
            failure_mech = "GOLD_IN_DENSE15_BUT_RERANKED_OUT"
        else:
            failure_mech = "SUCCESS_IN_TOP5"

        # Detailed record
        eval_record = {
            "query_id": qid,
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "language": lang,
            "expected_source_id": expected_sid,
            "gold_chunk_ids": gold_cids,
            "query_type": qtype,
            "intent_category": intent_cat,
            "dense_top15_cids": top15_cids,
            "dense_top15_scores": top15_scores,
            "best_dense_rank": best_dense_rank,
            "dense_hit_r5": dense_hit_r5,
            "dense_hit_r10": dense_hit_r10,
            "dense_hit_r15": dense_hit_r15,
            "final_top5_cids": final_top5_cids,
            "final_top5_scores": final_top5_scores,
            "final_top5_sids": retrieved_sids[:5],
            "best_final_rank": best_final_rank,
            "r1": r1,
            "r3": r3,
            "r5": r5,
            "reciprocal_rank": rr,
            "source_r1": source_r1,
            "source_r5": source_r5,
            "evidence_availability_category": evidence_cat,
            "failure_mechanism": failure_mech
        }
        supported_evaluations.append(eval_record)

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 7: EVALUATE UNSUPPORTED QUERIES (5 HN + 5 OOC = 10)
    # ──────────────────────────────────────────────────────────────────────────
    print(f"\n--- EVALUATING {len(hard_negatives) + len(out_of_corpus)} UNSUPPORTED QUERIES ---")
    unsupported_evaluations = []

    for q in hard_negatives + out_of_corpus:
        qid = q["query_id"]
        raw_q = q["query_text"]
        lang = q["language"]
        qtype = q["query_type"]
        intent_cat = q["intent_category"]

        norm_q = normalize_query_track_a(raw_q)
        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:k_depth]
        top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]

        pairs = [[raw_q, chunks_by_id[cid]["text"]] for cid in top15_cids]
        raw_rerank_scores = reranker.predict(pairs)

        adjusted_scores = []
        for cid, score in zip(top15_cids, raw_rerank_scores):
            adj = float(score)
            if cid.endswith("-HYB-000"):
                adj *= overview_mult
            adjusted_scores.append(adj)

        rerank_order = np.argsort(-np.array(adjusted_scores))
        final_ranked_cids = [top15_cids[i] for i in rerank_order]
        final_ranked_scores = [adjusted_scores[i] for i in rerank_order]

        top1_score = float(final_ranked_scores[0])
        top5_scores = [float(s) for s in final_ranked_scores[:5]]
        top5_sids = [chunks_by_id[cid]["parent_source_id"] for cid in final_ranked_cids[:5]]

        unsupported_evaluations.append({
            "query_id": qid,
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "language": lang,
            "query_type": qtype,
            "intent_category": intent_cat,
            "top1_score": top1_score,
            "top5_scores": top5_scores,
            "mean_top5_score": float(np.mean(top5_scores)),
            "retrieved_top5_cids": final_ranked_cids[:5],
            "retrieved_top5_sids": top5_sids
        })

    # ──────────────────────────────────────────────────────────────────────────
    # AGGREGATE CALCULATIONS
    # ──────────────────────────────────────────────────────────────────────────
    n_supp = len(supported_evaluations)
    chunk_r1_count = sum(1 for e in supported_evaluations if e["r1"])
    chunk_r3_count = sum(1 for e in supported_evaluations if e["r3"])
    chunk_r5_count = sum(1 for e in supported_evaluations if e["r5"])
    chunk_mrr = float(np.mean([e["reciprocal_rank"] for e in supported_evaluations]))

    dense_r5_count = sum(1 for e in supported_evaluations if e["dense_hit_r5"])
    dense_r10_count = sum(1 for e in supported_evaluations if e["dense_hit_r10"])
    dense_r15_count = sum(1 for e in supported_evaluations if e["dense_hit_r15"])

    source_r1_count = sum(1 for e in supported_evaluations if e["source_r1"])
    source_r5_count = sum(1 for e in supported_evaluations if e["source_r5"])

    # Evidence Availability Categories
    cat_counts = {
        "TOP1_CORRECT": sum(1 for e in supported_evaluations if e["evidence_availability_category"] == "TOP1_CORRECT"),
        "TOP1_WRONG_BUT_TOP3_HAS_GOLD": sum(1 for e in supported_evaluations if e["evidence_availability_category"] == "TOP1_WRONG_BUT_TOP3_HAS_GOLD"),
        "TOP3_WRONG_BUT_TOP5_HAS_GOLD": sum(1 for e in supported_evaluations if e["evidence_availability_category"] == "TOP3_WRONG_BUT_TOP5_HAS_GOLD"),
        "GOLD_ABSENT_FROM_TOP5": sum(1 for e in supported_evaluations if e["evidence_availability_category"] == "GOLD_ABSENT_FROM_TOP5")
    }

    # Failure mechanisms
    fail_counts = {
        "GOLD_IN_DENSE_TOP15": dense_r15_count,
        "GOLD_OUTSIDE_DENSE15": sum(1 for e in supported_evaluations if e["failure_mechanism"] == "GOLD_OUTSIDE_DENSE15"),
        "GOLD_IN_DENSE15_BUT_RERANKED_OUT": sum(1 for e in supported_evaluations if e["failure_mechanism"] == "GOLD_IN_DENSE15_BUT_RERANKED_OUT")
    }

    # Language breakdown
    languages = ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]
    lang_breakdown = {}
    for lang in languages:
        lang_evals = [e for e in supported_evaluations if e["language"] == lang]
        n_l = len(lang_evals)
        if n_l > 0:
            lang_breakdown[lang] = {
                "n": n_l,
                "dense_r15_count": sum(1 for e in lang_evals if e["dense_hit_r15"]),
                "dense_r15_pct": round(sum(1 for e in lang_evals if e["dense_hit_r15"]) / n_l * 100, 1),
                "chunk_r1_count": sum(1 for e in lang_evals if e["r1"]),
                "chunk_r1_pct": round(sum(1 for e in lang_evals if e["r1"]) / n_l * 100, 1),
                "chunk_r3_count": sum(1 for e in lang_evals if e["r3"]),
                "chunk_r3_pct": round(sum(1 for e in lang_evals if e["r3"]) / n_l * 100, 1),
                "chunk_r5_count": sum(1 for e in lang_evals if e["r5"]),
                "chunk_r5_pct": round(sum(1 for e in lang_evals if e["r5"]) / n_l * 100, 1),
                "mrr": round(float(np.mean([e["reciprocal_rank"] for e in lang_evals])), 4)
            }

    # Document / Topic Breakdown
    sources = sorted(list(set(e["expected_source_id"] for e in supported_evaluations)))
    doc_breakdown = {}
    for sid in sources:
        doc_evals = [e for e in supported_evaluations if e["expected_source_id"] == sid]
        n_d = len(doc_evals)
        doc_breakdown[sid] = {
            "n": n_d,
            "dense_r15_count": sum(1 for e in doc_evals if e["dense_hit_r15"]),
            "dense_r15_pct": round(sum(1 for e in doc_evals if e["dense_hit_r15"]) / n_d * 100, 1),
            "chunk_r5_count": sum(1 for e in doc_evals if e["r5"]),
            "chunk_r5_pct": round(sum(1 for e in doc_evals if e["r5"]) / n_d * 100, 1),
            "mrr": round(float(np.mean([e["reciprocal_rank"] for e in doc_evals])), 4)
        }

    # Unsupported query metrics
    hn_evals = [e for e in unsupported_evaluations if e["query_type"] == "Hard_Negative"]
    ooc_evals = [e for e in unsupported_evaluations if e["query_type"] == "Out_Of_Corpus"]

    unsupported_summary = {
        "hard_negatives": {
            "n": len(hn_evals),
            "top1_scores": [e["top1_score"] for e in hn_evals],
            "max_score": float(max(e["top1_score"] for e in hn_evals)),
            "min_score": float(min(e["top1_score"] for e in hn_evals)),
            "mean_top1_score": float(np.mean([e["top1_score"] for e in hn_evals])),
            "mean_top5_score": float(np.mean([e["mean_top5_score"] for e in hn_evals]))
        },
        "out_of_corpus": {
            "n": len(ooc_evals),
            "top1_scores": [e["top1_score"] for e in ooc_evals],
            "max_score": float(max(e["top1_score"] for e in ooc_evals)),
            "min_score": float(min(e["top1_score"] for e in ooc_evals)),
            "mean_top1_score": float(np.mean([e["top1_score"] for e in ooc_evals])),
            "mean_top5_score": float(np.mean([e["mean_top5_score"] for e in ooc_evals]))
        },
        "all_unsupported": {
            "n": len(unsupported_evaluations),
            "max_score": float(max(e["top1_score"] for e in unsupported_evaluations)),
            "min_score": float(min(e["top1_score"] for e in unsupported_evaluations)),
            "mean_top1_score": float(np.mean([e["top1_score"] for e in unsupported_evaluations]))
        }
    }

    # Failures list
    failures = [e for e in supported_evaluations if not e["r5"]]

    # Print summary to console
    print("\n" + "=" * 80)
    print("GATE 5.23 RESULTS SUMMARY")
    print("=" * 80)
    print(f"Primary Metric — Final Chunk Recall@5: {chunk_r5_count}/{n_supp} ({chunk_r5_count/n_supp*100:.1f}%)")
    print(f"Final Chunk Recall@3:                 {chunk_r3_count}/{n_supp} ({chunk_r3_count/n_supp*100:.1f}%)")
    print(f"Final Chunk Recall@1:                 {chunk_r1_count}/{n_supp} ({chunk_r1_count/n_supp*100:.1f}%)")
    print(f"Final Chunk MRR:                      {chunk_mrr:.4f}")
    print(f"Dense Candidate Recall@15:            {dense_r15_count}/{n_supp} ({dense_r15_count/n_supp*100:.1f}%)")
    print(f"Dense Candidate Recall@10:            {dense_r10_count}/{n_supp} ({dense_r10_count/n_supp*100:.1f}%)")
    print(f"Dense Candidate Recall@5:             {dense_r5_count}/{n_supp} ({dense_r5_count/n_supp*100:.1f}%)")
    print(f"Source Recall@1:                      {source_r1_count}/{n_supp} ({source_r1_count/n_supp*100:.1f}%)")
    print(f"Source Recall@5:                      {source_r5_count}/{n_supp} ({source_r5_count/n_supp*100:.1f}%)")

    print("\nEvidence Availability Breakdown:")
    for cat, cnt in cat_counts.items():
        print(f"  {cat:30s}: {cnt:2d}/{n_supp} ({cnt/n_supp*100:.1f}%)")

    print("\nFailure Decomposition:")
    print(f"  GOLD_IN_DENSE_TOP15:                {fail_counts['GOLD_IN_DENSE_TOP15']:2d}/{n_supp} ({fail_counts['GOLD_IN_DENSE_TOP15']/n_supp*100:.1f}%)")
    print(f"  GOLD_OUTSIDE_DENSE15:               {fail_counts['GOLD_OUTSIDE_DENSE15']:2d}/{n_supp} ({fail_counts['GOLD_OUTSIDE_DENSE15']/n_supp*100:.1f}%)")
    print(f"  GOLD_IN_DENSE15_BUT_RERANKED_OUT:   {fail_counts['GOLD_IN_DENSE15_BUT_RERANKED_OUT']:2d}/{n_supp} ({fail_counts['GOLD_IN_DENSE15_BUT_RERANKED_OUT']/n_supp*100:.1f}%)")

    print("\nLanguage Breakdown:")
    for lang, metrics in lang_breakdown.items():
        print(f"  {lang:22s} (N={metrics['n']}): Dense15={metrics['dense_r15_pct']}% | R@1={metrics['chunk_r1_pct']}% | R@3={metrics['chunk_r3_pct']}% | R@5={metrics['chunk_r5_pct']}% | MRR={metrics['mrr']:.4f}")

    print("\nDocument / Topic Breakdown:")
    for sid, metrics in doc_breakdown.items():
        print(f"  {sid:14s} (N={metrics['n']}): Dense15={metrics['dense_r15_pct']}% | R@5={metrics['chunk_r5_pct']}% | MRR={metrics['mrr']:.4f}")

    print("\nUnsupported Query Scores:")
    print(f"  Hard Negatives (N=5): Max={unsupported_summary['hard_negatives']['max_score']:.4f}, Mean={unsupported_summary['hard_negatives']['mean_top1_score']:.4f}")
    print(f"  Out-of-Corpus  (N=5): Max={unsupported_summary['out_of_corpus']['max_score']:.4f}, Mean={unsupported_summary['out_of_corpus']['mean_top1_score']:.4f}")

    if failures:
        print(f"\nFailure Cases (N={len(failures)}):")
        for f_case in failures:
            print(f"  {f_case['query_id']} [{f_case['language']}]: {f_case['failure_mechanism']} (DenseRank={f_case['best_dense_rank']}, FinalRank={f_case['best_final_rank']})")
            print(f"    Q: {f_case['raw_query']}")
            print(f"    Expected: {f_case['gold_chunk_ids']}, Retrieved Top5: {f_case['final_top5_cids']}")
    else:
        print("\n✓ ZERO FAILURES ON THE FRESH LOCKED BENCHMARK!")

    # ──────────────────────────────────────────────────────────────────────────
    # SAVE ALL RESULT ARTIFACTS
    # ──────────────────────────────────────────────────────────────────────────
    overall_results = {
        "gate": "GATE_5.23",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "benchmark_file": BENCHMARK_FILE,
        "benchmark_sha256": computed_bm_hash,
        "configuration_sha256": computed_cfg_hash,
        "sample_sizes": {
            "total_queries": len(queries),
            "supported_queries": n_supp,
            "hard_negatives": len(hard_negatives),
            "out_of_corpus": len(out_of_corpus)
        },
        "primary_metrics": {
            "final_chunk_recall_at_1_count": chunk_r1_count,
            "final_chunk_recall_at_1_pct": round(chunk_r1_count / n_supp * 100, 2),
            "final_chunk_recall_at_3_count": chunk_r3_count,
            "final_chunk_recall_at_3_pct": round(chunk_r3_count / n_supp * 100, 2),
            "final_chunk_recall_at_5_count": chunk_r5_count,
            "final_chunk_recall_at_5_pct": round(chunk_r5_count / n_supp * 100, 2),
            "final_chunk_mrr": round(chunk_mrr, 4)
        },
        "candidate_stage_metrics": {
            "dense_candidate_recall_at_5_count": dense_r5_count,
            "dense_candidate_recall_at_5_pct": round(dense_r5_count / n_supp * 100, 2),
            "dense_candidate_recall_at_10_count": dense_r10_count,
            "dense_candidate_recall_at_10_pct": round(dense_r10_count / n_supp * 100, 2),
            "dense_candidate_recall_at_15_count": dense_r15_count,
            "dense_candidate_recall_at_15_pct": round(dense_r15_count / n_supp * 100, 2)
        },
        "secondary_source_metrics": {
            "source_recall_at_1_count": source_r1_count,
            "source_recall_at_1_pct": round(source_r1_count / n_supp * 100, 2),
            "source_recall_at_5_count": source_r5_count,
            "source_recall_at_5_pct": round(source_r5_count / n_supp * 100, 2)
        },
        "evidence_availability_categories": {
            cat: {
                "count": cnt,
                "pct": round(cnt / n_supp * 100, 2)
            }
            for cat, cnt in cat_counts.items()
        },
        "failure_decomposition": {
            k: {
                "count": cnt,
                "pct": round(cnt / n_supp * 100, 2)
            }
            for k, cnt in fail_counts.items()
        },
        "language_breakdown": lang_breakdown,
        "document_breakdown": doc_breakdown,
        "unsupported_query_summary": unsupported_summary,
        "generalization_classification": (
            "FRESH_BENCHMARK_GENERALIZATION_SUPPORTED" if chunk_r5_count / n_supp >= 0.85
            else "FRESH_BENCHMARK_GENERALIZATION_PARTIAL" if chunk_r5_count / n_supp >= 0.60
            else "FRESH_BENCHMARK_GENERALIZATION_NOT_SUPPORTED"
        )
    }

    # 1. Main Results JSON
    with open(os.path.join(EVAL_OUT_DIR, "gate_5_23_fresh_benchmark_results.json"), "w", encoding="utf-8") as f:
        json.dump(overall_results, f, indent=2, ensure_ascii=False)
    print("\n✓ Saved gate_5_23_fresh_benchmark_results.json")

    # 2. Per-Query Results JSON
    per_query_data = {
        "gate": "GATE_5.23",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "supported_queries": supported_evaluations,
        "unsupported_queries": unsupported_evaluations
    }
    with open(os.path.join(EVAL_OUT_DIR, "gate_5_23_per_query_results.json"), "w", encoding="utf-8") as f:
        json.dump(per_query_data, f, indent=2, ensure_ascii=False)
    print("✓ Saved gate_5_23_per_query_results.json")

    # 3. Failure Analysis JSON
    failure_analysis_data = {
        "gate": "GATE_5.23",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "total_supported": n_supp,
        "total_failures": len(failures),
        "failure_rate_pct": round(len(failures) / n_supp * 100, 2),
        "failure_decomposition": fail_counts,
        "failure_details": [
            {
                "query_id": f_case["query_id"],
                "query_text": f_case["raw_query"],
                "normalized_query": f_case["normalized_query"],
                "language": f_case["language"],
                "expected_source_id": f_case["expected_source_id"],
                "gold_chunk_ids": f_case["gold_chunk_ids"],
                "query_type": f_case["query_type"],
                "intent_category": f_case["intent_category"],
                "best_dense_rank": f_case["best_dense_rank"],
                "best_final_rank": f_case["best_final_rank"],
                "failure_mechanism": f_case["failure_mechanism"],
                "retrieved_top5_cids": f_case["final_top5_cids"],
                "retrieved_top5_scores": f_case["final_top5_scores"],
                "retrieved_top5_sids": f_case["final_top5_sids"],
                "competition_type": "SAME_DOCUMENT_COMPETITION" if all(s == f_case["expected_source_id"] for s in f_case["final_top5_sids"]) else "CROSS_DOCUMENT_CONFUSION"
            }
            for f_case in failures
        ]
    }
    with open(os.path.join(DIAG_OUT_DIR, "gate_5_23_failure_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(failure_analysis_data, f, indent=2, ensure_ascii=False)
    print("✓ Saved gate_5_23_failure_analysis.json")

if __name__ == "__main__":
    main()
