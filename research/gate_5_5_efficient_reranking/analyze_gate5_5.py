import json
import numpy as np

def calculate_metrics(results, model_key, k_vals=[1, 3, 5]):
    total = 0
    recalls = {k: 0 for k in k_vals}
    mrr = 0.0
    
    no_result_expected_total = 0
    retrievable_expected_total = 0
    
    for q in results["queries"]:
        total += 1
        expected = q['expected']
        top_docs = q['pipelines'][model_key]['top_docs']
        
        is_no_result = (expected == "NONE")
        if is_no_result:
            no_result_expected_total += 1
        else:
            retrievable_expected_total += 1
            if expected in top_docs:
                rank = top_docs.index(expected) + 1
                for k in k_vals:
                    if rank <= k:
                        recalls[k] += 1
                mrr += 1.0 / rank
                        
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

def get_candidate_recall(results, base_pipeline, k_val):
    recalls = 0
    retrievable_expected_total = 0
    for q in results["queries"]:
        expected = q['expected']
        if expected != "NONE":
            retrievable_expected_total += 1
            top_docs = q['pipelines'][base_pipeline]['top_docs'][:k_val]
            if expected in top_docs:
                recalls += 1
    return recalls / retrievable_expected_total if retrievable_expected_total else 0

def get_latencies(results, pipeline):
    lats = [q['pipelines'][pipeline]['latency_s'] for q in results["queries"]]
    return np.mean(lats), np.median(lats), np.percentile(lats, 95)

def get_reranker_latencies(results, lat_key):
    lats = [q['latencies'].get(lat_key, 0) for q in results["queries"]]
    return np.mean(lats), np.median(lats), np.percentile(lats, 95)

def main():
    try:
        with open('research/gate_5_5_efficient_reranking/gate_5_5_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
    except FileNotFoundError:
        print("gate_5_5_results.json not found yet.")
        return
        
    print("\n================ CANDIDATE RECALL ================")
    for base in ["e5_dense", "bgem3_dense"]:
        print(f"\n--- {base.upper()} ---")
        for k in [3, 5, 10]:
            cr = get_candidate_recall(results, base, k)
            print(f"Candidate Recall@{k}: {cr:.3f}")
            
    pipelines = [
        "e5_dense", "e5_reranked_k3", "e5_reranked_k5", "e5_reranked_k10",
        "bgem3_dense", "bgem3_reranked_k3", "bgem3_reranked_k5", "bgem3_reranked_k10"
    ]
    
    print("\n================ FINAL METRICS ================")
    for p in pipelines:
        m = calculate_metrics(results, p, [1, 3, 5])
        print(f"\n--- {p.upper()} ---")
        print(f"R@1: {m['Recall@1']:.3f} | R@3: {m['Recall@3']:.3f} | R@5: {m['Recall@5']:.3f} | MRR: {m['MRR']:.3f}")

    print("\n================ LATENCY (seconds) ================")
    print("\nTotal End-to-End Pipeline Latency:")
    for p in pipelines:
        mean, med, p95 = get_latencies(results, p)
        print(f"  {p}: mean={mean:.3f}, median={med:.3f}, p95={p95:.3f}")
        
    print("\nReranker ONLY Latency:")
    for k in [3, 5, 10]:
        mean, med, p95 = get_reranker_latencies(results, f"reranker_e5_k{k}_s")
        print(f"  E5_K{k}: mean={mean:.3f}, median={med:.3f}, p95={p95:.3f}")

    print("\n================ LANGUAGE / CATEGORY (R@1) ================")
    categories = set(q['category'] for q in results["queries"])
    for cat in sorted(list(categories)):
        print(f"\n--- Category: {cat} ---")
        cat_qs = {"queries": [q for q in results["queries"] if q['category'] == cat]}
        for p in ["e5_dense", "e5_reranked_k5", "bgem3_dense", "bgem3_reranked_k5"]:
            m = calculate_metrics(cat_qs, p, [1])
            print(f"  {p}: R@1={m['Recall@1']:.2f} ({m['raw_counts']['recall_1']}/{m['raw_counts']['retrievable_total']})")
            
    print("\n================ CONDITIONAL RERANKING SIMULATION ================")
    # Simulation: Rule -> If E5 top score > threshold, don't rerank, else rerank (E5 -> K=5)
    thresholds = [0.82, 0.85, 0.86, 0.88, 0.90]
    for th in thresholds:
        sim_recalls = 0
        sim_latencies = []
        retrievable = 0
        rerank_count = 0
        
        for q in results["queries"]:
            expected = q['expected']
            if expected != "NONE":
                retrievable += 1
                e5_score = q['pipelines']['e5_dense']['top_scores'][0]
                
                if e5_score > th:
                    # Skip reranker
                    top_doc = q['pipelines']['e5_dense']['top_docs'][0]
                    sim_latencies.append(q['pipelines']['e5_dense']['latency_s'])
                else:
                    # Rerank K=5
                    rerank_count += 1
                    top_doc = q['pipelines']['e5_reranked_k5']['top_docs'][0]
                    sim_latencies.append(q['pipelines']['e5_reranked_k5']['latency_s'])
                    
                if top_doc == expected:
                    sim_recalls += 1
                    
        r1 = sim_recalls / retrievable if retrievable else 0
        mean_lat = np.mean(sim_latencies)
        print(f"Threshold {th}: R@1={r1:.3f} | Reranked {rerank_count}/{retrievable} queries | Mean Latency: {mean_lat:.3f}s")
        
if __name__ == "__main__":
    main()
