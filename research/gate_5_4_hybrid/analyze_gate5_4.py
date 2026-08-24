import json
import numpy as np

def calculate_metrics(results, model_key, k_vals=[1, 3, 5]):
    total = 0
    recalls = {k: 0 for k in k_vals}
    mrr = 0.0
    false_retrieval = 0
    false_no_result = 0
    no_result_acc = 0
    
    no_result_expected_total = 0
    retrievable_expected_total = 0
    
    for q in results["queries"]:
        total += 1
        expected = q['expected']
        top_docs = q['pipelines'][model_key]['top_docs']
        
        is_no_result = (expected == "NONE")
        if is_no_result:
            no_result_expected_total += 1
            # Hard threshold for FRR/FNR counting:
            if len(top_docs) > 0 and q['pipelines'][model_key]['top_scores'][0] > 0.0:
                false_retrieval += 1
            else:
                no_result_acc += 1
        else:
            retrievable_expected_total += 1
            if len(top_docs) == 0:
                false_no_result += 1
            elif expected in top_docs:
                rank = top_docs.index(expected) + 1
                for k in k_vals:
                    if rank <= k:
                        recalls[k] += 1
                mrr += 1.0 / rank
            else:
                false_no_result += 1
                        
    out = {
        f"Recall@{k}": recalls[k] / retrievable_expected_total if retrievable_expected_total else 0 for k in k_vals
    }
    out["MRR"] = mrr / retrievable_expected_total if retrievable_expected_total else 0
    out["raw_counts"] = {
        "retrievable_total": retrievable_expected_total,
        "no_result_total": no_result_expected_total,
    }
    for k in k_vals:
        out["raw_counts"][f"recall_{k}"] = recalls[k]
    
    return out

def print_distribution(scores, name):
    if not scores:
        print(f"  {name}: N/A")
        return
    print(f"  {name}: count={len(scores)}, min={np.min(scores):.3f}, max={np.max(scores):.3f}, mean={np.mean(scores):.3f}, median={np.median(scores):.3f}")

def find_failures(results, baseline_pipeline="hybrid_bgem3_bm25", final_pipeline="hybrid_reranked"):
    failures = []
    for q in results["queries"]:
        expected = q['expected']
        
        b_docs = q['pipelines'][baseline_pipeline]['top_docs']
        b_scores = q['pipelines'][baseline_pipeline]['top_scores']
        
        f_docs = q['pipelines'][final_pipeline]['top_docs']
        f_scores = q['pipelines'][final_pipeline]['top_scores']
        
        if expected != "NONE":
            if expected not in f_docs[:1]:
                failures.append({
                    "query": q['query'],
                    "cat": q['category'],
                    "lang": q['detected_language'],
                    "type": "WRONG_TOP_RESULT / FALSE_NO_RELEVANT_SOURCE",
                    "expected": expected,
                    "baseline_top": b_docs[0] if b_docs else "None",
                    "baseline_score": b_scores[0] if b_scores else 0,
                    "final_top": f_docs[0] if f_docs else "None",
                    "final_score": f_scores[0] if f_scores else 0
                })
        else:
            if len(f_docs) > 0 and f_scores[0] > 0.0: 
                failures.append({
                    "query": q['query'],
                    "cat": q['category'],
                    "lang": q['detected_language'],
                    "type": "HARD_NEGATIVE_SURVIVAL / FALSE_RETRIEVAL",
                    "expected": expected,
                    "baseline_top": b_docs[0] if b_docs else "None",
                    "baseline_score": b_scores[0] if b_scores else 0,
                    "final_top": f_docs[0] if f_docs else "None",
                    "final_score": f_scores[0] if f_scores else 0
                })
    return failures

def main():
    try:
        with open('research/gate_5_4_hybrid/gate_5_4_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
    except FileNotFoundError:
        print("gate_5_4_results.json not found yet.")
        return
        
    pipelines = ["e5_dense", "bgem3_dense", "hybrid_bgem3_bm25", "hybrid_reranked"]
    
    print("\n================ PIPELINE METRICS ================")
    for p in pipelines:
        m = calculate_metrics(results, p)
        print(f"\n--- {p.upper()} ---")
        print(f"R@1: {m['Recall@1']:.3f} | R@3: {m['Recall@3']:.3f} | R@5: {m['Recall@5']:.3f} | MRR: {m['MRR']:.3f}")
        
    print("\n================ SCORE DISTRIBUTIONS & SEPARATION ================")
    for p in pipelines:
        print(f"\n--- {p.upper()} Scores ---")
        relevant_top1 = []
        irrelevant_top1 = []
        hard_negative = []
        
        for q in results["queries"]:
            expected = q['expected']
            cat = q['category']
            top_scores = q['pipelines'][p]['top_scores']
            if len(top_scores) == 0: continue
            
            if expected == "NONE":
                irrelevant_top1.append(top_scores[0])
                if cat == "hard_negative":
                    hard_negative.append(top_scores[0])
            else:
                relevant_top1.append(top_scores[0])
                
        print_distribution(relevant_top1, "Relevant Top-1 Scores")
        print_distribution(irrelevant_top1, "Irrelevant/Out-of-corpus Top-1")
        print_distribution(hard_negative, "Hard Negative Top-1")
        
    print("\n================ CATEGORY BREAKDOWN (R@1) ================")
    categories = set(q['category'] for q in results["queries"])
    for cat in sorted(list(categories)):
        print(f"\n--- Category: {cat} ---")
        cat_qs = {"queries": [q for q in results["queries"] if q['category'] == cat]}
        for p in pipelines:
            m = calculate_metrics(cat_qs, p, [1])
            print(f"  {p}: R@1={m['Recall@1']:.2f} ({m['raw_counts']['recall_1']}/{m['raw_counts']['retrievable_total']})")
            
    print("\n================ LATENCY (seconds) ================")
    for lat_type in ["bm25_only_s", "hybrid_merge_s", "reranker_only_s"]:
        lats = [q['latencies'].get(lat_type, 0) for q in results["queries"]]
        if lats and max(lats) > 0:
            print(f"  {lat_type}: mean={np.mean(lats):.3f}, median={np.median(lats):.3f}, p95={np.percentile(lats, 95):.3f}")
            
    print("\nTotal Pipeline Latencies:")
    for p in pipelines:
        lats = [q['pipelines'][p]['latency_s'] for q in results["queries"]]
        print(f"  {p}: mean={np.mean(lats):.3f}, median={np.median(lats):.3f}, p95={np.percentile(lats, 95):.3f}")

    print("\n================ FAILURE ANALYSIS (Hybrid -> Reranked) ================")
    failures = find_failures(results)
    for f in failures[:15]:  # Print first 15 for analysis
        print(f"\nQuery: {f['query']}")
        print(f"Type: {f['type']} | Lang: {f['lang']} | Cat: {f['cat']}")
        print(f"Expected: {f['expected']}")
        print(f"Baseline (Hybrid) Top: {f['baseline_top']} (Score: {f['baseline_score']:.3f})")
        print(f"Final (Reranked) Top: {f['final_top']} (Score: {f['final_score']:.3f})")

if __name__ == "__main__":
    main()
