import os, json, time, re
import torch
import numpy as np
import gc

def reciprocal_rank_fusion(dense_ranks, sparse_ranks, k=60):
    rrf_scores = {}
    for rank, doc_id in enumerate(dense_ranks):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    for rank, doc_id in enumerate(sparse_ranks):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

def simple_tokenize(text):
    return re.findall(r'\w+', text.lower())

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, '..', 'gate_5_3_real_retrieval')
    
    print("Loading corpus...")
    corpus = []
    for f in ['DOC-NHS-001_chunks_A.json', 'DOC-NHS-002_chunks_A.json', 'DOC-NHS-003_chunks_A.json']:
        with open(os.path.join(input_dir, f), 'r', encoding='utf-8') as file:
            corpus.extend(json.load(file))
            
    print(f"Loaded {len(corpus)} chunks.")
    
    print("Loading benchmark...")
    with open(os.path.join(input_dir, 'benchmark_expanded_5_1.json'), 'r', encoding='utf-8') as file:
        benchmark = json.load(file)
        
    print(f"Loaded {len(benchmark)} queries.")
    
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
    
    # Pre-populate structure
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
    results["metadata"]["e5_load_time_s"] = time.time() - t0
    
    e5_corpus_texts = ["passage: " + t for t in corpus_texts]
    e5_corpus_embs = e5_model.encode(e5_corpus_texts, normalize_embeddings=True, convert_to_tensor=True)
    
    for i, q in enumerate(benchmark):
        query_text = q['query']
        t0 = time.time()
        e5_q_text = "query: " + query_text
        e5_q_emb = e5_model.encode([e5_q_text], normalize_embeddings=True, convert_to_tensor=True)
        e5_sims = util.cos_sim(e5_q_emb, e5_corpus_embs)[0].cpu().numpy()
        e5_top_indices = np.argsort(e5_sims)[::-1]
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
    t0 = time.time()
    bgem3_model = SentenceTransformer(results["metadata"]["bgem3_id"])
    results["metadata"]["bgem3_load_time_s"] = time.time() - t0
    
    bgem3_corpus_embs = bgem3_model.encode(corpus_texts, normalize_embeddings=True, convert_to_tensor=True)
    
    for i, q in enumerate(benchmark):
        query_text = q['query']
        t0 = time.time()
        bgem3_q_emb = bgem3_model.encode([query_text], normalize_embeddings=True, convert_to_tensor=True)
        bgem3_sims = util.cos_sim(bgem3_q_emb, bgem3_corpus_embs)[0].cpu().numpy()
        bgem3_top_indices = np.argsort(bgem3_sims)[::-1]
        results["queries"][i]["pipelines"]["bgem3_dense"] = {
            "top_docs": [corpus_ids[idx] for idx in bgem3_top_indices],
            "top_scores": [float(bgem3_sims[idx]) for idx in bgem3_top_indices],
            "latency_s": time.time() - t0
        }
    del bgem3_model
    del bgem3_corpus_embs
    gc.collect()

    # ================= BM25 & HYBRID =================
    print("--- Phase 3: BM25 & Hybrid ---")
    from rank_bm25 import BM25Okapi
    tokenized_corpus = [simple_tokenize(t) for t in corpus_texts]
    bm25 = BM25Okapi(tokenized_corpus)
    
    for i, q in enumerate(benchmark):
        query_text = q['query']
        
        t0 = time.time()
        tokenized_q = simple_tokenize(query_text)
        bm25_scores = bm25.get_scores(tokenized_q)
        bm25_top_indices = np.argsort(bm25_scores)[::-1]
        bm25_top_docs = [corpus_ids[idx] for idx in bm25_top_indices]
        lat_bm25 = time.time() - t0
        
        bgem3_top_docs = results["queries"][i]["pipelines"]["bgem3_dense"]["top_docs"]
        
        t0 = time.time()
        hybrid_ranked = reciprocal_rank_fusion(bgem3_top_docs, bm25_top_docs)
        hybrid_top_docs = [doc_id for doc_id, score in hybrid_ranked]
        hybrid_top_scores = [score for doc_id, score in hybrid_ranked]
        lat_hybrid_merge = time.time() - t0
        
        results["queries"][i]["pipelines"]["hybrid_bgem3_bm25"] = {
            "top_docs": hybrid_top_docs,
            "top_scores": hybrid_top_scores,
            "latency_s": results["queries"][i]["pipelines"]["bgem3_dense"]["latency_s"] + lat_bm25 + lat_hybrid_merge
        }
        results["queries"][i]["latencies"]["bm25_only_s"] = lat_bm25
        results["queries"][i]["latencies"]["hybrid_merge_s"] = lat_hybrid_merge

    # ================= RERANKER =================
    print("--- Phase 4: Reranker ---")
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    t0 = time.time()
    reranker_tokenizer = AutoTokenizer.from_pretrained(results["metadata"]["reranker_id"])
    reranker_model = AutoModelForSequenceClassification.from_pretrained(results["metadata"]["reranker_id"])
    reranker_model.eval()
    results["metadata"]["reranker_load_time_s"] = time.time() - t0
    
    for i, q in enumerate(benchmark):
        query_text = q['query']
        
        t0 = time.time()
        hybrid_top_docs = results["queries"][i]["pipelines"]["hybrid_bgem3_bm25"]["top_docs"]
        top10_hybrid_docs = hybrid_top_docs[:10]
        top10_hybrid_texts = [corpus_texts[corpus_ids.index(doc_id)] for doc_id in top10_hybrid_docs]
        
        rerank_inputs = [[query_text, doc] for doc in top10_hybrid_texts]
        
        if len(rerank_inputs) > 0:
            inputs = reranker_tokenizer(rerank_inputs, padding=True, truncation=True, return_tensors='pt', max_length=512)
            with torch.no_grad():
                scores = reranker_model(**inputs, return_dict=True).logits.view(-1,).float().cpu().numpy()
            
            reranked_indices = np.argsort(scores)[::-1]
            rerank_top_docs = [top10_hybrid_docs[idx] for idx in reranked_indices]
            rerank_top_scores = [float(scores[idx]) for idx in reranked_indices]
        else:
            rerank_top_docs = []
            rerank_top_scores = []
            
        lat_rerank = time.time() - t0
        
        results["queries"][i]["latencies"]["reranker_only_s"] = lat_rerank
        results["queries"][i]["pipelines"]["hybrid_reranked"] = {
            "top_docs": rerank_top_docs,
            "top_scores": rerank_top_scores,
            "latency_s": results["queries"][i]["pipelines"]["hybrid_bgem3_bm25"]["latency_s"] + lat_rerank
        }
        
    # ================= SAVE =================
    print("Saving results...")
    with open(os.path.join(base_dir, 'gate_5_4_results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
        
    print("Evaluation complete.")

if __name__ == "__main__":
    main()
