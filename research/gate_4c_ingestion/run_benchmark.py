import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import time

def load_data():
    with open('benchmark.json', 'r', encoding='utf-8') as f:
        queries = json.load(f)
        
    chunks = []
    for doc_id in ['DOC-NHS-001', 'DOC-NHS-002', 'DOC-NHS-003']:
        with open(f'{doc_id}_chunks_B.json', 'r', encoding='utf-8') as f:
            doc_chunks = json.load(f)
            chunks.extend(doc_chunks)
            
    return queries, chunks

def evaluate(queries, chunks, model, preprocess_func=None):
    start = time.time()
    chunk_texts = [c['text'] for c in chunks]
    chunk_embeddings = model.encode(chunk_texts)
    
    results = []
    for q in queries:
        query_text = q['query']
        if preprocess_func:
            query_text = preprocess_func(query_text)
            
        q_emb = model.encode([query_text])[0]
        sims = cosine_similarity([q_emb], chunk_embeddings)[0]
        
        # Sort indices descending
        ranked_indices = np.argsort(sims)[::-1]
        
        # Get top 5 docs
        ranked_docs = []
        for idx in ranked_indices:
            doc = chunks[idx]['source_id']
            if doc not in ranked_docs:
                ranked_docs.append(doc)
                
        # Metrics
        top_1 = ranked_docs[0] if ranked_docs else None
        
        # Evaluate
        if q['expected_doc'] is None:
            # For "no_result", we just see if the highest score is below a threshold.
            # We'll just record the max sim.
            results.append({
                'query': q['query'],
                'category': q['category'],
                'expected': 'None',
                'predicted': top_1,
                'max_score': float(sims[ranked_indices[0]]),
                'correct': float(sims[ranked_indices[0]]) < 0.3 # Arbitrary threshold
            })
            continue
            
        try:
            rank = ranked_docs.index(q['expected_doc']) + 1
            mrr = 1.0 / rank
            recall_1 = 1 if rank == 1 else 0
        except ValueError:
            mrr = 0.0
            recall_1 = 0
            
        results.append({
            'query': q['query'],
            'category': q['category'],
            'expected': q['expected_doc'],
            'predicted': top_1,
            'max_score': float(sims[ranked_indices[0]]),
            'correct': recall_1 == 1,
            'mrr': mrr
        })
        
    latency = time.time() - start
    return results, latency

def mock_translate(text):
    translations = {
        'আমার বাচ্চার গলায় কিছু আটকে গেছে': 'something is stuck in my child throat',
        'matha betha jor koto mg paracetamol khabo': 'headache fever how many mg paracetamol should I take',
        'baccha choking what to do': 'child choking what to do'
    }
    return translations.get(text, text)

def main():
    queries, chunks = load_data()
    print(f"Loaded {len(queries)} queries and {len(chunks)} chunks.")
    
    print("Loading Multilingual Model...")
    multi_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    print("Loading English Model...")
    en_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("\n--- Approach A: Multilingual Embedding (Direct) ---")
    multi_results, multi_lat = evaluate(queries, chunks, multi_model)
    multi_acc = sum(r['correct'] for r in multi_results) / len(multi_results)
    multi_mrr = sum(r.get('mrr', 0) for r in multi_results if 'mrr' in r) / (len(multi_results)-1)
    print(f"Accuracy (Recall@1): {multi_acc:.2f}, MRR: {multi_mrr:.2f}, Latency: {multi_lat:.2f}s")
    for r in multi_results:
        print(f"  [{r['category']}] {r['query']} -> {'PASS' if r['correct'] else 'FAIL'} (Pred: {r['predicted']} Score: {r['max_score']:.2f})")
        
    print("\n--- Approach B: Translation + English Embedding ---")
    en_results, en_lat = evaluate(queries, chunks, en_model, preprocess_func=mock_translate)
    en_acc = sum(r['correct'] for r in en_results) / len(en_results)
    en_mrr = sum(r.get('mrr', 0) for r in en_results if 'mrr' in r) / (len(en_results)-1)
    print(f"Accuracy (Recall@1): {en_acc:.2f}, MRR: {en_mrr:.2f}, Latency: {en_lat:.2f}s")
    for r in en_results:
        print(f"  [{r['category']}] {r['query']} -> {'PASS' if r['correct'] else 'FAIL'} (Pred: {r['predicted']} Score: {r['max_score']:.2f})")

if __name__ == '__main__':
    main()
