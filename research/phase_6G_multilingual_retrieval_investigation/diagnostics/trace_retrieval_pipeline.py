"""
Phase 6G Diagnostic Script 2: Step-by-Step Retrieval Pipeline Trace
Inspects each step:
  1. Raw Query -> Modality Detection
  2. Normalization / Concept Expansion
  3. Multilingual E5 Dense Embedding & Top-15
  4. BGE Cross-Encoder Reranking
  5. Lexical Overlap Calculation
  6. Dual-Anchor Fusion (Rerank + Overview Debiasing + Lambda*Dense + Alpha*Lexical)
  7. Final Top-5 Selection & Gating Outcome
"""
import os
import sys
import json
import re
import numpy as np

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.core.config import settings
from app.services.retrieval_service import (
    normalize_query_track_a,
    compute_token_overlap,
    classify_retrieval_outcome,
    BaseRetrievalService
)
from sentence_transformers import SentenceTransformer, CrossEncoder

def main():
    print("=== INITIALIZING RETRIEVAL TRACE DIAGNOSTIC ===")
    manifest_path = settings.CORPUS_MANIFEST_PATH
    with open(manifest_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} active chunks from {manifest_path}")
    chunks_by_id = {c["chunk_id"]: c for c in chunks}

    print("Loading models on CPU...")
    dense_model = SentenceTransformer(settings.DENSE_MODEL_NAME, device="cpu")
    reranker = CrossEncoder(settings.RERANKER_MODEL_NAME, device="cpu")

    print("Pre-encoding passage embeddings...")
    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    benchmark_path = os.path.join(ROOT, "research", "phase_6F_grounded_generation_evaluation", "benchmark", "development_grounding_eval_set.json")
    with open(benchmark_path, "r", encoding="utf-8") as f:
        bench_data = json.load(f)
    bench_cases = bench_data["cases"] if "cases" in bench_data else bench_data

    # Focus cases for deep trace
    focus_case_ids = [
        "EVAL-10-BGL-SUP-NUMERIC",
        "EVAL-16-ABB-SUP-CONTRAINDICATION",
        "EVAL-08-BN-SUP-CONTRAINDICATION",
        "EVAL-09-BGL-SUP-PROCEDURAL",
        "EVAL-13-ABB-SUP-PROCEDURAL",
        "EVAL-14-ABB-SUP-NUMERIC",
        "EVAL-15-ABB-SUP-SEEKHELP"
    ]

    results = []

    for bcase in bench_cases:
        cid = bcase["id"]
        q_raw = bcase["query"]
        lang = bcase["language"]
        cat = bcase["category"]
        exp_sources = bcase.get("expected_sources", [])
        exp_facts = bcase.get("expected_key_facts", [])

        # 1. Normalization & Expansion
        q_norm = normalize_query_track_a(q_raw)

        # 2. Dense Retrieval
        q_emb = dense_model.encode([f"query: {q_norm}"], normalize_embeddings=True)[0]
        dense_sims = np.dot(chunk_embeddings, q_emb)
        top15_indices = np.argsort(dense_sims)[::-1][:settings.DENSE_K]

        dense_top15 = []
        for rank_d, idx in enumerate(top15_indices, start=1):
            c = chunks[idx]
            dense_top15.append({
                "dense_rank": rank_d,
                "chunk_id": c["chunk_id"],
                "parent_source_id": c["parent_source_id"],
                "source_title": c["source_title"],
                "dense_score": float(dense_sims[idx]),
                "text_snippet": c["text"][:120]
            })

        # 3. Cross-Encoder Reranking on Top-15
        pairs = [(q_norm, chunks[idx]["text"]) for idx in top15_indices]
        raw_ce_scores = reranker.predict(pairs)

        # 4. Lexical Overlap & Fusion
        fused_candidates = []
        for i, idx in enumerate(top15_indices):
            c = chunks[idx]
            dense_score = float(dense_sims[idx])
            ce_score = float(raw_ce_scores[i])
            is_overview = (c.get("chunk_type") == "overview")
            ce_debiased = ce_score * settings.OVERVIEW_DEBIAS_MULTIPLIER if is_overview else ce_score
            lex_score = compute_token_overlap(q_norm, c["text"])
            final_fused = ce_debiased + (settings.LAMBDA_DENSE_FUSION * dense_score) + (settings.ALPHA_LEXICAL_OVERLAP * lex_score)

            fused_candidates.append({
                "chunk_id": c["chunk_id"],
                "parent_source_id": c["parent_source_id"],
                "source_title": c["source_title"],
                "chunk_type": c.get("chunk_type", "body"),
                "dense_rank": i + 1,
                "dense_score": round(dense_score, 4),
                "ce_raw_score": round(ce_score, 4),
                "ce_debiased": round(ce_debiased, 4),
                "lexical_overlap": round(lex_score, 4),
                "fused_score": round(final_fused, 4),
                "text_snippet": c["text"][:120]
            })

        fused_sorted = sorted(fused_candidates, key=lambda x: x["fused_score"], reverse=True)
        for rank_f, fc in enumerate(fused_sorted, start=1):
            fc["final_rank"] = rank_f

        top5_final = fused_sorted[:settings.TOP_K_FINAL]

        # Check expected sources in Dense Top-15 vs Final Top-5
        top15_chunk_ids = [fc["chunk_id"] for fc in fused_candidates]
        top15_sources = [fc["parent_source_id"] for fc in fused_candidates]
        top5_chunk_ids = [fc["chunk_id"] for fc in top5_final]
        top5_sources = [fc["parent_source_id"] for fc in top5_final]

        gold_in_dense_top15 = any(s in top15_sources for s in exp_sources) if exp_sources else None
        gold_in_final_top5 = any(s in top5_sources for s in exp_sources) if exp_sources else None

        trace_record = {
            "case_id": cid,
            "language": lang,
            "category": cat,
            "query_raw": q_raw,
            "query_normalized": q_norm,
            "expected_sources": exp_sources,
            "gold_in_dense_top15": gold_in_dense_top15,
            "gold_in_final_top5": gold_in_final_top5,
            "top_fused_score": top5_final[0]["fused_score"] if top5_final else 0.0,
            "top5_final": top5_final,
            "dense_top15": dense_top15
        }
        results.append(trace_record)

        if cid in focus_case_ids:
            print(f"\n============================================================")
            print(f"FOCUS CASE: [{cid}] ({lang} | {cat})")
            print(f"Raw Query: '{q_raw}'")
            print(f"Normalized Query: '{q_norm}'")
            print(f"Expected Sources: {exp_sources}")
            print(f"Gold in Dense Top-15: {gold_in_dense_top15} | Gold in Final Top-5: {gold_in_final_top5}")
            print(f"Top-1 Fused Score: {top5_final[0]['fused_score']:.4f}")
            print(f"\nDense Top-15 Candidates:")
            for d in dense_top15[:8]:
                is_gold = d["parent_source_id"] in exp_sources
                marker = " [GOLD]" if is_gold else ""
                print(f"  Rank {d['dense_rank']}: {d['chunk_id']} ({d['parent_source_id']}) score={d['dense_score']:.4f}{marker} title='{d['source_title']}'")
            print(f"\nFinal Top-5 Fused:")
            for f in top5_final:
                is_gold = f["parent_source_id"] in exp_sources
                marker = " [GOLD]" if is_gold else ""
                print(f"  Final Rank {f['final_rank']} (Dense Rank {f['dense_rank']}): {f['chunk_id']} ({f['parent_source_id']}) fused={f['fused_score']:.4f} (ce={f['ce_debiased']:.4f}, dense={f['dense_score']:.4f}, lex={f['lexical_overlap']:.4f}){marker}")
                print(f"    Snippet: {f['text_snippet']}...")

    out_path = os.path.join(ROOT, "research", "phase_6G_multilingual_retrieval_investigation", "trace_analysis_48_cases.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved complete 48-case trace to {out_path}")

if __name__ == "__main__":
    main()
