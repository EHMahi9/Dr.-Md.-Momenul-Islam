import os
import json
import numpy as np
import random
from collections import defaultdict

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, '..', 'gate_5_5_efficient_reranking', 'gate_5_5_results.json')
    
    with open(input_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
        
    benchmark = results["queries"]
    
    print("================ PHASE 2: BENCHMARK INTEGRITY ================")
    # Group by Expected Chunk
    expected_groups = defaultdict(list)
    for i, q in enumerate(benchmark):
        expected_groups[q['expected']].append(i)
        
    print(f"Total Queries: {len(benchmark)}")
    print(f"Total Unique Expected Chunks (excluding NONE): {len(expected_groups) - (1 if 'NONE' in expected_groups else 0)}")
    
    # Check for near-duplicates
    print("Inspecting for semantic duplication...")
    for exp, indices in expected_groups.items():
        if exp == "NONE": continue
        if len(indices) > 5:
            print(f"  Chunk {exp} has {len(indices)} queries associated with it. High risk of semantic leakage if split randomly.")
            
    # Define splits (Test indices)
    splits = {}
    
    # Random A (seed 42)
    random.seed(42)
    idx = list(range(len(benchmark)))
    random.shuffle(idx)
    splits['Random A (Seed 42)'] = idx[:len(idx)//2]
    
    # Random B (seed 123)
    random.seed(123)
    idx = list(range(len(benchmark)))
    random.shuffle(idx)
    splits['Random B (Seed 123)'] = idx[:len(idx)//2]
    
    # Random C (seed 999)
    random.seed(999)
    idx = list(range(len(benchmark)))
    random.shuffle(idx)
    splits['Random C (Seed 999)'] = idx[:len(idx)//2]
    
    # Intent-Grouped (Group by Expected chunk, so no leakage)
    random.seed(42)
    chunks = list(expected_groups.keys())
    random.shuffle(chunks)
    test_chunks = chunks[:len(chunks)//2]
    intent_test = []
    for c in test_chunks:
        intent_test.extend(expected_groups[c])
    splits['Intent-Grouped'] = intent_test
    
    # Language-Aware (Stratified by language category)
    random.seed(42)
    lang_groups = defaultdict(list)
    for i, q in enumerate(benchmark):
        lang_groups[q['category']].append(i)
    
    lang_test = []
    for cat, indices in lang_groups.items():
        random.shuffle(indices)
        lang_test.extend(indices[:len(indices)//2])
    splits['Language-Aware Stratified'] = lang_test
    
    print("\n================ PHASE 3 & 4: MULTI-SPLIT EVALUATION ================")
    candidates = ['e5_dense', 'e5_reranked_k3', 'e5_reranked_k5', 'e5_reranked_k10']
    
    candidate_scores = {c: [] for c in candidates}
    
    def evaluate(split_indices, candidate):
        recalls = 0
        retrievable = 0
        for i in split_indices:
            q = benchmark[i]
            exp = q['expected']
            if exp != "NONE":
                retrievable += 1
                if q['pipelines'][candidate]['top_docs'] and q['pipelines'][candidate]['top_docs'][0] == exp:
                    recalls += 1
        return recalls / retrievable if retrievable else 0

    print(f"{'Split Name':<30} | " + " | ".join([f"{c:^15}" for c in candidates]))
    print("-" * 100)
    
    for split_name, indices in splits.items():
        row = f"{split_name:<30} | "
        for c in candidates:
            r1 = evaluate(indices, c)
            candidate_scores[c].append(r1)
            row += f"{r1:^15.3f} | "
        print(row)
        
    print("-" * 100)
    print(f"{'MEAN':<30} | " + " | ".join([f"{np.mean(candidate_scores[c]):^15.3f}" for c in candidates]))
    print(f"{'MIN':<30} | " + " | ".join([f"{np.min(candidate_scores[c]):^15.3f}" for c in candidates]))
    print(f"{'MAX':<30} | " + " | ".join([f"{np.max(candidate_scores[c]):^15.3f}" for c in candidates]))
    print(f"{'RANGE (Max-Min)':<30} | " + " | ".join([f"{(np.max(candidate_scores[c]) - np.min(candidate_scores[c])):^15.3f}" for c in candidates]))

    print("\n================ PHASE 5: FAILURE BOUNDARY (Abbreviated Banglish) ================")
    for q in benchmark:
        if q['category'] == 'abbr_banglish' and q['expected'] != "NONE":
            print(f"Query: {q['query']} | Exp: {q['expected']}")
            print(f"E5 Top-3: {q['pipelines']['e5_dense']['top_docs'][:3]} (Scores: {[round(s,3) for s in q['pipelines']['e5_dense']['top_scores'][:3]]})")
            print(f"Reranker K=5 Top-3: {q['pipelines']['e5_reranked_k5']['top_docs'][:3]} (Scores: {[round(s,3) for s in q['pipelines']['e5_reranked_k5']['top_scores'][:3]]})")
            e5_rank = q['pipelines']['e5_dense']['top_docs'].index(q['expected']) + 1 if q['expected'] in q['pipelines']['e5_dense']['top_docs'] else -1
            rr_rank = q['pipelines']['e5_reranked_k5']['top_docs'].index(q['expected']) + 1 if q['expected'] in q['pipelines']['e5_reranked_k5']['top_docs'] else -1
            print(f"E5 Rank: {e5_rank} -> RR Rank: {rr_rank}")
            if e5_rank == 1 and rr_rank > 1:
                print("FAILURE TYPE: Reranker degraded correct candidate (Semantic misalignment).")
            elif e5_rank > 1 and rr_rank == 1:
                print("SUCCESS: Reranker improved candidate.")
            print("-" * 50)
            
    print("\n================ PHASE 6: NO-RELEVANT-SOURCE BOUNDARY ================")
    # Can we separate NO_RELEVANT_SOURCE from SUPPORTED?
    # We will test dense scores, reranker K=5 scores, and dense margin.
    hn_dense = []
    hn_rr = []
    hn_margin = []
    
    valid_dense = []
    valid_rr = []
    valid_margin = []
    
    for q in benchmark:
        d_scores = q['pipelines']['e5_dense']['top_scores']
        rr_scores = q['pipelines']['e5_reranked_k5']['top_scores']
        
        margin = (d_scores[0] - d_scores[1]) if len(d_scores) > 1 else 0
        ds = d_scores[0] if len(d_scores) > 0 else 0
        rs = rr_scores[0] if len(rr_scores) > 0 else 0
        
        if q['expected'] == 'NONE':
            hn_dense.append(ds)
            hn_rr.append(rs)
            hn_margin.append(margin)
        else:
            valid_dense.append(ds)
            valid_rr.append(rs)
            valid_margin.append(margin)
            
    print(f"Valid Dense Score: Mean={np.mean(valid_dense):.3f} (Min={np.min(valid_dense):.3f}, Max={np.max(valid_dense):.3f})")
    print(f"HN Dense Score:    Mean={np.mean(hn_dense):.3f} (Min={np.min(hn_dense):.3f}, Max={np.max(hn_dense):.3f})")
    
    print(f"Valid Reranker Score: Mean={np.mean(valid_rr):.3f} (Min={np.min(valid_rr):.3f}, Max={np.max(valid_rr):.3f})")
    print(f"HN Reranker Score:    Mean={np.mean(hn_rr):.3f} (Min={np.min(hn_rr):.3f}, Max={np.max(hn_rr):.3f})")
    
    print(f"Valid Dense Margin: Mean={np.mean(valid_margin):.3f}")
    print(f"HN Dense Margin:    Mean={np.mean(hn_margin):.3f}")
    
    overlap_dense = (np.min(valid_dense) <= np.max(hn_dense))
    overlap_rr = (np.min(valid_rr) <= np.max(hn_rr))
    print(f"Overlap in Dense Scores? {overlap_dense}")
    print(f"Overlap in Reranker Scores? {overlap_rr}")
    
    if overlap_dense and overlap_rr:
        print("\nCONCLUSION: RETRIEVAL_CONFIDENCE_NOT_SUFFICIENT_FOR_SAFE_NO_RESULT_DECISION")

if __name__ == "__main__":
    main()
