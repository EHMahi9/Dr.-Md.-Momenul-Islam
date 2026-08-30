"""
Phase 6G Diagnostic: Fast Targeted Trace for Focus Cases with Immediate Flush
"""
import os
import sys
import json
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
    classify_retrieval_outcome
)
from sentence_transformers import SentenceTransformer, CrossEncoder

def main():
    print("=== INITIALIZING FAST TARGETED RETRIEVAL TRACE ===", flush=True)
    manifest_path = settings.CORPUS_MANIFEST_PATH
    with open(manifest_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} active chunks from {manifest_path}", flush=True)

    print("Loading models on CPU...", flush=True)
    dense_model = SentenceTransformer(settings.DENSE_MODEL_NAME, device="cpu")
    reranker = CrossEncoder(settings.RERANKER_MODEL_NAME, device="cpu")

    print("Pre-encoding passage embeddings...", flush=True)
    passage_texts = [f"passage: {c['text']}" for c in chunks]
    chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

    benchmark_path = os.path.join(ROOT, "research", "phase_6F_grounded_generation_evaluation", "benchmark", "development_grounding_eval_set.json")
    with open(benchmark_path, "r", encoding="utf-8") as f:
        bench_data = json.load(f)
    bench_cases = bench_data["cases"] if "cases" in bench_data else bench_data

    # Focus cases: all 7 RETRIEVAL_FAILURE cases + 2 key baseline cases
    focus_ids = [
        "EVAL-01-ENG-SUP-PROCEDURAL",
        "EVAL-08-BN-SUP-CONTRAINDICATION",
        "EVAL-09-BGL-SUP-PROCEDURAL",
        "EVAL-10-BGL-SUP-NUMERIC",
        "EVAL-13-ABB-SUP-PROCEDURAL",
        "EVAL-14-ABB-SUP-NUMERIC",
        "EVAL-15-ABB-SUP-SEEKHELP",
        "EVAL-16-ABB-SUP-CONTRAINDICATION",
        "EVAL-32-BN-UNSUP-NONCORPUS"
    ]

    selected_cases = [c for c in bench_cases if c["id"] in focus_ids]
    print(f"Executing trace on {len(selected_cases)} selected cases...", flush=True)

    out_records = []

    for bcase in selected_cases:
        cid = bcase["id"]
        q_raw = bcase["query"]
        lang = bcase["language"]
        cat = bcase["category"]
        exp_sources = bcase.get("expected_sources", [])

        # 1. Normalization
        q_norm = normalize_query_track_a(q_raw)

        # 2. Dense retrieval
        q_emb = dense_model.encode([f"query: {q_norm}"], normalize_embeddings=True)[0]
        dense_sims = np.dot(chunk_embeddings, q_emb)
        top15_indices = np.argsort(dense_sims)[::-1][:settings.DENSE_K]

        # 3. Cross-Encoder reranking
        pairs = [(q_norm, chunks[idx]["text"]) for idx in top15_indices]
        raw_ce_scores = reranker.predict(pairs)

        # 4. Fusion
        fused = []
        for i, idx in enumerate(top15_indices):
            c = chunks[idx]
            dense_score = float(dense_sims[idx])
            ce_score = float(raw_ce_scores[i])
            is_overview = (c.get("chunk_type") == "overview")
            ce_deb = ce_score * settings.OVERVIEW_DEBIAS_MULTIPLIER if is_overview else ce_score
            lex = compute_token_overlap(q_norm, c["text"])
            final = ce_deb + (settings.LAMBDA_DENSE_FUSION * dense_score) + (settings.ALPHA_LEXICAL_OVERLAP * lex)

            fused.append({
                "chunk_id": c["chunk_id"],
                "parent_source_id": c["parent_source_id"],
                "source_title": c["source_title"],
                "chunk_type": c.get("chunk_type", "body"),
                "dense_rank": i + 1,
                "dense_score": round(dense_score, 4),
                "ce_raw_score": round(ce_score, 4),
                "ce_debiased": round(ce_deb, 4),
                "lexical_overlap": round(lex, 4),
                "fused_score": round(final, 4),
                "text_snippet": c["text"][:140]
            })

        fused_sorted = sorted(fused, key=lambda x: x["fused_score"], reverse=True)
        for rf, item in enumerate(fused_sorted, start=1):
            item["final_rank"] = rf

        top5 = fused_sorted[:settings.TOP_K_FINAL]

        dense_sources = [f["parent_source_id"] for f in fused]
        final_sources = [f["parent_source_id"] for f in top5]

        gold_in_d15 = any(s in dense_sources for s in exp_sources) if exp_sources else None
        gold_in_f5 = any(s in final_sources for s in exp_sources) if exp_sources else None

        rec = {
            "case_id": cid,
            "language": lang,
            "category": cat,
            "query_raw": q_raw,
            "query_normalized": q_norm,
            "expected_sources": exp_sources,
            "gold_in_dense_top15": gold_in_d15,
            "gold_in_final_top5": gold_in_f5,
            "top_fused_score": top5[0]["fused_score"] if top5 else 0.0,
            "fused_top5": top5,
            "dense_top15": fused
        }
        out_records.append(rec)

        print(f"\n============================================================", flush=True)
        print(f"CASE: [{cid}] ({lang} | {cat})", flush=True)
        print(f"  Raw Query: '{q_raw}'", flush=True)
        print(f"  Normalized: '{q_norm}'", flush=True)
        print(f"  Expected Sources: {exp_sources}", flush=True)
        print(f"  Gold in Dense Top-15: {gold_in_d15} | Gold in Final Top-5: {gold_in_f5}", flush=True)
        print(f"  Top Fused Score: {top5[0]['fused_score']:.4f}", flush=True)
        print(f"  --- Dense Top-15 Candidates ---", flush=True)
        for d in fused[:6]:
            marker = " [GOLD]" if d["parent_source_id"] in exp_sources else ""
            print(f"    Dense Rank {d['dense_rank']}: {d['chunk_id']} ({d['parent_source_id']}) score={d['dense_score']:.4f}{marker} title='{d['source_title']}'", flush=True)
        print(f"  --- Final Top-5 Fused ---", flush=True)
        for f in top5:
            marker = " [GOLD]" if f["parent_source_id"] in exp_sources else ""
            print(f"    Final Rank {f['final_rank']} (Dense Rank {f['dense_rank']}): {f['chunk_id']} ({f['parent_source_id']}) fused={f['fused_score']:.4f} (ce={f['ce_debiased']:.4f}, d={f['dense_score']:.4f}, lex={f['lexical_overlap']:.4f}){marker}", flush=True)
            print(f"      '{f['text_snippet']}...'", flush=True)

    out_path = os.path.join(ROOT, "research", "phase_6G_multilingual_retrieval_investigation", "targeted_trace_focus_cases.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_records, f, indent=2)
    print(f"\nSaved targeted trace results to: {out_path}", flush=True)

if __name__ == "__main__":
    main()
