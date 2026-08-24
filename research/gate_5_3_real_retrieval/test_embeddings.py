import time
from sentence_transformers import SentenceTransformer

models = ["BAAI/bge-small-en-v1.5", "intfloat/multilingual-e5-small"]
texts = ["This is a test document.", "Another passage for embedding."]
queries = ["test query", "find passage"]

for m in models:
    print(f"Loading {m}...")
    t0 = time.time()
    try:
        model = SentenceTransformer(m)
        t1 = time.time()
        print(f"Loaded {m} in {t1-t0:.2f}s")
        
        # Test passage
        if "e5" in m.lower():
            passages = ["passage: " + t for t in texts]
            qs = ["query: " + q for q in queries]
        else:
            passages = texts
            qs = queries
            
        t2 = time.time()
        p_embs = model.encode(passages, normalize_embeddings=True)
        q_embs = model.encode(qs, normalize_embeddings=True)
        t3 = time.time()
        print(f"Embedded in {t3-t2:.2f}s")
        print(f"Embedding shape: {p_embs.shape}")
    except Exception as e:
        print(f"Error loading {m}: {e}")
