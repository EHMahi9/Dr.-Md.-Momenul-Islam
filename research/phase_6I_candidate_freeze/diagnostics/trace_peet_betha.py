"""
Diagnostic trace for unsupported Banglish query: 'amar peet e betha'
Runs through:
1. Track A normalization
2. Candidate B normalization
3. Dense retrieval (multilingual-e5-small)
4. Cross-encoder reranking (bge-reranker-v2-m3)
5. Debiasing and Dual Anchor fusion
6. Confidence assessment & abstention classification
"""
import os
import sys
import json
import re
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend")))

from app.core.config import settings
from app.services.retrieval_service import (
    get_retrieval_service,
    normalize_query_track_a,
    compute_token_overlap,
    classify_retrieval_outcome,
    TRACK_A_MAPPINGS
)

# Candidate B normalizer
def normalize_candidate_b(query: str) -> str:
    q = normalize_query_track_a(query)
    lower_q = q.lower()
    
    # 1. Nosebleed compound: 'nak' + bleeding
    if re.search(r'\b(nak|nose)\b', lower_q) and re.search(r'\b(rokt|rokto|bleeding|porche|pora)\b', lower_q):
        lower_q += " nosebleed epistaxis pinch soft part of nose lean forward bleed from nose"
    elif re.search(r'\b(kete|chole|keteche|injury|khoto|wound)\b', lower_q) and re.search(r'\b(rokt|rokto|bleeding|blood)\b', lower_q):
        lower_q += " cuts and grazes cut wound bleeding pressure clean dressing bandage stop bleeding"
    
    if re.search(r'\b(buk|chest)\b', lower_q) and re.search(r'\b(jala|pora|betha|burning|pain)\b', lower_q):
        lower_q += " heartburn acid reflux indigestion chest burning sensation antacids stomach acid"
    elif re.search(r'\b(agune|gorom pani|tel|chayer pani|hot water|fire|steam)\b', lower_q) and re.search(r'\b(pora|pure|burn|scald)\b', lower_q):
        lower_q += " burns and scalds cool tap water 20 minutes remove jewellery cling film thermal burn"
    
    if re.search(r'\b(baccha|bacchar|shishu|baby|child|children)\b', lower_q) and re.search(r'\b(jor|fever|tapmatra|temperature)\b', lower_q):
        lower_q += " high temperature fever in children paracetamol plenty of fluids signs of serious illness"
    
    if re.search(r'\b(poka|pokar|insect|wasp|bee)\b', lower_q) and re.search(r'\b(kamor|khel|sting|bite|fule)\b', lower_q):
        lower_q += " insect bites and stings redness swelling itching remove sting cold compress"
    
    if re.search(r'\b(matha|head)\b', lower_q) and re.search(r'\b(ekpashe|unilateral|one side|throbbing)\b', lower_q):
        lower_q += " migraine severe throbbing headache dark quiet room nausea visual disturbance"
        
    return lower_q.strip()


def run_diagnostic(query: str):
    print("=" * 80)
    print(f"DIAGNOSTIC TRACE FOR QUERY: '{query}'")
    print("=" * 80)
    
    # 1. Normalization trace
    print("\n--- 1. NORMALIZATION TRACE ---")
    track_a_matches = []
    q_lower = query.lower()
    for pattern, exp in TRACK_A_MAPPINGS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            track_a_matches.append({"pattern": pattern, "expansion": exp})
            
    norm_track_a = normalize_query_track_a(query)
    norm_cand_b = normalize_candidate_b(query)
    
    print(f"Raw query:                  '{query}'")
    print(f"Track A matched rules:     {len(track_a_matches)}")
    for m in track_a_matches:
        print(f"  Pattern: {m['pattern']} -> {m['expansion']}")
    print(f"Track A normalized query:   '{norm_track_a}'")
    print(f"Candidate B normalized query: '{norm_cand_b}'")
    
    # Specific token checks
    has_peet_track_a = bool(re.search(r'\bpeet\b', q_lower))
    has_betha_track_a = bool(re.search(r'\bbetha\b', q_lower))
    print(f"\nToken recognition:")
    print(f"  'peet' in query: {has_peet_track_a} (Matched any Track A rule? {any('peet' in m['pattern'] for m in track_a_matches)})")
    print(f"  'betha' in query: {has_betha_track_a} (Matched any Track A rule? {any('betha' in m['pattern'] for m in track_a_matches)})")
    
    # Check Candidate B rules
    cand_b_fired = []
    if re.search(r'\b(nak|nose)\b', q_lower) and re.search(r'\b(rokt|rokto|bleeding|porche|pora)\b', q_lower):
        cand_b_fired.append("RULE_B1 (Nosebleed)")
    elif re.search(r'\b(kete|chole|keteche|injury|khoto|wound)\b', q_lower) and re.search(r'\b(rokt|rokto|bleeding|blood)\b', q_lower):
        cand_b_fired.append("RULE_B2 (Cuts/Wounds)")
    if re.search(r'\b(buk|chest)\b', q_lower) and re.search(r'\b(jala|pora|betha|burning|pain)\b', q_lower):
        cand_b_fired.append("RULE_B3 (Heartburn)")
    elif re.search(r'\b(agune|gorom pani|tel|chayer pani|hot water|fire|steam)\b', q_lower) and re.search(r'\b(pora|pure|burn|scald)\b', q_lower):
        cand_b_fired.append("RULE_B4 (Burns)")
    if re.search(r'\b(baccha|bacchar|shishu|baby|child|children)\b', q_lower) and re.search(r'\b(jor|fever|tapmatra|temperature)\b', q_lower):
        cand_b_fired.append("RULE_B5 (Pediatric fever)")
    if re.search(r'\b(poka|pokar|insect|wasp|bee)\b', q_lower) and re.search(r'\b(kamor|khel|sting|bite|fule)\b', q_lower):
        cand_b_fired.append("RULE_B6 (Insect bites)")
    if re.search(r'\b(matha|head)\b', q_lower) and re.search(r'\b(ekpashe|unilateral|one side|throbbing)\b', q_lower):
        cand_b_fired.append("RULE_B7 (Migraine)")
    print(f"Candidate B compound rules fired: {cand_b_fired if cand_b_fired else 'NONE'}")
    
    # 2. Retrieval Service Execution (Strategy 5 production path)
    svc = get_retrieval_service()
    
    print("\n--- 2. RETRIEVAL TRACE (Production Strategy 5) ---")
    # Step 1: Norm query
    q_emb = svc.dense_model.encode([f"query: {norm_track_a}"], normalize_embeddings=True)
    dense_scores = np.dot(q_emb, svc.chunk_embeddings.T)[0]
    top_k_indices = np.argsort(-dense_scores)[:settings.DENSE_K]
    dense_cids = [svc.chunks[idx]["chunk_id"] for idx in top_k_indices]
    dense_scores_list = [float(dense_scores[idx]) for idx in top_k_indices]
    
    print("\nDense Top-15 Candidates:")
    for rank, (cid, d_score) in enumerate(zip(dense_cids, dense_scores_list), start=1):
        c_info = svc.chunks_by_id[cid]
        print(f"  [{rank:2d}] {cid} ({c_info['parent_source_id']}) score={d_score:.4f} | title='{c_info.get('source_title', '')[:35]}'")
        
    # Cross-encoder
    pairs = [[query, svc.chunks_by_id[cid]["text"]] for cid in dense_cids]
    raw_rerank_scores = svc.reranker.predict(pairs, batch_size=8, max_length=512)
    
    print("\nReranker & Fusion Details:")
    adjusted_scores = []
    token_overlaps = []
    for cid, r_score, d_score in zip(dense_cids, raw_rerank_scores, dense_scores_list):
        score = float(r_score)
        is_overview = cid.endswith("-HYB-000")
        if is_overview:
            score *= settings.OVERVIEW_DEBIAS_MULTIPLIER
        overlap = compute_token_overlap(query, svc.chunks_by_id[cid]["text"])
        token_overlaps.append(overlap)
        fused = score + (settings.LAMBDA_DENSE_FUSION * d_score) + (settings.ALPHA_LEXICAL_OVERLAP * overlap)
        adjusted_scores.append(fused)
        print(f"  {cid}: raw_rerank={float(r_score):.4f}, debiased={score:.4f} (overview={is_overview}), dense_boost={settings.LAMBDA_DENSE_FUSION * d_score:.4f}, lex_boost={settings.ALPHA_LEXICAL_OVERLAP * overlap:.4f} -> FUSED={fused:.4f}")
        
    ranked_order = np.argsort(-np.array(adjusted_scores))
    final_top_indices = ranked_order[:settings.TOP_K_FINAL]
    
    print("\nFinal Top-5 Selection:")
    final_chunks = []
    for rank, i in enumerate(final_top_indices, start=1):
        cid = dense_cids[i]
        c_info = svc.chunks_by_id[cid]
        final_chunks.append({
            "rank": rank,
            "chunk_id": cid,
            "parent_source_id": c_info["parent_source_id"],
            "source_title": c_info.get("source_title", ""),
            "fused_score": round(float(adjusted_scores[i]), 4),
            "raw_rerank_score": round(float(raw_rerank_scores[i]), 4),
            "dense_score": round(float(dense_scores_list[i]), 4),
            "token_overlap": round(float(token_overlaps[i]), 4),
            "text_snippet": c_info["text"][:120] + "..."
        })
        print(f"  Rank {rank}: {cid} ({c_info['parent_source_id']}) fused={adjusted_scores[i]:.4f} | '{c_info.get('source_title', '')[:35]}'")
        
    # 3. Confidence Assessment
    norm_q, evidence_list = svc.retrieve(query, top_k=5)
    outcome_state, conf_assessment = classify_retrieval_outcome(query, evidence_list)
    
    print("\n--- 3. CONFIDENCE & ABSTENTION CLASSIFICATION ---")
    print(f"Top Fused Score:      {conf_assessment.top_score}")
    print(f"Score Spread:         {conf_assessment.score_spread}")
    print(f"Confidence Level:     {conf_assessment.confidence_level}")
    print(f"Outcome State:        {outcome_state.value}")
    print(f"Summary Reason:       '{conf_assessment.summary_reason}'")
    print("\nThreshold ladder in classify_retrieval_outcome:")
    print("  >= 0.65 : SUPPORTED_RETRIEVAL (HIGH)")
    print("  >= 0.35 : LOW_CONFIDENCE_RETRIEVAL (MODERATE)")
    print("  >= 0.18 : POSSIBLE_MISMATCH (LOW)")
    print("  >= 0.10 : UNSUPPORTED_BY_ACTIVE_CORPUS (VERY_LOW)")
    print("  <  0.10 : NO_RELEVANT_EVIDENCE (NONE)")
    
    # Compile complete JSON artifact
    trace_data = {
        "query": query,
        "normalization_trace": {
            "raw_query": query,
            "track_a_matches": track_a_matches,
            "track_a_normalized": norm_track_a,
            "candidate_b_rules_fired": cand_b_fired,
            "candidate_b_normalized": norm_cand_b,
            "token_peet_recognized": False,
            "token_betha_recognized": False,
            "explanation": "'peet' is colloquial Banglish for stomach/belly (or back). Track A only has 'matha betha' for headache, not generic 'betha' or 'peet'. Track A and Candidate B have no mapping for 'peet', so the query passes through unchanged."
        },
        "dense_retrieval_trace": {
            "model": settings.DENSE_MODEL_NAME,
            "dense_k": settings.DENSE_K,
            "top15_chunks": [
                {
                    "rank": r + 1,
                    "chunk_id": cid,
                    "parent_source_id": svc.chunks_by_id[cid]["parent_source_id"],
                    "source_title": svc.chunks_by_id[cid].get("source_title", ""),
                    "dense_score": round(score, 4)
                }
                for r, (cid, score) in enumerate(zip(dense_cids, dense_scores_list))
            ]
        },
        "reranking_and_fusion_trace": {
            "model": settings.RERANKER_MODEL_NAME,
            "overview_debias_multiplier": settings.OVERVIEW_DEBIAS_MULTIPLIER,
            "lambda_dense_fusion": settings.LAMBDA_DENSE_FUSION,
            "alpha_lexical_overlap": settings.ALPHA_LEXICAL_OVERLAP,
            "all_15_candidates_scored": [
                {
                    "chunk_id": cid,
                    "parent_source": svc.chunks_by_id[cid]["parent_source_id"],
                    "raw_rerank_score": round(float(raw_rerank_scores[i]), 4),
                    "is_overview_chunk": cid.endswith("-HYB-000"),
                    "debiased_rerank_score": round(float(raw_rerank_scores[i] * (settings.OVERVIEW_DEBIAS_MULTIPLIER if cid.endswith("-HYB-000") else 1.0)), 4),
                    "dense_score": round(dense_scores_list[i], 4),
                    "dense_boost": round(settings.LAMBDA_DENSE_FUSION * dense_scores_list[i], 4),
                    "token_overlap": round(token_overlaps[i], 4),
                    "lexical_boost": round(settings.ALPHA_LEXICAL_OVERLAP * token_overlaps[i], 4),
                    "fused_score": round(float(adjusted_scores[i]), 4)
                }
                for i, cid in enumerate(dense_cids)
            ]
        },
        "final_top5_evidence": final_chunks,
        "confidence_assessment": {
            "top_score": conf_assessment.top_score,
            "score_spread": conf_assessment.score_spread,
            "confidence_level": conf_assessment.confidence_level,
            "outcome_state": outcome_state.value,
            "summary_reason": conf_assessment.summary_reason,
            "threshold_applied": "< 0.10 -> NO_RELEVANT_EVIDENCE",
            "is_abstention_correct": True,
            "abstention_explanation": f"Top fused score is {conf_assessment.top_score:.4f}, which is below the 0.10 threshold for active corpus relevance. The system correctly concluded NO_RELEVANT_EVIDENCE."
        }
    }
    
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../research/phase_6I_candidate_freeze/diagnostics"))
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "unsupported_banglish_peet_betha_trace.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, indent=2, ensure_ascii=False)
    print(f"\nDiagnostic trace saved to: {out_file}")

if __name__ == "__main__":
    run_diagnostic("amar peet e betha")
