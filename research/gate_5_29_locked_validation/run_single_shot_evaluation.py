"""
Gate 5.29 — Single-Shot Locked Validation of Strategy 5 on the New Locked NHS Benchmark
Executes the frozen Strategy 5 configuration EXACTLY ONCE over all 50 queries across the 51 newly ingested NHS chunks.
"""

import os
import sys
import json
import time
import hashlib
import re
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTEG_DIR = os.path.join(BASE_DIR, "integrity")
EVALS_DIR = os.path.join(BASE_DIR, "evaluations")
DIAG_DIR = os.path.join(BASE_DIR, "diagnostics")
PER_QUERY_DIR = os.path.join(BASE_DIR, "per_query")

for d in [INTEG_DIR, EVALS_DIR, DIAG_DIR, PER_QUERY_DIR]:
    os.makedirs(d, exist_ok=True)

# -------------------------------------------------------------
# PHASE 1: PRE-RUN INTEGRITY VERIFICATION
# -------------------------------------------------------------
print("=" * 80)
print("GATE 5.29: PRE-RUN INTEGRITY VERIFICATION")
print("=" * 80)

BENCHMARK_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "gate_5_28_independent_benchmark", "benchmark", "new_locked_benchmark.json")
)
EXPECTED_BENCHMARK_SHA256 = "464612e733aeb1496c1dcdc5674e01d9504bd4ccd1244190e487c6e957dcc722"

with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
    bench_text = f.read()
# Platform-independent canonical UNIX LF bytes
canonical_bench_bytes = bench_text.replace('\r\n', '\n').encode('utf-8')
actual_benchmark_sha256 = hashlib.sha256(canonical_bench_bytes).hexdigest()

print(f"Benchmark File: {BENCHMARK_PATH}")
print(f"Expected Canonical SHA-256: {EXPECTED_BENCHMARK_SHA256}")
print(f"Actual Canonical SHA-256:   {actual_benchmark_sha256}")
if actual_benchmark_sha256 != EXPECTED_BENCHMARK_SHA256:
    print("✗ CRITICAL INTEGRITY FAILURE: Benchmark SHA-256 mismatch!")
    sys.exit(1)
print("✓ Benchmark canonical SHA-256 verified identical.")

FROZEN_CANDIDATE_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "gate_5_24_reranker_development_research", "candidate", "strategy_5_dev_candidate_configuration.json")
)
with open(FROZEN_CANDIDATE_PATH, "rb") as f:
    cand_bytes = f.read()
actual_candidate_sha256 = hashlib.sha256(cand_bytes).hexdigest()
frozen_cfg = json.loads(cand_bytes.decode('utf-8'))

print(f"\nFrozen Strategy 5 Config File: {FROZEN_CANDIDATE_PATH}")
print(f"Candidate Config SHA-256:     {actual_candidate_sha256}")
print(f"Candidate Name:               {frozen_cfg.get('candidate_name')}")

CORPUS_MANIFEST_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "gate_5_27_ingestion", "provenance_manifest.json")
)
with open(CORPUS_MANIFEST_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)
chunks_by_id = {c["chunk_id"]: c for c in chunks}
print(f"\nCorpus Manifest File:         {CORPUS_MANIFEST_PATH}")
print(f"Total Chunks in Corpus:       {len(chunks)} chunks across 6 documents (DOC-NHS-012..017)")

with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
    benchmark_data = json.load(f)
queries = benchmark_data["queries"]
supported_queries = [q for q in queries if q.get("query_type") not in ["hard_negative_confounder", "out_of_corpus"]]
unsupported_queries = [q for q in queries if q.get("query_type") in ["hard_negative_confounder", "out_of_corpus"]]

print(f"Total Queries in Benchmark:   {len(queries)} (Supported: {len(supported_queries)}, Unsupported: {len(unsupported_queries)})")

# Verify all gold chunk references exist in Gate 5.27 corpus
missing_gold = []
for q in supported_queries:
    for gcid in q["gold_chunk_ids"]:
        if gcid not in chunks_by_id:
            missing_gold.append((q["query_id"], gcid))

if missing_gold:
    print(f"✗ CRITICAL INTEGRITY FAILURE: Missing gold chunks {missing_gold}")
    sys.exit(1)
print(f"✓ 100% of gold chunk references ({sum(len(q['gold_chunk_ids']) for q in supported_queries)} citations) verified in Gate 5.27 corpus.")

pre_run_integrity = {
    "gate": "GATE_5.29",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "benchmark_file": BENCHMARK_PATH,
    "benchmark_sha256": actual_benchmark_sha256,
    "candidate_config_file": FROZEN_CANDIDATE_PATH,
    "candidate_config_sha256": actual_candidate_sha256,
    "corpus_manifest_file": CORPUS_MANIFEST_PATH,
    "corpus_chunk_count": len(chunks),
    "total_queries": len(queries),
    "supported_queries": len(supported_queries),
    "unsupported_queries": len(unsupported_queries),
    "gold_integrity_pass": True,
    "verdict": "PRE_RUN_INTEGRITY_VERIFIED"
}
with open(os.path.join(INTEG_DIR, "gate_5_29_pre_run_integrity.json"), "w", encoding="utf-8") as f:
    json.dump(pre_run_integrity, f, indent=2)

# -------------------------------------------------------------
# PHASE 2: SINGLE-SHOT MODEL EXECUTION
# -------------------------------------------------------------
print("\n" + "=" * 80)
print("GATE 5.29: EXECUTING SINGLE-SHOT EVALUATION")
print("=" * 80)

# Track A Normalization Mappings (Frozen)
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

def compute_token_overlap(q_text: str, chunk_text: str) -> float:
    q_tokens = set(re.findall(r'\w+', q_text.lower()))
    c_tokens = set(re.findall(r'\w+', chunk_text.lower()))
    if not q_tokens or not c_tokens:
        return 0.0
    return len(q_tokens.intersection(c_tokens)) / len(q_tokens)

print("Loading Dense Bi-Encoder: intfloat/multilingual-e5-small...")
dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")

print("Loading Cross-Encoder: BAAI/bge-reranker-v2-m3...")
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

passage_texts = [f"passage: {c['text']}" for c in chunks]
print(f"Encoding {len(passage_texts)} corpus passages...")
chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

k_depth = 15
overview_mult = 0.85
lambda_dense = 0.10
alpha_lexical = 0.03

per_query_results = []
supported_evals = []
unsupported_evals = []

print("\nRunning single-shot retrieval across all 50 queries...")

for q in queries:
    qid = q["query_id"]
    raw_q = q["query_text"]
    q_type = q.get("query_type")
    lang = q.get("language", "English")
    is_supported = q_type not in ["hard_negative_confounder", "out_of_corpus"]
    gold_cids = q.get("gold_chunk_ids", [])
    expected_sid = q.get("expected_source_id")

    norm_q = normalize_query_track_a(raw_q)
    q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
    dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]

    # Candidate depth K=15
    top15_indices = np.argsort(-dense_scores)[:k_depth]
    top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
    top15_dense_scores = [float(dense_scores[idx]) for idx in top15_indices]

    # Cross-encoder reranking
    pairs = [[raw_q, chunks_by_id[cid]["text"]] for cid in top15_cids]
    raw_rerank_scores = reranker.predict(pairs)

    # Dual-Anchor Fusion + 0.85x Overview Debiasing
    adjusted_scores = []
    for cid, r_score, d_score in zip(top15_cids, raw_rerank_scores, top15_dense_scores):
        score = float(r_score)
        if cid.endswith("-HYB-000"):
            score *= overview_mult
        overlap = compute_token_overlap(raw_q, chunks_by_id[cid]["text"])
        final_score = score + (lambda_dense * d_score) + (alpha_lexical * overlap)
        adjusted_scores.append(final_score)

    ranked_indices = np.argsort(-np.array(adjusted_scores))
    final_cids = [top15_cids[i] for i in ranked_indices]
    final_scores = [adjusted_scores[i] for i in ranked_indices]

    if is_supported:
        # Candidate Stage Ranks
        dense_ranks = [top15_cids.index(gc) + 1 for gc in gold_cids if gc in top15_cids]
        best_dense_rank = min(dense_ranks) if dense_ranks else None
        dense_r5 = best_dense_rank is not None and best_dense_rank <= 5
        dense_r10 = best_dense_rank is not None and best_dense_rank <= 10
        dense_r15 = best_dense_rank is not None and best_dense_rank <= 15

        # Final Ranks
        final_ranks = [final_cids.index(gc) + 1 for gc in gold_cids if gc in final_cids]
        best_final_rank = min(final_ranks) if final_ranks else None
        chunk_r1 = best_final_rank is not None and best_final_rank == 1
        chunk_r3 = best_final_rank is not None and best_final_rank <= 3
        chunk_r5 = best_final_rank is not None and best_final_rank <= 5
        reciprocal_rank = (1.0 / best_final_rank) if best_final_rank is not None else 0.0

        # Source Level
        final_top1_sid = chunks_by_id[final_cids[0]]["parent_source_id"]
        source_r1 = final_top1_sid == expected_sid
        final_top5_sids = [chunks_by_id[cid]["parent_source_id"] for cid in final_cids[:5]]
        source_r5 = expected_sid in final_top5_sids

        # Availability Classification
        if chunk_r1:
            avail_class = "TOP1_CORRECT"
        elif chunk_r3:
            avail_class = "TOP1_WRONG_BUT_TOP3_HAS_GOLD"
        elif chunk_r5:
            avail_class = "TOP3_WRONG_BUT_TOP5_HAS_GOLD"
        else:
            avail_class = "GOLD_ABSENT_FROM_TOP5"

        # Dense vs Reranker Triage
        if not dense_r15:
            triage_class = "GOLD_OUTSIDE_DENSE15"
        elif dense_r15 and not chunk_r5:
            triage_class = "GOLD_IN_DENSE15_BUT_RERANKED_OUT"
        else:
            triage_class = "GOLD_IN_DENSE_TOP15"

        eval_record = {
            "query_id": qid,
            "language": lang,
            "query_type": q_type,
            "query_text": raw_q,
            "normalized_query": norm_q,
            "expected_source_id": expected_sid,
            "gold_chunk_ids": gold_cids,
            "best_dense_rank": best_dense_rank,
            "dense_r5": dense_r5,
            "dense_r10": dense_r10,
            "dense_r15": dense_r15,
            "best_final_rank": best_final_rank,
            "chunk_r1": chunk_r1,
            "chunk_r3": chunk_r3,
            "chunk_r5": chunk_r5,
            "chunk_mrr": reciprocal_rank,
            "source_r1": source_r1,
            "source_r5": source_r5,
            "availability_class": avail_class,
            "triage_class": triage_class,
            "final_top5_chunks": [
                {
                    "rank": idx + 1,
                    "chunk_id": final_cids[idx],
                    "parent_source_id": chunks_by_id[final_cids[idx]]["parent_source_id"],
                    "source_title": chunks_by_id[final_cids[idx]]["source_title"],
                    "fused_score": round(final_scores[idx], 4),
                    "is_gold": final_cids[idx] in gold_cids
                }
                for idx in range(min(5, len(final_cids)))
            ]
        }
        supported_evals.append(eval_record)
        per_query_results.append(eval_record)

    else:
        # Unsupported Query
        max_score = float(max(final_scores)) if final_scores else 0.0
        mean_score = float(np.mean(final_scores)) if final_scores else 0.0
        min_score = float(min(final_scores)) if final_scores else 0.0

        eval_record = {
            "query_id": qid,
            "language": lang,
            "query_type": q_type,
            "query_text": raw_q,
            "normalized_query": norm_q,
            "distractor_source_id": q.get("distractor_source_id"),
            "max_score": round(max_score, 4),
            "mean_score": round(mean_score, 4),
            "min_score": round(min_score, 4),
            "score_range": [round(min_score, 4), round(max_score, 4)],
            "final_top5_chunks": [
                {
                    "rank": idx + 1,
                    "chunk_id": final_cids[idx],
                    "parent_source_id": chunks_by_id[final_cids[idx]]["parent_source_id"],
                    "source_title": chunks_by_id[final_cids[idx]]["source_title"],
                    "fused_score": round(final_scores[idx], 4)
                }
                for idx in range(min(5, len(final_cids)))
            ]
        }
        unsupported_evals.append(eval_record)
        per_query_results.append(eval_record)

print("✓ All 50 queries evaluated.")

# -------------------------------------------------------------
# PHASE 3: COMPUTE SUPPORTED METRICS
# -------------------------------------------------------------
n_sup = len(supported_evals)

chunk_r1_cnt = sum(1 for e in supported_evals if e["chunk_r1"])
chunk_r3_cnt = sum(1 for e in supported_evals if e["chunk_r3"])
chunk_r5_cnt = sum(1 for e in supported_evals if e["chunk_r5"])
chunk_mrr = float(np.mean([e["chunk_mrr"] for e in supported_evals]))

dense_r5_cnt = sum(1 for e in supported_evals if e["dense_r5"])
dense_r10_cnt = sum(1 for e in supported_evals if e["dense_r10"])
dense_r15_cnt = sum(1 for e in supported_evals if e["dense_r15"])

source_r1_cnt = sum(1 for e in supported_evals if e["source_r1"])
source_r5_cnt = sum(1 for e in supported_evals if e["source_r5"])

# -------------------------------------------------------------
# PHASE 4: EVIDENCE AVAILABILITY CLASSIFICATION
# -------------------------------------------------------------
avail_summary = {
    "TOP1_CORRECT": sum(1 for e in supported_evals if e["availability_class"] == "TOP1_CORRECT"),
    "TOP1_WRONG_BUT_TOP3_HAS_GOLD": sum(1 for e in supported_evals if e["availability_class"] == "TOP1_WRONG_BUT_TOP3_HAS_GOLD"),
    "TOP3_WRONG_BUT_TOP5_HAS_GOLD": sum(1 for e in supported_evals if e["availability_class"] == "TOP3_WRONG_BUT_TOP5_HAS_GOLD"),
    "GOLD_ABSENT_FROM_TOP5": sum(1 for e in supported_evals if e["availability_class"] == "GOLD_ABSENT_FROM_TOP5")
}

triage_summary = {
    "GOLD_IN_DENSE_TOP15": sum(1 for e in supported_evals if e["triage_class"] == "GOLD_IN_DENSE_TOP15"),
    "GOLD_OUTSIDE_DENSE15": sum(1 for e in supported_evals if e["triage_class"] == "GOLD_OUTSIDE_DENSE15"),
    "GOLD_IN_DENSE15_BUT_RERANKED_OUT": sum(1 for e in supported_evals if e["triage_class"] == "GOLD_IN_DENSE15_BUT_RERANKED_OUT")
}

# -------------------------------------------------------------
# PHASE 5: LANGUAGE BREAKDOWN
# -------------------------------------------------------------
lang_breakdown = {}
for l in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
    l_evals = [e for e in supported_evals if e["language"] == l]
    if l_evals:
        l_n = len(l_evals)
        lang_breakdown[l] = {
            "n": l_n,
            "dense_recall_at_15": f"{sum(1 for e in l_evals if e['dense_r15'])}/{l_n} ({sum(1 for e in l_evals if e['dense_r15'])/l_n*100:.1f}%)",
            "chunk_recall_at_1": f"{sum(1 for e in l_evals if e['chunk_r1'])}/{l_n} ({sum(1 for e in l_evals if e['chunk_r1'])/l_n*100:.1f}%)",
            "chunk_recall_at_3": f"{sum(1 for e in l_evals if e['chunk_r3'])}/{l_n} ({sum(1 for e in l_evals if e['chunk_r3'])/l_n*100:.1f}%)",
            "chunk_recall_at_5": f"{sum(1 for e in l_evals if e['chunk_r5'])}/{l_n} ({sum(1 for e in l_evals if e['chunk_r5'])/l_n*100:.1f}%)",
            "chunk_mrr": round(float(np.mean([e["chunk_mrr"] for e in l_evals])), 4)
        }

# -------------------------------------------------------------
# PHASE 6: DOCUMENT BREAKDOWN
# -------------------------------------------------------------
doc_breakdown = {}
for sid in ["DOC-NHS-012", "DOC-NHS-013", "DOC-NHS-014", "DOC-NHS-015", "DOC-NHS-016", "DOC-NHS-017"]:
    d_evals = [e for e in supported_evals if e["expected_source_id"] == sid]
    if d_evals:
        d_n = len(d_evals)
        doc_breakdown[sid] = {
            "document_title": chunks_by_id[f"{sid}-HYB-000"]["source_title"],
            "supported_queries_count": d_n,
            "dense_recall_at_15": f"{sum(1 for e in d_evals if e['dense_r15'])}/{d_n} ({sum(1 for e in d_evals if e['dense_r15'])/d_n*100:.1f}%)",
            "chunk_recall_at_5": f"{sum(1 for e in d_evals if e['chunk_r5'])}/{d_n} ({sum(1 for e in d_evals if e['chunk_r5'])/d_n*100:.1f}%)",
            "chunk_mrr": round(float(np.mean([e["chunk_mrr"] for e in d_evals])), 4)
        }

# -------------------------------------------------------------
# PHASE 7: UNSUPPORTED QUERIES SUMMARY
# -------------------------------------------------------------
hn_evals = [e for e in unsupported_evals if e["query_type"] == "hard_negative_confounder"]
ooc_evals = [e for e in unsupported_evals if e["query_type"] == "out_of_corpus"]

unsupported_summary = {
    "hard_negatives": {
        "count": len(hn_evals),
        "max_score_overall": round(float(max(e["max_score"] for e in hn_evals)), 4) if hn_evals else 0.0,
        "mean_max_score": round(float(np.mean([e["max_score"] for e in hn_evals])), 4) if hn_evals else 0.0,
        "min_max_score": round(float(min(e["max_score"] for e in hn_evals)), 4) if hn_evals else 0.0,
        "per_query": hn_evals
    },
    "out_of_corpus": {
        "count": len(ooc_evals),
        "max_score_overall": round(float(max(e["max_score"] for e in ooc_evals)), 4) if ooc_evals else 0.0,
        "mean_max_score": round(float(np.mean([e["max_score"] for e in ooc_evals])), 4) if ooc_evals else 0.0,
        "min_max_score": round(float(min(e["max_score"] for e in ooc_evals)), 4) if ooc_evals else 0.0,
        "per_query": ooc_evals
    }
}

# -------------------------------------------------------------
# PHASE 8: FAILURE ANALYSIS
# -------------------------------------------------------------
failures = [e for e in supported_evals if not e["chunk_r5"]]
failure_analysis = []

for f in failures:
    top1_chunk = f["final_top5_chunks"][0]
    is_same_doc = top1_chunk["parent_source_id"] == f["expected_source_id"]
    
    analysis_entry = {
        "query_id": f["query_id"],
        "language": f["language"],
        "expected_source_id": f["expected_source_id"],
        "gold_chunk_ids": f["gold_chunk_ids"],
        "query_text": f["query_text"],
        "failure_mode": f["triage_class"],
        "dense_rank": f["best_dense_rank"],
        "final_rank": f["best_final_rank"],
        "top_competing_chunk": {
            "chunk_id": top1_chunk["chunk_id"],
            "parent_source_id": top1_chunk["parent_source_id"],
            "source_title": top1_chunk["source_title"],
            "score": top1_chunk["fused_score"],
            "same_document": is_same_doc
        },
        "verified_facts": [
            f"Gold chunk {f['gold_chunk_ids']} had dense rank {f['best_dense_rank']}.",
            f"Top retrieved chunk was {top1_chunk['chunk_id']} with score {top1_chunk['fused_score']}."
        ],
        "observations": [
            f"Query failed to place any gold chunk in final Top-5 context.",
            f"Triage class: {f['triage_class']}."
        ],
        "hypotheses": [
            "Dense bi-encoder failed to pull gold chunk into Top-15" if f["triage_class"] == "GOLD_OUTSIDE_DENSE15" else "Cross-encoder or debiasing suppressed gold chunk below competing passages."
        ]
    }
    failure_analysis.append(analysis_entry)

# -------------------------------------------------------------
# PHASE 9 & 10: ASSEMBLE SUMMARY & CLASSIFICATION
# -------------------------------------------------------------
r5_pct = chunk_r5_cnt / n_sup * 100
dense_r15_pct = dense_r15_cnt / n_sup * 100

if r5_pct >= 90.0 and dense_r15_pct >= 95.0:
    final_classification = "NEW_CORPUS_GENERALIZATION_SUPPORTED"
elif r5_pct >= 75.0:
    final_classification = "NEW_CORPUS_GENERALIZATION_PARTIAL"
else:
    final_classification = "NEW_CORPUS_GENERALIZATION_NOT_SUPPORTED"

results_summary = {
    "gate": "GATE_5.29",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "benchmark_name": benchmark_data.get("benchmark_name"),
    "locked_benchmark_sha256": actual_benchmark_sha256,
    "strategy_evaluated": frozen_cfg.get("candidate_name"),
    "strategy_config_sha256": actual_candidate_sha256,
    "final_classification": final_classification,
    "primary_metrics": {
        "chunk_recall_at_5": f"{chunk_r5_cnt}/{n_sup} ({r5_pct:.1f}%)"
    },
    "secondary_metrics": {
        "chunk_recall_at_1": f"{chunk_r1_cnt}/{n_sup} ({chunk_r1_cnt/n_sup*100:.1f}%)",
        "chunk_recall_at_3": f"{chunk_r3_cnt}/{n_sup} ({chunk_r3_cnt/n_sup*100:.1f}%)",
        "chunk_mrr": round(chunk_mrr, 4)
    },
    "candidate_stage_metrics": {
        "dense_recall_at_5": f"{dense_r5_cnt}/{n_sup} ({dense_r5_cnt/n_sup*100:.1f}%)",
        "dense_recall_at_10": f"{dense_r10_cnt}/{n_sup} ({dense_r10_cnt/n_sup*100:.1f}%)",
        "dense_recall_at_15": f"{dense_r15_cnt}/{n_sup} ({dense_r15_pct:.1f}%)"
    },
    "source_level_metrics": {
        "source_recall_at_1": f"{source_r1_cnt}/{n_sup} ({source_r1_cnt/n_sup*100:.1f}%)",
        "source_recall_at_5": f"{source_r5_cnt}/{n_sup} ({source_r5_cnt/n_sup*100:.1f}%)"
    },
    "evidence_availability_summary": avail_summary,
    "triage_summary": triage_summary,
    "language_breakdown": lang_breakdown,
    "document_breakdown": doc_breakdown,
    "unsupported_queries_summary": {
        "hard_negatives": {
            "count": len(hn_evals),
            "max_score_overall": unsupported_summary["hard_negatives"]["max_score_overall"],
            "mean_max_score": unsupported_summary["hard_negatives"]["mean_max_score"]
        },
        "out_of_corpus": {
            "count": len(ooc_evals),
            "max_score_overall": unsupported_summary["out_of_corpus"]["max_score_overall"],
            "mean_max_score": unsupported_summary["out_of_corpus"]["mean_max_score"]
        }
    },
    "failure_count": len(failures)
}

# Write All Artifacts
with open(os.path.join(EVALS_DIR, "gate_5_29_results.json"), "w", encoding="utf-8") as f:
    json.dump(results_summary, f, indent=2, ensure_ascii=False)

with open(os.path.join(EVALS_DIR, "gate_5_29_per_query_results.json"), "w", encoding="utf-8") as f:
    json.dump(per_query_results, f, indent=2, ensure_ascii=False)

with open(os.path.join(DIAG_DIR, "gate_5_29_failure_analysis.json"), "w", encoding="utf-8") as f:
    json.dump(failure_analysis, f, indent=2, ensure_ascii=False)

with open(os.path.join(PER_QUERY_DIR, "gate_5_29_per_query_details.json"), "w", encoding="utf-8") as f:
    json.dump(per_query_results, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 80)
print("GATE 5.29 SINGLE-SHOT VALIDATION RESULTS SUMMARY")
print("=" * 80)
print(f"Strategy:              {frozen_cfg.get('candidate_name')}")
print(f"Benchmark:             {benchmark_data.get('benchmark_name')} (N=40 Supported, 10 Unsupported)")
print(f"Final Classification:  {final_classification}")
print("-" * 80)
print(f"Primary Metric:        Chunk Recall@5 = {chunk_r5_cnt}/{n_sup} ({r5_pct:.1f}%)")
print(f"Secondary:             Chunk Recall@1 = {chunk_r1_cnt}/{n_sup} ({chunk_r1_cnt/n_sup*100:.1f}%)")
print(f"                       Chunk Recall@3 = {chunk_r3_cnt}/{n_sup} ({chunk_r3_cnt/n_sup*100:.1f}%)")
print(f"                       Chunk MRR      = {chunk_mrr:.4f}")
print(f"Candidate Stage:       Dense Recall@15 = {dense_r15_cnt}/{n_sup} ({dense_r15_pct:.1f}%)")
print(f"Source Level:          Source Recall@1 = {source_r1_cnt}/{n_sup} ({source_r1_cnt/n_sup*100:.1f}%)")
print(f"                       Source Recall@5 = {source_r5_cnt}/{n_sup} ({source_r5_cnt/n_sup*100:.1f}%)")
print("\nLanguage Breakdown:")
for l, data in lang_breakdown.items():
    print(f"  - {l:22s}: Chunk R@5={data['chunk_recall_at_5']:<16s} | MRR={data['chunk_mrr']:<6.4f} | Dense R@15={data['dense_recall_at_15']}")

print("\nDocument Breakdown:")
for sid, data in doc_breakdown.items():
    print(f"  - {sid} ({data['document_title'][:20]:<20s}): Chunk R@5={data['chunk_recall_at_5']:<16s} | MRR={data['chunk_mrr']:<6.4f} | Dense R@15={data['dense_recall_at_15']}")

print("\nUnsupported Queries:")
print(f"  - Hard Negatives (N=5): Max Score={unsupported_summary['hard_negatives']['max_score_overall']}, Mean Score={unsupported_summary['hard_negatives']['mean_max_score']}")
print(f"  - Out-of-Corpus  (N=5): Max Score={unsupported_summary['out_of_corpus']['max_score_overall']}, Mean Score={unsupported_summary['out_of_corpus']['mean_max_score']}")

print(f"\nFailures: {len(failures)} / {n_sup} queries failed Top-5 evidence retrieval.")
print("=" * 80)
