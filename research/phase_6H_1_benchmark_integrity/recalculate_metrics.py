"""
Phase 6H.1: Re-evaluation of Phase 6H Experiment Metrics with Ground-Truth Corrected Targets
Audits what the metrics become when the benchmark targets are corrected to the authoritative active corpus manifest.
"""

import json
import numpy as np

def run_metric_audit():
    # 1. Load active corpus manifest
    manifest_path = "research/phase_6C/promoted_corpus_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    
    sources = {}
    for c in corpus:
        sid = c.get("parent_source_id", c["chunk_id"][:11])
        stitle = c.get("source_title", "").replace("\n", " ").strip()
        if sid not in sources:
            sources[sid] = stitle

    # 2. Load Phase 6H Results
    exp_res_path = "research/phase_6H_banglish_retrieval_experiment/outputs/phase_6H_experiment_results.json"
    with open(exp_res_path, "r", encoding="utf-8") as f:
        exp_data = json.load(f)

    # 3. Ground Truth Target Mapping for the 12 Challenge Cases
    # Note:
    # DEV-001 (Nosebleed): DOC-NHS-016 (Nosebleed) [was DOC-NHS-012]
    # DEV-002 (Cuts): DOC-NHS-006 (Cuts and grazes) [was DOC-NHS-006]
    # DEV-003 (Heartburn / post-eating chest burn): DOC-NHS-012 (Chest pain - Heartburn/indigestion) [was DOC-NHS-009]
    # DEV-004 (Burns): DOC-NHS-005 (Burns and scalds) [was DOC-NHS-005]
    # DEV-005 (Diarrhea / ORS): DOC-NHS-007 (Dehydration) or DOC-NHS-008 (Diarrhoea & vomiting) [was DOC-NHS-007]
    # DEV-006 (Child Fever): DOC-NHS-010 (High temp in children) [was DOC-NHS-010]
    # DEV-007 (Rash / Itch / Blister): OUT-OF-CORPUS (No Chickenpox in 14-condition corpus; closest is DOC-NHS-015 Meningitis rash or DOC-NHS-011 Anaphylaxis)
    # DEV-008 (Asthma): DOC-NHS-004 (Asthma) [was DOC-NHS-004]
    # DEV-009 (Eye infection / Conjunctivitis): OUT-OF-CORPUS (No Conjunctivitis in 14-condition corpus) [was DOC-NHS-016]
    # DEV-010 (Mouth ulcers): OUT-OF-CORPUS (No Mouth Ulcers in 14-condition corpus) [was DOC-NHS-014]
    # DEV-011 (Insect bite): DOC-NHS-011 (Anaphylaxis - wasp/bee sting) [was DOC-NHS-011]
    # DEV-012 (Headache / Migraine): DOC-NHS-009 (Headaches) [was DOC-NHS-017]
    
    corrected_challenge_targets = {
        "DEV-CHALLENGE-001": {"corr_target": "DOC-NHS-016", "in_corpus": True, "condition": "Nosebleed"},
        "DEV-CHALLENGE-002": {"corr_target": "DOC-NHS-006", "in_corpus": True, "condition": "Cuts and grazes"},
        "DEV-CHALLENGE-003": {"corr_target": "DOC-NHS-012", "in_corpus": True, "condition": "Chest pain / Heartburn"},
        "DEV-CHALLENGE-004": {"corr_target": "DOC-NHS-005", "in_corpus": True, "condition": "Burns and scalds"},
        "DEV-CHALLENGE-005": {"corr_target": ["DOC-NHS-007", "DOC-NHS-008"], "in_corpus": True, "condition": "Dehydration / Diarrhea"},
        "DEV-CHALLENGE-006": {"corr_target": "DOC-NHS-010", "in_corpus": True, "condition": "High temperature in children"},
        "DEV-CHALLENGE-007": {"corr_target": None, "in_corpus": False, "condition": "Chickenpox (OUT-OF-CORPUS)"},
        "DEV-CHALLENGE-008": {"corr_target": "DOC-NHS-004", "in_corpus": True, "condition": "Asthma"},
        "DEV-CHALLENGE-009": {"corr_target": None, "in_corpus": False, "condition": "Conjunctivitis (OUT-OF-CORPUS)"},
        "DEV-CHALLENGE-010": {"corr_target": None, "in_corpus": False, "condition": "Mouth ulcers (OUT-OF-CORPUS)"},
        "DEV-CHALLENGE-011": {"corr_target": "DOC-NHS-011", "in_corpus": True, "condition": "Anaphylaxis / Insect sting"},
        "DEV-CHALLENGE-012": {"corr_target": "DOC-NHS-009", "in_corpus": True, "condition": "Headaches (Migraine)"}
    }

    print("="*80)
    print("RECALCULATING METRICS FOR ALL 4 CANDIDATES ON IN-CORPUS CHALLENGE CASES (9 In-Corpus Cases)")
    print("="*80)

    for cand_name, cdata in exp_data["detailed_results"].items():
        dense_hits = 0
        r5_hits = 0
        r3_hits = 0
        r1_hits = 0
        rr_list = []
        
        in_corpus_count = 0
        all_12_dense_hits = 0
        all_12_r5_hits = 0
        all_12_r1_hits = 0
        all_12_rr_list = []

        print(f"\n--- {cand_name} ---")
        for cr in cdata["challenge_results"]:
            cid = cr["case_id"]
            q = cr["query"]
            info = corrected_challenge_targets[cid]
            target = info["corr_target"]
            in_corp = info["in_corpus"]
            
            top5_sids = [cid_chunk[:11] for cid_chunk in cr.get("top5_cids", [])]
            dense_sids = [cid_chunk[:11] for cid_chunk in cr.get("dense_candidates", [])]
            
            # Check hit
            def check_hit(sids, tgt):
                if tgt is None:
                    return False
                if isinstance(tgt, list):
                    return any(t in sids for t in tgt)
                return tgt in sids

            def get_rank(sids, tgt):
                if tgt is None:
                    return None
                if isinstance(tgt, list):
                    ranks = [sids.index(t) + 1 for t in tgt if t in sids]
                    return min(ranks) if ranks else None
                return sids.index(tgt) + 1 if tgt in sids else None

            dense_hit = check_hit(dense_sids, target)
            r5_hit = check_hit(top5_sids, target)
            r3_hit = check_hit(top5_sids[:3], target)
            rank = get_rank(top5_sids, target)
            r1_hit = (rank == 1)
            rr = (1.0 / rank) if rank else 0.0

            if in_corp:
                in_corpus_count += 1
                if dense_hit: dense_hits += 1
                if r5_hit: r5_hits += 1
                if r3_hit: r3_hits += 1
                if r1_hit: r1_hits += 1
                rr_list.append(rr)
                print(f"[{cid}] (IN-CORPUS) Target: {target} | Top-1: {top5_sids[0] if top5_sids else 'None'} | Hit: {r1_hit} (Rank: {rank})")
            else:
                print(f"[{cid}] (OUT-OF-CORPUS) Intended: {info['condition']} | Top-1: {top5_sids[0] if top5_sids else 'None'}")

        print(f"\nSummary on In-Corpus Cases (N={in_corpus_count}):")
        print(f"  Dense Recall@15: {dense_hits/in_corpus_count*100:.2f}% ({dense_hits}/{in_corpus_count})")
        print(f"  Final Recall@5:  {r5_hits/in_corpus_count*100:.2f}% ({r5_hits}/{in_corpus_count})")
        print(f"  Final Recall@3:  {r3_hits/in_corpus_count*100:.2f}% ({r3_hits}/{in_corpus_count})")
        print(f"  Top-1 Accuracy:  {r1_hits/in_corpus_count*100:.2f}% ({r1_hits}/{in_corpus_count})")
        print(f"  MRR:             {np.mean(rr_list):.4f}")

if __name__ == "__main__":
    run_metric_audit()
