import os
import json
import time
import re
import numpy as np
from datetime import datetime, timezone

# ---------------------------------------------------------
# MODULE: Corpus Loader
# ---------------------------------------------------------
class CorpusLoader:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.chunks = []
        
    def load_corpus(self):
        # Only load the 3 approved documents (Strategy B chunks)
        docs = ['DOC-NHS-001', 'DOC-NHS-002', 'DOC-NHS-003']
        for doc_id in docs:
            path = os.path.join(self.data_dir, f"{doc_id}_chunks_A.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    doc_chunks = json.load(f)
                    self.chunks.extend(doc_chunks)
            else:
                print(f"Warning: {path} not found.")
        return self.chunks

# ---------------------------------------------------------
# MODULE: Query Processing
# ---------------------------------------------------------
class QueryProcessor:
    def __init__(self):
        pass

    def detect_language(self, text):
        if re.search(r'[\u0980-\u09FF]', text):
            return "bn"
        words = text.lower().split()
        banglish_indicators = {'koto', 'khabo', 'ki', 'hocche', 'ache', 'kisu', 'atke', 'gese', 'betha', 'matha', 'jor'}
        if any(w in banglish_indicators for w in words):
            return "banglish/mixed"
        return "en"

    def normalize(self, text):
        text = text.replace('\u200b', '').strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def process(self, original_query):
        normalized = self.normalize(original_query)
        lang = self.detect_language(normalized)
        return {
            "original_query": original_query,
            "detected_language_or_script": lang,
            "normalized_query": normalized,
            "translation_required": lang != "en",
            "translated_query": None,
            "translation_status": "PENDING",
            "translation_error": None,
            "translation_latency_ms": 0
        }

# ---------------------------------------------------------
# MODULE: Translation Adapter
# ---------------------------------------------------------
class TranslationAdapter:
    def __init__(self):
        self.provider = "Simulated Translation Service (Gate 5 Prototype)"
        self.mock_dict = {
            'প্যারাসিটামল খাওয়ার নিয়ম কি?': 'What are the rules for taking paracetamol?',
            'হিট স্ট্রোক হলে কি করব?': 'What should I do for a heat stroke?',
            'আমার বাচ্চার গলায় কিছু আটকে গেছে এবং সে নিশ্বাস নিতে পারছে না': 'Something is stuck in my child throat and cannot breathe',
            'জ্বরের জন্য কি খাব?': 'What should I eat for fever?',
            'paracetamol koto mg khabo din e': 'how many mg of paracetamol should I take a day',
            'bachar golay kisu atke gese': 'something is stuck in child throat',
            'matha ghurtese ar betha roder moddhe': 'feeling dizzy and headache in the sun',
            'pera koto mg': 'how many mg of para',
            'mtha ghurse rod e': 'head spinning in sun',
            'আমার বাচ্চার choking হচ্ছে': 'my child is choking',
            'adult দের জন্য paracetamol dose': 'paracetamol dose for adults',
            'child choking hocche ki korbo': 'child is choking what to do',
            'heatstroke er symptoms ki': 'what are symptoms of heatstroke',
            'dim parbi naki': 'will you lay an egg',
            'matha betha bori': 'headache pill'
        }

    def translate(self, query_obj):
        start = time.time()
        time.sleep(0.01)
        if not query_obj["translation_required"]:
            query_obj["translated_query"] = query_obj["normalized_query"]
            query_obj["translation_status"] = "NOT_REQUIRED"
        else:
            q = query_obj["normalized_query"]
            if q in self.mock_dict:
                query_obj["translated_query"] = self.mock_dict[q]
                query_obj["translation_status"] = "SUCCESS"
                if "pera" in q.lower():
                    query_obj["translation_status"] = "TRANSLATION_SUSPECTED_MEANING_DRIFT"
            else:
                query_obj["translated_query"] = q 
                query_obj["translation_status"] = "TRANSLATION_FAILED"
                query_obj["translation_error"] = "Unmapped mock translation"
        query_obj["translation_latency_ms"] = (time.time() - start) * 1000
        return query_obj

# ---------------------------------------------------------
# MODULE: Embedding Module
# ---------------------------------------------------------
class EmbeddingModule:
    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self.use_mock = True
        self.dim = "Mock Keywords"

    def encode(self, texts):
        # Very simple pure-python keyword overlap mock for pipeline validation
        # Returns list of sets of lowercase words
        return [set(re.findall(r'\w+', t.lower())) for t in texts]

# ---------------------------------------------------------
# MODULE: Retrieval Module
# ---------------------------------------------------------
class RetrievalModule:
    def __init__(self, chunks, embedding_module):
        self.chunks = chunks
        self.embedding_module = embedding_module
        
        start = time.time()
        self.chunk_texts = [c['text'] for c in self.chunks]
        self.chunk_embeddings = self.embedding_module.encode(self.chunk_texts)
        self.index_latency_ms = (time.time() - start) * 1000
        
    def search(self, query_obj, top_k=3, threshold=0.1):
        start = time.time()
        
        search_text = query_obj["translated_query"] if query_obj["translated_query"] else query_obj["normalized_query"]
        q_emb = self.embedding_module.encode([search_text])[0]
        
        sims = []
        for doc_emb in self.chunk_embeddings:
            if len(q_emb) == 0 or len(doc_emb) == 0:
                sims.append(0.0)
            else:
                overlap = len(q_emb.intersection(doc_emb))
                sims.append(overlap / (len(q_emb) + 0.1)) # Jaccard-like
                
        sims = np.array(sims)
            
        ranked_indices = np.argsort(sims)[::-1]
        
        results = []
        for i in range(min(top_k, len(ranked_indices))):
            idx = ranked_indices[i]
            score = float(sims[idx])
            if score >= threshold:
                c = self.chunks[idx]
                results.append({
                    "chunk_id": c["chunk_id"],
                    "document_id": c["source_id"],
                    "source_url": c["provenance"]["url"],
                    "source_title": c["provenance"]["title"],
                    "section_heading": c.get("section_heading", ""),
                    "retrieval_score": score,
                    "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
                    "source_attribution": c["provenance"]["attribution_required"],
                    "adaptation_status": c["provenance"]["adaptation_status"],
                    "text": c["text"]
                })
        
        retrieval_latency_ms = (time.time() - start) * 1000
        
        status = "SUCCESS"
        if not results:
            if float(sims[ranked_indices[0]]) < threshold:
                status = "NO_RELEVANT_SOURCE"
            else:
                status = "LOW_SIMILARITY"
                
        return {
            "results": results,
            "status": status,
            "highest_score": float(sims[ranked_indices[0]]) if len(sims) > 0 else 0.0,
            "retrieval_latency_ms": retrieval_latency_ms
        }


# ---------------------------------------------------------
# MODULE: Evaluation Module
# ---------------------------------------------------------
class EvaluationModule:
    def __init__(self, benchmark_file):
        with open(benchmark_file, 'r', encoding='utf-8') as f:
            self.queries = json.load(f)
            
    def evaluate(self, pipeline_fn, thresholds=[0.1, 0.2, 0.3, 0.4]):
        # Test thresholds to determine the best engineering threshold
        results_by_threshold = {}
        for t in thresholds:
            results_by_threshold[t] = self._run_eval(pipeline_fn, t)
        return results_by_threshold

    def _run_eval(self, pipeline_fn, threshold):
        metrics = {
            "total": len(self.queries),
            "recall_1": 0,
            "recall_3": 0,
            "mrr": 0.0,
            "no_result_correct": 0,
            "false_retrieval": 0, # Retrieved when should be NONE
            "false_no_result": 0, # Returned NONE when should be retrieved
            "translation_failures": 0,
            "latencies_ms": []
        }
        
        per_category = {}
        failures = []
        
        for q in self.queries:
            cat = q['cat']
            if cat not in per_category:
                per_category[cat] = {"total": 0, "correct": 0}
            
            per_category[cat]["total"] += 1
            
            start = time.time()
            res = pipeline_fn(q['query'], top_k=3, threshold=threshold)
            metrics["latencies_ms"].append((time.time() - start) * 1000)
            
            q_obj = res['query_obj']
            retrieval = res['retrieval']
            
            if q_obj['translation_status'] in ['TRANSLATION_FAILED', 'TRANSLATION_SUSPECTED_MEANING_DRIFT']:
                metrics["translation_failures"] += 1
                
            expected = q['expected']
            predicted_docs = [r['document_id'] for r in retrieval['results']]
            
            is_correct = False
            
            if expected == 'NONE':
                if len(predicted_docs) == 0:
                    metrics["no_result_correct"] += 1
                    is_correct = True
                else:
                    metrics["false_retrieval"] += 1
                    failures.append({"query": q['query'], "type": "IRRELEVANT_TOP_RESULT", "score": retrieval['highest_score']})
            else:
                if len(predicted_docs) == 0:
                    metrics["false_no_result"] += 1
                    failures.append({"query": q['query'], "type": "NO_RELEVANT_SOURCE (False Negative)", "score": retrieval['highest_score']})
                else:
                    if expected in predicted_docs:
                        metrics["recall_3"] += 1
                        rank = predicted_docs.index(expected) + 1
                        metrics["mrr"] += 1.0 / rank
                        if rank == 1:
                            metrics["recall_1"] += 1
                            is_correct = True
                    else:
                        failures.append({"query": q['query'], "type": "IRRELEVANT_TOP_RESULT", "predicted": predicted_docs})
                        
            if is_correct:
                per_category[cat]["correct"] += 1

        return {
            "metrics": metrics,
            "per_category": per_category,
            "failures": failures
        }

# ---------------------------------------------------------
# MAIN ORCHESTRATION
# ---------------------------------------------------------
def main():
    print("Starting Gate 5 Controlled In-Memory Retrieval Prototype...")
    
    loader = CorpusLoader('../gate_4c_ingestion')
    chunks = loader.load_corpus()
    print(f"Loaded {len(chunks)} chunks.")
    
    processor = QueryProcessor()
    translator = TranslationAdapter()
    embedder = EmbeddingModule("BAAI/bge-small-en-v1.5")
    retriever = RetrievalModule(chunks, embedder)
    
    def pipeline(query_text, top_k=3, threshold=0.3):
        q_obj = processor.process(query_text)
        q_obj = translator.translate(q_obj)
        
        # Enforce conservative normalization: if translation fails, use normalized query
        if q_obj["translation_status"] == "TRANSLATION_FAILED":
            # Fallback
            q_obj["translated_query"] = q_obj["normalized_query"]
            
        retrieval_res = retriever.search(q_obj, top_k=top_k, threshold=threshold)
        return {
            "query_obj": q_obj,
            "retrieval": retrieval_res
        }
        
    evaluator = EvaluationModule("benchmark_data.json")
    
    # Evaluate thresholds
    # In a real environment with BGE, 0.6 to 0.7 is a good cosine threshold. 
    # With TF-IDF mock, threshold is lower, around 0.1 to 0.2.
    test_thresholds = [0.15, 0.2, 0.5, 0.65] 
    results = evaluator.evaluate(pipeline, thresholds=test_thresholds)
    
    with open("gate_5_evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    print("Evaluation complete. Results saved to gate_5_evaluation_results.json.")

if __name__ == "__main__":
    main()
