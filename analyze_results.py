import json
import numpy as np

def calculate_metrics(results, model_key, threshold):
    total = 0
    recall_1 = 0
    recall_3 = 0
    mrr = 0.0
    false_retrieval = 0
    false_no_result = 0
    no_result_acc = 0
    
    no_result_expected_total = 0
    retrievable_expected_total = 0
    
    for q in results["queries"]:
        total += 1
        expected = q['expected']
        top_docs = q[model_key]['top_docs']
        top_scores = q[model_key]['top_scores']
        
        # Apply threshold
        retrieved_docs = [doc for doc, score in zip(top_docs, top_scores) if score >= threshold]
        
        is_no_result = (expected == "NONE")
        if is_no_result:
            no_result_expected_total += 1
            if len(retrieved_docs) > 0:
                false_retrieval += 1
            else:
                no_result_acc += 1
        else:
            retrievable_expected_total += 1
            if len(retrieved_docs) == 0:
                false_no_result += 1
            else:
                if expected in retrieved_docs:
                    recall_3 += 1
                    rank = retrieved_docs.index(expected) + 1
                    mrr += 1.0 / rank
                    if rank == 1:
                        recall_1 += 1
                        
    return {
        "Recall@1": recall_1 / retrievable_expected_total if retrievable_expected_total else 0,
        "Recall@3": recall_3 / retrievable_expected_total if retrievable_expected_total else 0,
        "MRR": mrr / retrievable_expected_total if retrievable_expected_total else 0,
        "FRR": false_retrieval / no_result_expected_total if no_result_expected_total else 0,
        "FNR": false_no_result / retrievable_expected_total if retrievable_expected_total else 0,
        "No Result Acc": no_result_acc / no_result_expected_total if no_result_expected_total else 0,
        "raw_counts": {
            "retrievable_total": retrievable_expected_total,
            "no_result_total": no_result_expected_total,
            "recall_1": recall_1,
            "recall_3": recall_3,
            "false_retrieval": false_retrieval,
            "false_no_result": false_no_result,
            "no_result_acc": no_result_acc
        }
    }

def print_distribution(scores, name):
    if not scores:
        print(f"  {name}: N/A")
        return
    print(f"  {name}: count={len(scores)}, min={np.min(scores):.3f}, max={np.max(scores):.3f}, mean={np.mean(scores):.3f}, median={np.median(scores):.3f}")

def main():
    try:
        with open('research/gate_5_3_real_retrieval/real_retrieval_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
    except FileNotFoundError:
        print("real_retrieval_results.json not found yet.")
        return
        
    print("\n================ METADATA ================")
    print(json.dumps(results["metadata"], indent=2))
        
    for model in ["bge", "e5"]:
        print(f"\n================ {model.upper()} SCORE DISTRIBUTIONS ================")
        relevant_top1 = []
        relevant_top3 = []
        irrelevant_top1 = [] # Out of corpus / hard negative (expected=NONE)
        hard_negative = []
        
        for q in results["queries"]:
            expected = q['expected']
            cat = q['category']
            top_scores = q[model]['top_scores']
            if len(top_scores) == 0: continue
            
            if expected == "NONE":
                irrelevant_top1.append(top_scores[0])
                if cat == "hard_negative":
                    hard_negative.append(top_scores[0])
            else:
                relevant_top1.append(top_scores[0])
                relevant_top3.extend(top_scores)
                
        print_distribution(relevant_top1, "Relevant Top-1 Scores")
        print_distribution(relevant_top3, "Relevant Top-3 Scores")
        print_distribution(irrelevant_top1, "Irrelevant (Expected=NONE) Top-1")
        print_distribution(hard_negative, "Hard Negative Top-1")
        
        print(f"\n================ {model.upper()} THRESHOLD CALIBRATION ================")
        for t in [0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85]:
            m = calculate_metrics(results, model, t)
            print(f"Threshold {t:.2f} | R@1: {m['Recall@1']:.3f} | R@3: {m['Recall@3']:.3f} | MRR: {m['MRR']:.3f} | FRR: {m['FRR']:.3f} | FNR: {m['FNR']:.3f}")
            
    print("\n================ LANGUAGE CATEGORY BREAKDOWN (Threshold=0.0) ================")
    categories = set(q['category'] for q in results["queries"])
    for cat in sorted(list(categories)):
        print(f"\n--- Category: {cat} ---")
        for model in ["bge", "e5"]:
            cat_qs = {"queries": [q for q in results["queries"] if q['category'] == cat]}
            m = calculate_metrics(cat_qs, model, 0.0)
            print(f"  {model.upper()}: R@1={m['Recall@1']:.2f} ({m['raw_counts']['recall_1']}/{m['raw_counts']['retrievable_total']})")
            
    print("\n================ TRANSLATION EVALUATION ================")
    t_status = {}
    for q in results["queries"]:
        if q['detected_language'] != "ENGLISH":
            # Print a few samples
            if len(t_status) < 20: 
                print(f"Orig: {q['query']}\nTran: {q['translated_text']}\nCat: {q['category']} | Lang: {q['detected_language']}\n---")
            
        s = q['translation_status']
        t_status[s] = t_status.get(s, 0) + 1
    print("\nTranslation Statuses:", t_status)

if __name__ == "__main__":
    main()
