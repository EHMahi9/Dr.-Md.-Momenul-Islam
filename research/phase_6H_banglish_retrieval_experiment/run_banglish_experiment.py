"""
Phase 6H: Development-Only Banglish Retrieval Improvement Experiment
Compares:
1. CONTROL: Frozen Strategy 5 Normalization
2. Candidate A: Targeted Transliteration Normalization
3. Candidate B: Context-Aware Compound Disambiguation
4. Candidate C: Integrated Track A Hybrid (A + B)

Evaluates on:
- 12-case Development Banglish Challenge Set
- 12-case Regression Control Set (6 English + 6 Native Bangla)

Metrics:
- Dense Recall@15
- Final Recall@5, Recall@3, Recall@1 (Top-1 Accuracy)
- MRR
- Cross-Condition Contamination Rate
- Regression Count vs CONTROL
"""

import time
import json
import os
import sys
import re
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.services.retrieval_service import get_retrieval_service, normalize_query_track_a, compute_token_overlap
from app.core.config import settings

# ==============================================================================
# NORMALIZATION CANDIDATES
# ==============================================================================

def normalize_control(query: str) -> str:
    """CONTROL: Current frozen Track A normalization."""
    return normalize_query_track_a(query)

def normalize_candidate_a(query: str) -> str:
    """
    Candidate A: Targeted Transliteration Normalization.
    Expands high-frequency transliterated colloquial tokens into clinical concepts.
    """
    q = normalize_query_track_a(query)
    lower_q = q.lower()
    
    # 1:1 Transliteration & Colloquial Expansions
    trans_map = [
        (r'\b(rokt|rokto)\b', 'bleeding blood'),
        (r'\b(pet kharap|patla paykhana)\b', 'diarrhoea vomiting dehydration oral rehydration salts'),
        (r'\b(shorir betha|gaa betha|ga betha)\b', 'body ache fever high temperature paracetamol'),
        (r'\b(chulkani|lal guti)\b', 'itchy rash spots blister chickenpox'),
        (r'\b(shash nite koshto|shosh shobdo)\b', 'breathlessness difficulty breathing wheezing asthma inhaler'),
        (r'\b(pishti|chokh jole)\b', 'sticky eye discharge conjunctivitis watery eyes'),
        (r'\b(mukhe gha|mukhe lal gha)\b', 'mouth ulcers sore painful ulcer inside mouth'),
        (r'\b(pokar kamor|poka kamor)\b', 'insect bites and stings bee wasp spider bite redness swelling'),
        (r'\b(mathar ekpashe betha|ekpashe betha)\b', 'migraine one-sided throbbing headache nausea sensitivity to light'),
        (r'\b(napa|paracitamol|parasitamol)\b', 'paracetamol medication fever pain relief')
    ]
    
    for pat, repl in trans_map:
        lower_q = re.sub(pat, repl, lower_q)
        
    return lower_q.strip()

def normalize_candidate_b(query: str) -> str:
    """
    Candidate B: Context-Aware Compound Disambiguation.
    Detects multi-token compound patterns with anatomical site grounding to strictly route
    queries and avoid cross-condition contamination.
    """
    q = normalize_query_track_a(query)
    lower_q = q.lower()
    
    # Compound Rules with Contextual Isolation
    # 1. Nosebleed compound: 'nak' + bleeding
    if re.search(r'\b(nak|nose)\b', lower_q) and re.search(r'\b(rokt|rokto|bleeding|porche|pora)\b', lower_q):
        lower_q += " nosebleed epistaxis pinch soft part of nose lean forward bleed from nose"
        
    # 2. Cut / Wound compound: trauma ('kete'/'chole'/'ghotona') + bleeding
    elif re.search(r'\b(kete|chole|keteche|injury|khoto|wound)\b', lower_q) and re.search(r'\b(rokt|rokto|bleeding|blood)\b', lower_q):
        lower_q += " cuts and grazes cut wound bleeding pressure clean dressing bandage stop bleeding"
        
    # 3. Heartburn compound: 'buk' + burning/pain
    if re.search(r'\b(buk|chest)\b', lower_q) and re.search(r'\b(jala|pora|betha|burning|pain)\b', lower_q):
        lower_q += " heartburn acid reflux indigestion chest burning sensation antacids stomach acid"
        
    # 4. Thermal Burns compound: thermal agent ('agune'/'gorom pani'/'tel'/'chaye') + 'pora'/'pure'
    elif re.search(r'\b(agune|gorom pani|tel|chayer pani|hot water|fire|steam)\b', lower_q) and re.search(r'\b(pora|pure|burn|scald)\b', lower_q):
        lower_q += " burns and scalds cool tap water 20 minutes remove jewellery cling film thermal burn"
        
    # 5. Pediatric fever: 'baccha'/'shishu' + 'jor'/'fever'
    if re.search(r'\b(baccha|bacchar|shishu|baby|child|children)\b', lower_q) and re.search(r'\b(jor|fever|tapmatra|temperature)\b', lower_q):
        lower_q += " high temperature fever in children paracetamol plenty of fluids signs of serious illness"
        
    # 6. Insect bites: 'pokar kamor'
    if re.search(r'\b(poka|pokar|insect|wasp|bee)\b', lower_q) and re.search(r'\b(kamor|khel|sting|bite|fule)\b', lower_q):
        lower_q += " insect bites and stings redness swelling itching remove sting cold compress"
        
    # 7. Migraine: 'mathar ekpashe' + betha
    if re.search(r'\b(matha|head)\b', lower_q) and re.search(r'\b(ekpashe|unilateral|one side|throbbing)\b', lower_q):
        lower_q += " migraine severe throbbing headache dark quiet room nausea visual disturbance"
        
    return lower_q.strip()

def normalize_candidate_c(query: str) -> str:
    """
    Candidate C: Integrated Track A Hybrid (A + B).
    Two-stage pipeline: atomic transliteration normalization followed by contextual compound disambiguation.
    """
    stage1 = normalize_candidate_a(query)
    stage2 = normalize_candidate_b(stage1)
    return stage2

# ==============================================================================
# RETRIEVAL EXECUTION WITH ARBITRARY NORMALIZATION
# ==============================================================================

def execute_retrieval_with_normalizer(svc, query: str, normalizer_fn, top_k: int = 5):
    """Executes Strategy 5 pipeline with candidate normalizer."""
    norm_query = normalizer_fn(query)
    
    # Dense Retrieval (Top-15)
    q_emb = svc.dense_model.encode([f"query: {norm_query}"], normalize_embeddings=True)
    dense_scores = np.dot(q_emb, svc.chunk_embeddings.T)[0]
    top_k_indices = np.argsort(-dense_scores)[:settings.DENSE_K]
    candidate_cids = [svc.chunks[idx]["chunk_id"] for idx in top_k_indices]
    candidate_dense_scores = [float(dense_scores[idx]) for idx in top_k_indices]
    
    # Cross-Encoder Reranking (bs=8, max_length=512)
    pairs = [[query, svc.chunks_by_id[cid]["text"]] for cid in candidate_cids]
    raw_rerank_scores = svc.reranker.predict(pairs, batch_size=8, max_length=512)
    
    # Overview Debiasing & Dual Anchor Fusion
    adjusted_scores = []
    token_overlaps = []
    
    for cid, r_score, d_score in zip(candidate_cids, raw_rerank_scores, candidate_dense_scores):
        score = float(r_score)
        if cid.endswith("-HYB-000"):
            score *= settings.OVERVIEW_DEBIAS_MULTIPLIER
            
        overlap = compute_token_overlap(query, svc.chunks_by_id[cid]["text"])
        token_overlaps.append(overlap)
        
        final_score = score + (settings.LAMBDA_DENSE_FUSION * d_score) + (settings.ALPHA_LEXICAL_OVERLAP * overlap)
        adjusted_scores.append(final_score)
        
    ranked_order = np.argsort(-np.array(adjusted_scores))
    final_top_indices = ranked_order[:top_k]
    
    final_cids = [candidate_cids[i] for i in final_top_indices]
    final_scores = [round(float(adjusted_scores[i]), 4) for i in final_top_indices]
    
    return {
        "norm_query": norm_query,
        "dense_candidates": candidate_cids,
        "dense_scores": [round(s, 4) for s in candidate_dense_scores],
        "top5_cids": final_cids,
        "top5_scores": final_scores,
        "top_chunk": final_cids[0] if final_cids else None,
        "top_score": final_scores[0] if final_scores else None
    }

# ==============================================================================
# MAIN BENCHMARK RUNNER
# ==============================================================================

def main():
    print("="*80)
    print("PHASE 6H: DEVELOPMENT-ONLY BANGLISH RETRIEVAL IMPROVEMENT EXPERIMENT")
    print("="*80)
    
    svc = get_retrieval_service()
    
    # 1. Load Challenge Dataset
    challenge_path = "research/phase_6G_2_runtime_and_banglish/banglish_challenge_dataset.json"
    with open(challenge_path, "r", encoding="utf-8") as f:
        challenge_cases = json.load(f)
        
    # 2. Regression Control Set (6 English + 6 Native Bangla)
    regression_cases = [
        {"case_id": "REG-EN-001", "lang": "English", "query": "how to treat minor burns with cool water", "expected_doc_id": "DOC-NHS-005"},
        {"case_id": "REG-EN-002", "lang": "English", "query": "clean cut or graze with clean water and dressing", "expected_doc_id": "DOC-NHS-006"},
        {"case_id": "REG-EN-003", "lang": "English", "query": "what are symptoms of measles in children", "expected_doc_id": "DOC-NHS-013"},
        {"case_id": "REG-EN-004", "lang": "English", "query": "how to treat diarrhea with oral rehydration salts", "expected_doc_id": "DOC-NHS-007"},
        {"case_id": "REG-EN-005", "lang": "English", "query": "child high temperature fever paracetamol fluids", "expected_doc_id": "DOC-NHS-010"},
        {"case_id": "REG-EN-006", "lang": "English", "query": "how to stop a nosebleed by pinching nose and leaning forward", "expected_doc_id": "DOC-NHS-012"},
        {"case_id": "REG-BN-001", "lang": "Bangla", "query": "বাচ্চার জ্বর হলে করণীয় কি?", "expected_doc_id": "DOC-NHS-010"},
        {"case_id": "REG-BN-002", "lang": "Bangla", "query": "কাটা বা ছড়ে যাওয়ার প্রাথমিক চিকিৎসা কি?", "expected_doc_id": "DOC-NHS-006"},
        {"case_id": "REG-BN-003", "lang": "Bangla", "query": "ডায়রিয়া হলে কি স্যালাইন খেতে হবে?", "expected_doc_id": "DOC-NHS-007"},
        {"case_id": "REG-BN-004", "lang": "Bangla", "query": "হামের লক্ষণ কি কি?", "expected_doc_id": "DOC-NHS-013"},
        {"case_id": "REG-BN-005", "lang": "Bangla", "query": "হাত পুড়ে গেলে ঠান্ডা পানি দিতে হবে?", "expected_doc_id": "DOC-NHS-005"},
        {"case_id": "REG-BN-006", "lang": "Bangla", "query": "নাক দিয়ে রক্ত পড়লে কি করতে হবে?", "expected_doc_id": "DOC-NHS-012"}
    ]
    
    candidates = [
        ("CONTROL", normalize_control),
        ("Candidate A (Targeted Transliteration)", normalize_candidate_a),
        ("Candidate B (Context Disambiguation)", normalize_candidate_b),
        ("Candidate C (Integrated Hybrid A+B)", normalize_candidate_c)
    ]
    
    candidate_metrics = {}
    candidate_case_results = {}
    
    for cand_name, norm_fn in candidates:
        print(f"\n" + "="*70)
        print(f"EVALUATING CANDIDATE: {cand_name}")
        print("="*70)
        
        # A. Evaluate Challenge Set (12 Banglish cases)
        challenge_results = []
        dense_hits = 0
        r5_hits = 0
        r3_hits = 0
        r1_hits = 0
        rr_sum = 0.0
        contamination_count = 0
        
        for c in challenge_cases:
            res = execute_retrieval_with_normalizer(svc, c["query"], norm_fn, top_k=5)
            target_doc = c["expected_doc_id"]
            
            # Check dense recall@15
            dense_sids = [cid[:11] for cid in res["dense_candidates"]]
            dense_hit = target_doc in dense_sids
            if dense_hit:
                dense_hits += 1
                
            # Check final top-5 ranks
            top5_sids = [cid[:11] for cid in res["top5_cids"]]
            r5_hit = target_doc in top5_sids
            r3_hit = target_doc in top5_sids[:3]
            r1_hit = target_doc in top5_sids[:1]
            
            if r5_hit:
                r5_hits += 1
            if r3_hit:
                r3_hits += 1
            if r1_hit:
                r1_hits += 1
                
            # Reciprocal rank
            rank = None
            if target_doc in top5_sids:
                rank = top5_sids.index(target_doc) + 1
                rr_sum += 1.0 / rank
                
            # Check known cross-condition contamination
            is_contaminated = False
            if target_doc == "DOC-NHS-012" and "DOC-NHS-006" in top5_sids:
                is_contaminated = True
            elif target_doc == "DOC-NHS-009" and "DOC-NHS-005" in top5_sids:
                is_contaminated = True
            elif target_doc == "DOC-NHS-011" and "DOC-NHS-008" in top5_sids:
                is_contaminated = True
            if is_contaminated:
                contamination_count += 1
                
            print(f"[{c['case_id']}] '{c['query'][:45]}...' -> Target: {target_doc} | Dense Hit: {dense_hit} | Top-1: {res['top_chunk'][:11]} (Hit: {r1_hit}, Rank: {rank})")
            
            challenge_results.append({
                "case_id": c["case_id"],
                "query": c["query"],
                "expected_doc_id": target_doc,
                "dense_hit": dense_hit,
                "r5_hit": r5_hit,
                "r3_hit": r3_hit,
                "r1_hit": r1_hit,
                "rank": rank,
                "is_contaminated": is_contaminated,
                "top_chunk": res["top_chunk"],
                "top_score": res["top_score"],
                "top5_cids": res["top5_cids"]
            })
            
        n_chal = len(challenge_cases)
        mrr = round(rr_sum / n_chal, 4)
        dense_r15_pct = round(dense_hits / n_chal * 100, 2)
        r5_pct = round(r5_hits / n_chal * 100, 2)
        r3_pct = round(r3_hits / n_chal * 100, 2)
        r1_pct = round(r1_hits / n_chal * 100, 2)
        contam_pct = round(contamination_count / n_chal * 100, 2)
        
        # B. Evaluate Regression Control Set (12 cases)
        regression_results = []
        reg_r1_hits = 0
        reg_r5_hits = 0
        for reg in regression_cases:
            res = execute_retrieval_with_normalizer(svc, reg["query"], norm_fn, top_k=5)
            target_doc = reg["expected_doc_id"]
            top5_sids = [cid[:11] for cid in res["top5_cids"]]
            r1_hit = target_doc in top5_sids[:1]
            r5_hit = target_doc in top5_sids
            if r1_hit:
                reg_r1_hits += 1
            if r5_hit:
                reg_r5_hits += 1
            regression_results.append({
                "case_id": reg["case_id"],
                "lang": reg["lang"],
                "query": reg["query"],
                "target_doc": target_doc,
                "r1_hit": r1_hit,
                "r5_hit": r5_hit,
                "top_chunk": res["top_chunk"]
            })
            
        candidate_metrics[cand_name] = {
            "dense_recall_at_15_pct": dense_r15_pct,
            "recall_at_5_pct": r5_pct,
            "recall_at_3_pct": r3_pct,
            "top1_accuracy_pct": r1_pct,
            "mrr": mrr,
            "cross_condition_contamination_rate_pct": contam_pct,
            "regression_control_top1_accuracy_pct": round(reg_r1_hits / len(regression_cases) * 100, 2),
            "regression_control_recall_at_5_pct": round(reg_r5_hits / len(regression_cases) * 100, 2)
        }
        
        candidate_case_results[cand_name] = {
            "challenge_results": challenge_results,
            "regression_results": regression_results
        }
        
        print(f"\n--- {cand_name} Summary ---")
        print(f"Dense Recall@15: {dense_r15_pct}%")
        print(f"Final Recall@5:  {r5_pct}%")
        print(f"Top-1 Accuracy:  {r1_pct}%")
        print(f"MRR:             {mrr}")
        print(f"Contamination:   {contam_pct}%")
        print(f"Regression Top1: {round(reg_r1_hits/len(regression_cases)*100, 1)}%")

    # Print Comparison Table
    print("\n" + "="*80)
    print("PHASE 6H EXPERIMENT COMPARISON TABLE")
    print("="*80)
    print(f"{'Candidate':<40} | {'Dense R@15':<10} | {'Final R@5':<10} | {'Top-1 Acc':<10} | {'MRR':<8} | {'Contam %':<8} | {'Reg Top1'}")
    print("-" * 105)
    for cand_name, m in candidate_metrics.items():
        print(f"{cand_name:<40} | {m['dense_recall_at_15_pct']:<10}% | {m['recall_at_5_pct']:<10}% | {m['top1_accuracy_pct']:<10}% | {m['mrr']:<8} | {m['cross_condition_contamination_rate_pct']:<8}% | {m['regression_control_top1_accuracy_pct']}%")
        
    out_data = {
        "phase": "6H",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "challenge_cases_count": len(challenge_cases),
        "regression_cases_count": len(regression_cases),
        "candidate_summary_metrics": candidate_metrics,
        "detailed_results": candidate_case_results
    }
    
    out_file = "research/phase_6H_banglish_retrieval_experiment/outputs/phase_6H_experiment_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)
        
    print(f"\nSaved full experiment results to: {out_file}")

if __name__ == "__main__":
    main()
