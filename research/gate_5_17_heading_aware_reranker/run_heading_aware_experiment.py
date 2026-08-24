"""
Gate 5.17 — Development-Only Heading-Aware Reranker Experiment (DEV N=40)
Evaluates Baseline Control vs Experimental Heading-Aware Representation.
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

BASELINE_OUT_FILE = os.path.join(BASE_DIR, "baseline", "dev_baseline_results.json")
EXPERIMENT_OUT_FILE = os.path.join(BASE_DIR, "experiment", "dev_heading_aware_results.json")
COMPARISON_OUT_FILE = os.path.join(BASE_DIR, "comparisons", "gate_5_17_metric_comparison.json")
MOVEMENT_OUT_FILE = os.path.join(BASE_DIR, "diagnostics", "gate_5_17_failure_movement_analysis.json")

HEADING_PATTERNS = [
    r'^Immediate action required:.*$',
    r'^Urgent advice:.*$',
    r'^Non-urgent advice:.*$',
    r'^Important:.*$',
    r'^Information:.*$',
    r'^Warning:.*$',
    r'^See a GP if:.*$',
    r'^Call 999.*$',
    r'^Ask for an urgent.*$',
    r'^Get help from.*$',
    r'^How .*$',
    r'^Symptoms of .*$',
    r'^Causes of .*$',
    r'^Treatments? for .*$',
    r'^What to do .*$',
    r'^Things you can do .*$',
    r'^Help and support .*$',
    r'^Find out more.*$',
    r'^Do$',
    r'^Don\'?t$',
    r'^Video:.*$'
]

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

def is_heading_or_leadin(line: str) -> bool:
    line = line.strip()
    if not line:
        return False
    if line.endswith(':'):
        return True
    for pat in HEADING_PATTERNS:
        if re.match(pat, line, re.IGNORECASE):
            return True
    if len(line) <= 60 and not line.endswith(('.', ',', ';', '?', '!')) and '\n' not in line:
        return True
    return False

def extract_section_heading(chunk: dict) -> str:
    paragraphs = [p.strip() for p in chunk["text"].split("\n\n") if p.strip()]
    first_p = paragraphs[0] if paragraphs else ""
    lines = [l.strip() for l in first_p.split("\n") if l.strip()]
    first_line = lines[0] if lines else ""

    clean_source_title = chunk["source_title"].split("\n")[0].replace(" - NHS", "").strip()

    if is_heading_or_leadin(first_line):
        return first_line
    elif is_heading_or_leadin(first_p):
        return first_p.replace("\n", " ")
    else:
        return clean_source_title

def main():
    print("="*80)
    print("GATE 5.17: DEVELOPMENT-ONLY HEADING-AWARE RERANKER EXPERIMENT (N=40)")
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

    # Pre-extract headings for all chunks
    chunk_headings = {c["chunk_id"]: extract_section_heading(c) for c in chunks}

    print("Loading models on CPU...")
    dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

    # Encode passages for dense candidate search (IDENTICAL for both)
    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    # 1. Retrieve Dense Top-15 Candidates for all 40 DEV queries (IDENTICAL for both)
    print("Retrieving Dense Top-15 candidate pools...")
    dev_candidate_pools = []
    for q in dev_queries:
        qid = q["query_id"]
        raw_q = q["query_text"]
        norm_q = normalize_query_text(raw_q)
        gold = gold_labels[qid]
        acceptable_cids = gold["gold_chunk_ids"]
        expected_sid = q["expected_source_id"]

        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-dense_scores)[:15]
        dense_top15_cids = [chunks[idx]["chunk_id"] for idx in top15_indices]
        dense_top15_scores = [float(dense_scores[idx]) for idx in top15_indices]

        dev_candidate_pools.append({
            "query_id": qid,
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "language_category": q["language_category"],
            "expected_source_id": expected_sid,
            "gold_chunk_ids": acceptable_cids,
            "top15_indices": top15_indices,
            "dense_top15_cids": dense_top15_cids,
            "dense_top15_scores": dense_top15_scores
        })

    # 2. RUN CONTROL (BASELINE): {chunk_text}
    print("\n" + "="*80)
    print("RUNNING PIPELINE A: CONTROL BASELINE (RAW CHUNK TEXT)")
    print("="*80)

    t0_base = time.time()
    baseline_pairs_all = []
    for cp in dev_candidate_pools:
        norm_q = cp["normalized_query"]
        for idx in cp["top15_indices"]:
            baseline_pairs_all.append((norm_q, chunks[idx]["text"]))

    baseline_scores_flat = reranker.predict(baseline_pairs_all)
    latency_baseline = time.time() - t0_base
    print(f"Control Baseline inference completed in {latency_baseline:.2f}s ({latency_baseline/40:.3f}s/query)")

    # 3. RUN EXPERIMENTAL: Section: {heading}\nContent: {chunk_text}
    print("\n" + "="*80)
    print("RUNNING PIPELINE B: EXPERIMENTAL HEADING-AWARE REPRESENTATION")
    print("="*80)

    t0_exp = time.time()
    exp_pairs_all = []
    for cp in dev_candidate_pools:
        norm_q = cp["normalized_query"]
        for idx in cp["top15_indices"]:
            c = chunks[idx]
            hdr = chunk_headings[c["chunk_id"]]
            exp_text = f"Section: {hdr}\nContent: {c['text']}"
            exp_pairs_all.append((norm_q, exp_text))

    exp_scores_flat = reranker.predict(exp_pairs_all)
    latency_exp = time.time() - t0_exp
    print(f"Experimental inference completed in {latency_exp:.2f}s ({latency_exp/40:.3f}s/query)")

    # Evaluate both pipelines
    def evaluate_pipeline(scores_flat, pipeline_name):
        results = []
        pair_offset = 0
        for cp in dev_candidate_pools:
            qid = cp["query_id"]
            acceptable_cids = cp["gold_chunk_ids"]
            dense_cids = cp["dense_top15_cids"]
            n_cands = len(dense_cids)

            raw_scores = [float(s) for s in scores_flat[pair_offset : pair_offset + n_cands]]
            pair_offset += n_cands

            # 0.85x Overview debiasing (identical for both)
            adj_scores = []
            for i, cid in enumerate(dense_cids):
                s = raw_scores[i]
                if cid.endswith("-HYB-000"):
                    adj_scores.append(s * 0.85)
                else:
                    adj_scores.append(s)

            adj_scores = np.array(adj_scores)
            rerank_order = np.argsort(-adj_scores)

            rerank_cids = [dense_cids[i] for i in rerank_order]
            rerank_scores = [float(adj_scores[i]) for i in rerank_order]

            top5_cids = rerank_cids[:5]
            top5_scores = rerank_scores[:5]

            hits = [cid in acceptable_cids for cid in top5_cids]
            r1 = hits[0]
            r3 = any(hits[:3])
            r5 = any(hits[:5])

            all_hits = [cid in acceptable_cids for cid in rerank_cids]
            rank = (all_hits.index(True) + 1) if any(all_hits) else 0

            results.append({
                "query_id": qid,
                "language_category": cp["language_category"],
                "raw_query": cp["raw_query"],
                "gold_chunk_ids": acceptable_cids,
                "expected_source_id": cp["expected_source_id"],
                "dense_top15_cids": dense_cids,
                "rerank_top15_cids": rerank_cids,
                "rerank_top15_scores": rerank_scores,
                "final_top5_cids": top5_cids,
                "final_top5_scores": top5_scores,
                "r1": r1,
                "r3": r3,
                "r5": r5,
                "rank": rank,
                "gold_score": rerank_scores[rank - 1] if rank > 0 else 0.0,
                "top1_cid": rerank_cids[0],
                "top1_score": rerank_scores[0]
            })
        return results

    baseline_results = evaluate_pipeline(baseline_scores_flat, "CONTROL_BASELINE")
    exp_results = evaluate_pipeline(exp_scores_flat, "EXPERIMENTAL_HEADING_AWARE")

    # Aggregate Metrics Computation
    def compute_metrics(results):
        n = len(results)
        r1 = sum(1 for r in results if r["r1"])
        r3 = sum(1 for r in results if r["r3"])
        r5 = sum(1 for r in results if r["r5"])
        mrr = sum(1.0 / r["rank"] for r in results if r["rank"] > 0) / n

        lang_breakdown = {}
        for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]:
            subs = [r for r in results if r["language_category"] == lang]
            ln = len(subs)
            l_r1 = sum(1 for r in subs if r["r1"])
            l_r3 = sum(1 for r in subs if r["r3"])
            l_r5 = sum(1 for r in subs if r["r5"])
            l_mrr = sum(1.0 / r["rank"] for r in subs if r["rank"] > 0) / ln
            lang_breakdown[lang] = {
                "n": ln,
                "r1_count": f"{l_r1}/{ln}",
                "r1_pct": round(l_r1 / ln * 100, 2),
                "r3_count": f"{l_r3}/{ln}",
                "r3_pct": round(l_r3 / ln * 100, 2),
                "r5_count": f"{l_r5}/{ln}",
                "r5_pct": round(l_r5 / ln * 100, 2),
                "mrr": round(l_mrr, 4)
            }

        return {
            "n": n,
            "r1_count": f"{r1}/{n}",
            "r1_pct": round(r1 / n * 100, 2),
            "r3_count": f"{r3}/{n}",
            "r3_pct": round(r3 / n * 100, 2),
            "r5_count": f"{r5}/{n}",
            "r5_pct": round(r5 / n * 100, 2),
            "mrr": round(mrr, 4),
            "language_breakdown": lang_breakdown
        }

    base_metrics = compute_metrics(baseline_results)
    exp_metrics = compute_metrics(exp_results)

    # Save Individual Result Sets
    with open(BASELINE_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"metrics": base_metrics, "latency_seconds": latency_baseline, "queries": baseline_results}, f, indent=2, ensure_ascii=False)

    with open(EXPERIMENT_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"metrics": exp_metrics, "latency_seconds": latency_exp, "queries": exp_results}, f, indent=2, ensure_ascii=False)

    # 4. Failure Movement & Difference Analysis
    movement_analysis = []
    base_map = {r["query_id"]: r for r in baseline_results}
    exp_map = {r["query_id"]: r for r in exp_results}

    for qid, b_res in base_map.items():
        e_res = exp_map[qid]
        b_rank = b_res["rank"]
        e_rank = e_res["rank"]
        b_r5 = b_res["r5"]
        e_r5 = e_res["r5"]

        rank_diff = (b_rank != e_rank)
        improved = (e_rank < b_rank) if (b_rank > 0 and e_rank > 0) else (b_rank == 0 and e_rank > 0)
        degraded = (e_rank > b_rank) if (b_rank > 0 and e_rank > 0) else (e_rank == 0 and b_rank > 0)

        # Inspect Competing Chunks
        b_top1_cid = b_res["top1_cid"]
        e_top1_cid = e_res["top1_cid"]
        competing_is_same_doc = (chunks_by_id.get(e_top1_cid, {}).get("parent_source_id") == b_res["expected_source_id"])

        if rank_diff or (b_res["final_top5_cids"] != e_res["final_top5_cids"]):
            movement_analysis.append({
                "query_id": qid,
                "language": b_res["language_category"],
                "raw_query": b_res["raw_query"],
                "gold_chunk_ids": b_res["gold_chunk_ids"],
                "baseline_rank": b_rank,
                "experimental_rank": e_rank,
                "baseline_score": b_res["gold_score"],
                "experimental_score": e_res["gold_score"],
                "baseline_top1": b_top1_cid,
                "experimental_top1": e_top1_cid,
                "competing_chunk_is_same_doc": competing_is_same_doc,
                "improved": improved,
                "degraded": degraded,
                "baseline_top5": b_res["final_top5_cids"],
                "experimental_top5": e_res["final_top5_cids"]
            })

    # Save Movement Analysis
    with open(MOVEMENT_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "total_queries_with_rank_or_context_difference": len(movement_analysis),
            "improved_queries": [m["query_id"] for m in movement_analysis if m["improved"]],
            "degraded_queries": [m["query_id"] for m in movement_analysis if m["degraded"]],
            "differences": movement_analysis
        }, f, indent=2, ensure_ascii=False)

    # 5. Full Comparison Summary
    delta_r1 = exp_metrics["r1_pct"] - base_metrics["r1_pct"]
    delta_r3 = exp_metrics["r3_pct"] - base_metrics["r3_pct"]
    delta_r5 = exp_metrics["r5_pct"] - base_metrics["r5_pct"]
    delta_mrr = exp_metrics["mrr"] - base_metrics["mrr"]

    latency_rel_overhead = (latency_exp - latency_baseline) / latency_baseline * 100

    # Classification logic according to selection rule
    if delta_r5 > 0 and delta_mrr >= -0.02:
        classification = "HEADING_AWARE_RERANKER_SUPPORTED"
    elif delta_r5 == 0 and abs(delta_mrr) <= 0.01:
        classification = "HEADING_AWARE_RERANKER_NEUTRAL"
    else:
        classification = "HEADING_AWARE_RERANKER_REJECTED"

    comparison_summary = {
        "gate": "GATE_5.17",
        "timestamp": "2026-08-22T21:10:00+06:00",
        "hypothesis": "Adding the exact structural section heading to the reranker passage representation may reduce same-document section confusion.",
        "final_classification": classification,
        "sample_size": 40,
        "metrics_comparison": {
            "chunk_recall_at_1": {
                "baseline": base_metrics["r1_count"] + f" ({base_metrics['r1_pct']}%)",
                "experimental": exp_metrics["r1_count"] + f" ({exp_metrics['r1_pct']}%)",
                "delta": f"{delta_r1:+.2f}%"
            },
            "chunk_recall_at_3": {
                "baseline": base_metrics["r3_count"] + f" ({base_metrics['r3_pct']}%)",
                "experimental": exp_metrics["r3_count"] + f" ({exp_metrics['r3_pct']}%)",
                "delta": f"{delta_r3:+.2f}%"
            },
            "chunk_recall_at_5 (PRIMARY)": {
                "baseline": base_metrics["r5_count"] + f" ({base_metrics['r5_pct']}%)",
                "experimental": exp_metrics["r5_count"] + f" ({exp_metrics['r5_pct']}%)",
                "delta": f"{delta_r5:+.2f}%"
            },
            "chunk_mrr": {
                "baseline": base_metrics["mrr"],
                "experimental": exp_metrics["mrr"],
                "delta": round(delta_mrr, 4)
            }
        },
        "language_comparison": {
            lang: {
                "baseline_r5": base_metrics["language_breakdown"][lang]["r5_count"] + f" ({base_metrics['language_breakdown'][lang]['r5_pct']}%)",
                "experimental_r5": exp_metrics["language_breakdown"][lang]["r5_count"] + f" ({exp_metrics['language_breakdown'][lang]['r5_pct']}%)",
                "baseline_mrr": base_metrics["language_breakdown"][lang]["mrr"],
                "experimental_mrr": exp_metrics["language_breakdown"][lang]["mrr"]
            }
            for lang in ["English", "Native_Bangla", "Standard_Banglish", "Abbreviated_Banglish"]
        },
        "latency": {
            "baseline_seconds": round(latency_baseline, 2),
            "experimental_seconds": round(latency_exp, 2),
            "relative_overhead_pct": round(latency_rel_overhead, 2)
        }
    }

    with open(COMPARISON_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(comparison_summary, f, indent=2, ensure_ascii=False)

    print("\n" + "="*80)
    print("GATE 5.17 METRIC COMPARISON SUMMARY (DEV N=40)")
    print("="*80)
    print(f"Primary Metric (Chunk Recall@5): Baseline={base_metrics['r5_count']} ({base_metrics['r5_pct']}%) | Experimental={exp_metrics['r5_count']} ({exp_metrics['r5_pct']}%) | Delta={delta_r5:+.2f}%")
    print(f"Secondary Metric (Chunk MRR):     Baseline={base_metrics['mrr']} | Experimental={exp_metrics['mrr']} | Delta={delta_mrr:+.4f}")
    print(f"Secondary Metric (Chunk Recall@1): Baseline={base_metrics['r1_count']} ({base_metrics['r1_pct']}%) | Experimental={exp_metrics['r1_count']} ({exp_metrics['r1_pct']}%) | Delta={delta_r1:+.2f}%")
    print(f"Secondary Metric (Chunk Recall@3): Baseline={base_metrics['r3_count']} ({base_metrics['r3_pct']}%) | Experimental={exp_metrics['r3_count']} ({exp_metrics['r3_pct']}%) | Delta={delta_r3:+.2f}%")
    print(f"Latency: Baseline={latency_baseline:.2f}s | Experimental={latency_exp:.2f}s | Overhead={latency_rel_overhead:+.2f}%")
    print(f"\nFinal Classification: {classification}")

if __name__ == "__main__":
    main()
