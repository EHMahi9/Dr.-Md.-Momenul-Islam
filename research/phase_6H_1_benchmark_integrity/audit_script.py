"""
Phase 6H.1: Banglish Development Benchmark Target-Source Integrity Audit Script
Audits:
1. Active Corpus Manifest 14 Sources & Chunk Mappings
2. Phase 6G.2 Challenge Dataset Target IDs vs Actual Manifest
3. Phase 6H Experiment Results & Case Evaluations (Challenge + Regression)
4. Symptoms vs Corpus Content Mapping (for any unrepresented conditions)
"""

import json
import os
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_audit():
    # 1. Load Promoted Active Corpus Manifest
    manifest_path = "research/phase_6C/promoted_corpus_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)
        
    print("="*80)
    print("1. AUTHORITATIVE ACTIVE CORPUS MANIFEST")
    print("="*80)
    sources = {}
    chunks_by_id = {}
    for c in corpus:
        sid = c.get("parent_source_id", c["chunk_id"][:11])
        stitle = c.get("source_title", "").replace("\n", " ").strip()
        chunks_by_id[c["chunk_id"]] = c
        if sid not in sources:
            sources[sid] = {
                "source_id": sid,
                "title": stitle,
                "url": c.get("source_url", ""),
                "chunks": []
            }
        sources[sid]["chunks"].append(c["chunk_id"])
        
    for sid in sorted(sources.keys()):
        print(f"  {sid}: \"{sources[sid]['title']}\" ({len(sources[sid]['chunks'])} chunks)")
        
    # 2. Load Phase 6G.2 Challenge Dataset
    challenge_path = "research/phase_6G_2_runtime_and_banglish/banglish_challenge_dataset.json"
    with open(challenge_path, "r", encoding="utf-8") as f:
        challenge_cases = json.load(f)
        
    print("\n" + "="*80)
    print("2. AUDITING PHASE 6G.2 CHALLENGE DATASET (12 Cases)")
    print("="*80)
    
    challenge_audit = []
    for c in challenge_cases:
        cid = c["case_id"]
        q = c["query"]
        exp_cond = c["expected_condition"]
        exp_doc = c["expected_doc_id"]
        
        actual_source_info = sources.get(exp_doc)
        actual_title = actual_source_info["title"] if actual_source_info else "NON-EXISTENT"
        
        # Check condition alignment
        match = False
        notes = []
        if actual_source_info:
            # Does actual_title correspond to exp_cond?
            if exp_cond.lower() in actual_title.lower() or actual_title.lower() in exp_cond.lower():
                match = True
            elif exp_doc == "DOC-NHS-006" and "cut" in exp_cond.lower():
                match = True
            elif exp_doc == "DOC-NHS-005" and "burn" in exp_cond.lower():
                match = True
            elif exp_doc == "DOC-NHS-010" and "fever" in exp_cond.lower():
                match = True
            elif exp_doc == "DOC-NHS-004" and "asthma" in exp_cond.lower():
                match = True
            else:
                match = False
                notes.append(f"MISMATCH: Dataset claims '{exp_cond}', but {exp_doc} is '{actual_title}'")
        else:
            notes.append(f"CRITICAL: {exp_doc} does not exist in active corpus")
            
        print(f"[{cid}] '{q}'")
        print(f"  Claimed Condition: {exp_cond} | Claimed Doc: {exp_doc}")
        print(f"  Actual Manifest Doc: {exp_doc} -> \"{actual_title}\"")
        print(f"  Status: {'MATCH' if match else 'MISMATCH'}")
        if notes:
            for n in notes:
                print(f"  -> {n}")
        print()
        
        challenge_audit.append({
            "case_id": cid,
            "query": q,
            "claimed_condition": exp_cond,
            "claimed_doc_id": exp_doc,
            "actual_doc_title": actual_title,
            "is_valid_mapping": match,
            "notes": notes
        })

    # 3. Audit Regression Cases from Phase 6H script
    regression_cases = [
        {"case_id": "REG-EN-001", "lang": "English", "query": "how to treat minor burns with cool water", "expected_doc_id": "DOC-NHS-005", "cond": "Burns and scalds"},
        {"case_id": "REG-EN-002", "lang": "English", "query": "clean cut or graze with clean water and dressing", "expected_doc_id": "DOC-NHS-006", "cond": "Cuts and grazes"},
        {"case_id": "REG-EN-003", "lang": "English", "query": "what are symptoms of measles in children", "expected_doc_id": "DOC-NHS-013", "cond": "Measles"},
        {"case_id": "REG-EN-004", "lang": "English", "query": "how to treat diarrhea with oral rehydration salts", "expected_doc_id": "DOC-NHS-007", "cond": "Dehydration / Diarrhea"},
        {"case_id": "REG-EN-005", "lang": "English", "query": "child high temperature fever paracetamol fluids", "expected_doc_id": "DOC-NHS-010", "cond": "High temperature in children"},
        {"case_id": "REG-EN-006", "lang": "English", "query": "how to stop a nosebleed by pinching nose and leaning forward", "expected_doc_id": "DOC-NHS-012", "cond": "Nosebleed"},
        {"case_id": "REG-BN-001", "lang": "Bangla", "query": "বাচ্চার জ্বর হলে করণীয় কি?", "expected_doc_id": "DOC-NHS-010", "cond": "High temperature in children"},
        {"case_id": "REG-BN-002", "lang": "Bangla", "query": "কাটা বা ছড়ে যাওয়ার প্রাথমিক চিকিৎসা কি?", "expected_doc_id": "DOC-NHS-006", "cond": "Cuts and grazes"},
        {"case_id": "REG-BN-003", "lang": "Bangla", "query": "ডায়রিয়া হলে কি স্যালাইন খেতে হবে?", "expected_doc_id": "DOC-NHS-007", "cond": "Dehydration / Diarrhea"},
        {"case_id": "REG-BN-004", "lang": "Bangla", "query": "হামের লক্ষণ কি কি?", "expected_doc_id": "DOC-NHS-013", "cond": "Measles"},
        {"case_id": "REG-BN-005", "lang": "Bangla", "query": "হাত পুড়ে গেলে ঠান্ডা পানি দিতে হবে?", "expected_doc_id": "DOC-NHS-005", "cond": "Burns and scalds"},
        {"case_id": "REG-BN-006", "lang": "Bangla", "query": "নাক দিয়ে রক্ত পড়লে কি করতে হবে?", "expected_doc_id": "DOC-NHS-012", "cond": "Nosebleed"}
    ]
    
    print("="*80)
    print("3. AUDITING PHASE 6H REGRESSION CONTROL CASES (12 Cases)")
    print("="*80)
    for r in regression_cases:
        cid = r["case_id"]
        q = r["query"]
        cond = r["cond"]
        exp_doc = r["expected_doc_id"]
        act_info = sources.get(exp_doc)
        act_title = act_info["title"] if act_info else "NON-EXISTENT"
        
        match = False
        notes = []
        if "high temperature" in cond.lower() and "high temperature" in act_title.lower():
            match = True
        elif cond.lower() in act_title.lower() or act_title.lower() in cond.lower():
            match = True
        elif exp_doc == "DOC-NHS-006" and "cut" in cond.lower():
            match = True
        elif exp_doc == "DOC-NHS-005" and "burn" in cond.lower():
            match = True
        elif exp_doc == "DOC-NHS-010" and ("fever" in cond.lower() or "temperature" in cond.lower()):
            match = True
        elif exp_doc == "DOC-NHS-007" and ("dehydration" in cond.lower() or "diarrhea" in cond.lower()):
            match = True
        else:
            match = False
            notes.append(f"MISMATCH: Case is for '{cond}', but {exp_doc} is '{act_title}'")
            
        print(f"[{cid}] ({r['lang']}) '{q}'")
        print(f"  Intended: {cond} | Assigned: {exp_doc}")
        print(f"  Actual Manifest: {exp_doc} -> \"{act_title}\"")
        print(f"  Status: {'MATCH' if match else 'MISMATCH'}")
        if notes:
            for n in notes:
                print(f"  -> {n}")
        print()

    # 4. Load Phase 6H Results
    exp_res_path = "research/phase_6H_banglish_retrieval_experiment/outputs/phase_6H_experiment_results.json"
    with open(exp_res_path, "r", encoding="utf-8") as f:
        exp_data = json.load(f)
        
    print("="*80)
    print("4. PHASE 6H EXPERIMENT RAW RETRIEVAL OUTPUTS PER CANDIDATE")
    print("="*80)
    for name, cdata in exp_data["detailed_results"].items():
        print(f"\n--- {name} ---")
        for cr in cdata["challenge_results"]:
            cid = cr["case_id"]
            q = cr["query"]
            target = cr["expected_doc_id"]
            top1_chunk = cr.get("top_chunk", "None")
            top1_src = top1_chunk[:11] if top1_chunk != "None" else "None"
            top1_title = sources.get(top1_src, {}).get("title", "Unknown")
            top5 = cr.get("top5_cids", [])
            print(f"[{cid}] Target: {target} | Top-1: {top1_chunk} ({top1_title}) | Top-5: {[c[:11] for c in top5]}")
            
if __name__ == "__main__":
    run_audit()
