import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util

def main():
    print("Testing BGE-small-en-v1.5 reproducibility...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    
    text = "This is a deterministic reproducibility check for the medical RAG."
    
    emb1 = model.encode([text], normalize_embeddings=True)[0]
    emb2 = model.encode([text], normalize_embeddings=True)[0]
    emb3 = model.encode([text], normalize_embeddings=True)[0]
    
    # Check max difference
    diff12 = np.max(np.abs(emb1 - emb2))
    diff13 = np.max(np.abs(emb1 - emb3))
    
    print(f"Max absolute diff between run 1 and 2: {diff12}")
    print(f"Max absolute diff between run 1 and 3: {diff13}")
    
    if diff12 < 1e-6 and diff13 < 1e-6:
        print("Vectors are identical within floating-point tolerance (1e-6).")
    else:
        print("VECTORS DIFFER!")
        
    print("\nTesting E5-small reproducibility...")
    model2 = SentenceTransformer('intfloat/multilingual-e5-small')
    emb_e1 = model2.encode([text], normalize_embeddings=True)[0]
    emb_e2 = model2.encode([text], normalize_embeddings=True)[0]
    
    diff_e12 = np.max(np.abs(emb_e1 - emb_e2))
    print(f"Max absolute diff between run 1 and 2: {diff_e12}")
    if diff_e12 < 1e-6:
        print("E5 Vectors are identical within floating-point tolerance (1e-6).")
    else:
        print("E5 VECTORS DIFFER!")

if __name__ == "__main__":
    main()
