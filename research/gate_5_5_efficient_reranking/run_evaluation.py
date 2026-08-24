import os, json, time, gc
import torch
import numpy as np

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, '..', 'gate_5_3_real_retrieval')
    
    print("Loading corpus...")
    corpus = []
    for f in ['DOC-NHS-001_chunks_A.json', 'DOC-NHS-002_chunks_A.json', 'DOC-NHS-003_chunks_A.json']:
        with open(os.path.join(input_dir, f), 'r', encoding='utf-8') as file:
            corpus.extend(json.load(file))
            
    print("Loading benchmark...")
    with open(os.path.join(input_dir, 'benchmark_expanded_5_1.json'), 'r', encoding='utf-8') as file:
        benchmark = json.load(file)
        
    corpus_texts = [c['text'] for c in corpus]
    corpus_ids = [c['source_id'] for c in corpus]
    
    results = {
        "metadata": {
            "e5_id": "intfloat/multilingual-e5-small",
            "bgem3_id": "BAAI/bge-m3",
            "reranker_id": "BAAI/bge-reranker-v2-m3",
        },
        "queries": []
    }
    
    for q in benchmark:
        results["queries"].append({
            "query": q['query'],
            "expected": q['expected'],
            "category": q['cat'],
            "detected_language": q.get('lang', 'UNKNOWN'),
            "pipelines": {},
            "latencies": {}
        })

    # ================= E5 =================
    print("--- Phase 1: E5 Dense ---")
    from sentence_transformers import SentenceTransformer, util
    t0 = time.time()
    e5_model = SentenceTransformer(results["metadata"]["e5_id"])
    
    e5_corpus_texts = ["passage: " + t for t in corpus_texts]
    e5_corpus_embs = e5_model.encode(e5_corpus_texts, normalize_embeddings=True, convert_to_tensor=True)
    
    for i, q in enumerate(benchmark):
        query_text = q['query']
        t0 = time.time()
        e5_q_text = "query: " + query_text
        e5_q_emb = e5_model.encode([e5_q_text], normalize_embeddings=True, convert_to_tensor=True)
        e5_sims = util.cos_sim(e5_q_emb, e5_corpus_embs)[0].cpu().numpy()
        e5_top_indices = np.argsort(e5_sims)[::-1][:10]
        
        results["queries"][i]["pipelines"]["e5_dense"] = {
            "top_docs": [corpus_ids[idx] for idx in e5_top_indices],
            "top_scores": [float(e5_sims[idx]) for idx in e5_top_indices],
            "latency_s": time.time() - t0
        }
    del e5_model
    del e5_corpus_embs
    gc.collect()
    
    # ================= BGE-M3 =================
    print("--- Phase 2: BGE-M3 Dense ---")
    bgem3_model = SentenceTransformer(results["metadata"]["bgem3_id"])
    
    bgem3_corpus_embs = bgem3_model.encode(corpus_texts, normalize_embeddings=True, convert_to_tensor=True)
    
    for i, q in enumerate(benchmark):
        query_text = q['query']
        t0 = time.time()
        bgem3_q_emb = bgem3_model.encode([query_text], normalize_embeddings=True, convert_to_tensor=True)
        bgem3_sims = util.cos_sim(bgem3_q_emb, bgem3_corpus_embs)[0].cpu().numpy()
        bgem3_top_indices = np.argsort(bgem3_sims)[::-1][:10]
        
        results["queries"][i]["pipelines"]["bgem3_dense"] = {
            "top_docs": [corpus_ids[idx] for idx in bgem3_top_indices],
            "top_scores": [float(bgem3_sims[idx]) for idx in bgem3_top_indices],
            "latency_s": time.time() - t0
        }
    del bgem3_model
    del bgem3_corpus_embs
    gc.collect()

    # ================= RERANKER =================
    print("--- Phase 3: Reranker ---")
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    reranker_tokenizer = AutoTokenizer.from_pretrained(results["metadata"]["reranker_id"])
    reranker_model = AutoModelForSequenceClassification.from_pretrained(results["metadata"]["reranker_id"])
    reranker_model.eval()
    
    k_vals = [3, 5, 10]
    
    for i, q in enumerate(benchmark):
        query_text = q['query']
        
        # Helper to rerank a specific set of top-k docs
        def rerank_docs(base_pipeline, k):
            base_top_docs = results["queries"][i]["pipelines"][base_pipeline]["top_docs"][:k]
            base_top_texts = [corpus_texts[corpus_ids.index(d)] for d in base_top_docs]
            
            t0 = time.time()
            rerank_inputs = [[query_text, doc] for doc in base_top_texts]
            if len(rerank_inputs) > 0:
                inputs = reranker_tokenizer(rerank_inputs, padding=True, truncation=True, return_tensors='pt', max_length=512)
                with torch.no_grad():
                    scores = reranker_model(**inputs, return_dict=True).logits.view(-1,).float().cpu().numpy()
                reranked_indices = np.argsort(scores)[::-1]
                top_docs = [base_top_docs[idx] for idx in reranked_indices]
                top_scores = [float(scores[idx]) for idx in reranked_indices]
            else:
                top_docs = []
                top_scores = []
            lat = time.time() - t0
            return top_docs, top_scores, lat
            
        for k in k_vals:
            # E5 -> Reranker
            docs, scores, lat = rerank_docs("e5_dense", k)
            results["queries"][i]["pipelines"][f"e5_reranked_k{k}"] = {
                "top_docs": docs,
                "top_scores": scores,
                "latency_s": results["queries"][i]["pipelines"]["e5_dense"]["latency_s"] + lat
            }
            results["queries"][i]["latencies"][f"reranker_e5_k{k}_s"] = lat
            
            # BGE-M3 -> Reranker
            docs, scores, lat = rerank_docs("bgem3_dense", k)
            results["queries"][i]["pipelines"][f"bgem3_reranked_k{k}"] = {
                "top_docs": docs,
                "top_scores": scores,
                "latency_s": results["queries"][i]["pipelines"]["bgem3_dense"]["latency_s"] + lat
            }
            results["queries"][i]["latencies"][f"reranker_bgem3_k{k}_s"] = lat
            
        if (i + 1) % 10 == 0:
            print(f"Processed {i+1}/103 queries...")

    # ================= SAVE =================
    print("Saving results...")
    with open(os.path.join(base_dir, 'gate_5_5_results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
        
    print("Evaluation complete.")

if __name__ == "__main__":
    main()
