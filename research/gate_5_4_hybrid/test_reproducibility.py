import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from rank_bm25 import BM25Okapi
import re

def simple_tokenize(text):
    return re.findall(r'\w+', text.lower())

def main():
    print("Testing BGE-M3 reproducibility...")
    model = SentenceTransformer('BAAI/bge-m3')
    
    text = "This is a deterministic reproducibility check for the hybrid RAG."
    
    emb1 = model.encode([text], normalize_embeddings=True)[0]
    emb2 = model.encode([text], normalize_embeddings=True)[0]
    emb3 = model.encode([text], normalize_embeddings=True)[0]
    
    # Check max difference
    diff12 = np.max(np.abs(emb1 - emb2))
    diff13 = np.max(np.abs(emb1 - emb3))
    
    print(f"Max absolute diff between run 1 and 2: {diff12}")
    print(f"Max absolute diff between run 1 and 3: {diff13}")
    
    if diff12 < 1e-6 and diff13 < 1e-6:
        print("BGE-M3 Dense Vectors are identical within floating-point tolerance (1e-6).")
    else:
        print("BGE-M3 VECTORS DIFFER!")
        
    print("\nTesting BGE-Reranker reproducibility...")
    reranker_tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-reranker-v2-m3')
    reranker_model = AutoModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-v2-m3')
    reranker_model.eval()
    
    query = "How to treat a fever?"
    doc = "Paracetamol is used to treat fever in adults."
    
    inputs = reranker_tokenizer([[query, doc]], return_tensors='pt', padding=True, truncation=True, max_length=512)
    
    with torch.no_grad():
        score1 = reranker_model(**inputs, return_dict=True).logits.view(-1,).float().numpy()[0]
        score2 = reranker_model(**inputs, return_dict=True).logits.view(-1,).float().numpy()[0]
        
    diff_r = np.abs(score1 - score2)
    print(f"Reranker Run 1 Score: {score1}")
    print(f"Reranker Run 2 Score: {score2}")
    print(f"Max absolute diff between run 1 and 2: {diff_r}")
    
    if diff_r < 1e-6:
        print("BGE-Reranker Scores are identical within floating-point tolerance (1e-6).")
    else:
        print("BGE-Reranker SCORES DIFFER!")
        
    print("\nTesting BM25 reproducibility...")
    corpus = ["This is doc one.", "This is doc two.", "Fever paracetamol treatment."]
    tokenized = [simple_tokenize(c) for c in corpus]
    bm25 = BM25Okapi(tokenized)
    
    q_tok = simple_tokenize("fever treatment")
    s1 = bm25.get_scores(q_tok)
    s2 = bm25.get_scores(q_tok)
    
    diff_bm25 = np.max(np.abs(s1 - s2))
    print(f"BM25 Max absolute diff: {diff_bm25}")
    if diff_bm25 < 1e-6:
        print("BM25 Scores are identical within floating-point tolerance (1e-6).")
    else:
        print("BM25 SCORES DIFFER!")

if __name__ == "__main__":
    main()
