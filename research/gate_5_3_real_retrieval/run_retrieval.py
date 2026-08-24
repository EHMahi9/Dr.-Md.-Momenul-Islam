import os, json, time, re
import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

def detect_language(text):
    bengali_chars = re.compile(r'[\u0980-\u09FF]')
    has_bengali = bool(bengali_chars.search(text))
    
    banglish_keywords = ['koto', 'khabo', 'ki', 'korbo', 'bacha', 'baccha', 'gese', 'atke', 'matha', 'betha', 'naki', 'rod', 'gorom', 'jor', 'asle']
    lower_text = text.lower()
    has_banglish = any(re.search(rf'\b{kw}\b', lower_text) for kw in banglish_keywords)
    
    if has_bengali:
        if re.search(r'[a-zA-Z]', text):
            return "MIXED"
        return "BANGLA_NATIVE_SCRIPT"
    else:
        if has_banglish:
            if any(w in lower_text.split() for w in ['what', 'how', 'is', 'the', 'for']):
                return "MIXED"
            return "BANGLISH_LATIN_SCRIPT"
        return "ENGLISH"

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Loading corpus...")
    corpus = []
    for f in ['DOC-NHS-001_chunks_A.json', 'DOC-NHS-002_chunks_A.json', 'DOC-NHS-003_chunks_A.json']:
        with open(os.path.join(base_dir, f), 'r', encoding='utf-8') as file:
            corpus.extend(json.load(file))
            
    print(f"Loaded {len(corpus)} chunks.")
    
    print("Loading benchmark...")
    with open(os.path.join(base_dir, 'benchmark_expanded_5_1.json'), 'r', encoding='utf-8') as file:
        benchmark = json.load(file)
        
    print(f"Loaded {len(benchmark)} queries.")
    
    print("Initializing translation model...")
    t0 = time.time()
    
    # We fallback to facebook/nllb-200-distilled-600M because ai4bharat/indictrans2 is gated.
    translator_id = "facebook/nllb-200-distilled-600M"
    tokenizer = AutoTokenizer.from_pretrained(translator_id)
    model_tr = AutoModelForSeq2SeqLM.from_pretrained(translator_id)
    model_tr.eval()
    t_load_time = time.time() - t0
    print(f"Loaded translation model in {t_load_time:.2f}s")
    
    def translate(text, lang):
        if lang == "ENGLISH":
            return text, "NOT_REQUIRED", 0.0
        
        start = time.time()
        try:
            # For NLLB we specify target language as English
            inputs = tokenizer(text, return_tensors="pt")
            outputs = model_tr.generate(**inputs, max_length=100, forced_bos_token_id=tokenizer.lang_code_to_id["eng_Latn"])
            translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
            latency = time.time() - start
            
            if len(translated.strip()) == 0:
                return text, "TRANSLATION_FAILED", latency
            
            # Simple heuristic for meaning drift (e.g. Banglish output exactly same as input or nonsensical)
            if translated.strip().lower() == text.strip().lower() and lang in ["BANGLISH_LATIN_SCRIPT", "BANGLA_NATIVE_SCRIPT"]:
                return translated, "TRANSLATION_MEANING_DRIFT", latency
                
            return translated, "TRANSLATION_ATTEMPTED", latency
        except Exception as e:
            print("Translation error:", e)
            return text, "TRANSLATION_FAILED", time.time() - start
            
    print("Initializing embedding models...")
    bge_id = "BAAI/bge-small-en-v1.5"
    e5_id = "intfloat/multilingual-e5-small"
    
    t0 = time.time()
    bge_model = SentenceTransformer(bge_id)
    bge_load_time = time.time() - t0
    print(f"Loaded BGE in {bge_load_time:.2f}s")
    
    t0 = time.time()
    e5_model = SentenceTransformer(e5_id)
    e5_load_time = time.time() - t0
    print(f"Loaded E5 in {e5_load_time:.2f}s")
    
    print("Embedding corpus...")
    corpus_texts = [c['text'] for c in corpus]
    
    bge_corpus_embs = bge_model.encode(corpus_texts, normalize_embeddings=True, convert_to_tensor=True)
    
    e5_corpus_texts = ["passage: " + t for t in corpus_texts]
    e5_corpus_embs = e5_model.encode(e5_corpus_texts, normalize_embeddings=True, convert_to_tensor=True)
    
    results = {
        "metadata": {
            "translator_load_time_s": t_load_time,
            "bge_load_time_s": bge_load_time,
            "e5_load_time_s": e5_load_time,
            "bge_model_id": bge_id,
            "e5_model_id": e5_id,
            "translator_model_id": translator_id,
            "device": str(bge_model.device)
        },
        "queries": []
    }
    
    for q in benchmark:
        query_text = q['query']
        expected = q['expected']
        
        t_pre = time.time()
        lang = detect_language(query_text)
        translated_text, tr_status, tr_latency = translate(query_text, lang)
        
        t0 = time.time()
        bge_q_emb = bge_model.encode([translated_text], normalize_embeddings=True, convert_to_tensor=True)
        bge_sims = util.cos_sim(bge_q_emb, bge_corpus_embs)[0].cpu().numpy()
        bge_latency = time.time() - t0
        
        bge_top_indices = np.argsort(bge_sims)[::-1]
        bge_top_docs = [corpus[i]['source_id'] for i in bge_top_indices[:3]]
        bge_top_scores = [float(bge_sims[i]) for i in bge_top_indices[:3]]
        
        t0 = time.time()
        e5_q_text = "query: " + query_text # E5 uses "query: " prefix
        e5_q_emb = e5_model.encode([e5_q_text], normalize_embeddings=True, convert_to_tensor=True)
        e5_sims = util.cos_sim(e5_q_emb, e5_corpus_embs)[0].cpu().numpy()
        e5_latency = time.time() - t0
        
        e5_top_indices = np.argsort(e5_sims)[::-1]
        e5_top_docs = [corpus[i]['source_id'] for i in e5_top_indices[:3]]
        e5_top_scores = [float(e5_sims[i]) for i in e5_top_indices[:3]]
        
        results["queries"].append({
            "query": query_text,
            "expected": expected,
            "category": q['cat'],
            "detected_language": lang,
            "translated_text": translated_text,
            "translation_status": tr_status,
            "translation_latency_s": tr_latency,
            "bge": {
                "top_docs": bge_top_docs,
                "top_scores": bge_top_scores,
                "latency_s": bge_latency
            },
            "e5": {
                "top_docs": e5_top_docs,
                "top_scores": e5_top_scores,
                "latency_s": e5_latency
            },
            "preprocessing_latency_s": time.time() - t_pre
        })
        
    with open(os.path.join(base_dir, 'real_retrieval_results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
        
    print("Finished evaluating benchmark.")

if __name__ == "__main__":
    main()
