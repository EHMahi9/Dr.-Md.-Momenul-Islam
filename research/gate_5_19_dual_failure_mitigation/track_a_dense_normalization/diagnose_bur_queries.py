import json
import re
import sys
import numpy as np
from sentence_transformers import SentenceTransformer

sys.stdout.reconfigure(encoding='utf-8')

with open('research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json', 'r', encoding='utf-8') as f:
    benchmark = json.load(f)
dev_queries = {q['query_id']: q for q in benchmark if q['benchmark_split'] == 'DEV'}

with open('research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)
chunks_by_id = {c['chunk_id']: c for c in chunks}

dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
passage_texts = [f"passage: {c['text']}" for c in chunks]
chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

# Test different normalizations for DEV-BUR-02 and DEV-BUR-03
test_q2 = "হাত পুড়ে গেলে কতক্ষণ ঠাণ্ডা পানির নিচে রাখতে হবে?"
test_q3 = "pure gele thanda pani koto minute dhalbo?"

gold_cid = "DOC-NHS-005-HYB-000"
print(f"Target Gold Chunk ({gold_cid}):")
print(chunks_by_id[gold_cid]['text'])
print("=" * 80)

candidates_to_test = [
    ("Raw DEV-BUR-02", test_q2),
    ("DEV-BUR-02 + (burns scalds cool running water first aid)", f"{test_q2} (burns scalds cool running water first aid)"),
    ("DEV-BUR-02 + (burns scalds cool running water 20 minutes first aid)", f"{test_q2} (burns scalds cool running water 20 minutes first aid)"),
    ("DEV-BUR-02 + (burns scalds cool running water for 20 minutes first aid treatment)", f"{test_q2} (burns scalds cool running water for 20 minutes first aid treatment)"),
    ("Raw DEV-BUR-03", test_q3),
    ("DEV-BUR-03 + (burns scalds cool running water first aid)", f"{test_q3} (burns scalds cool running water first aid)"),
    ("DEV-BUR-03 + (burns scalds cool running water 20 minutes first aid)", f"{test_q3} (burns scalds cool running water 20 minutes first aid)"),
    ("DEV-BUR-03 + (burns scalds cool running water for 20 minutes first aid treatment)", f"{test_q3} (burns scalds cool running water for 20 minutes first aid treatment)")
]

for label, q_text in candidates_to_test:
    q_emb = dense_model.encode([f"query: {q_text}"], normalize_embeddings=True)
    scores = np.dot(q_emb, chunk_embeddings.T)[0]
    top15_indices = np.argsort(-scores)[:15]
    top15_cids = [chunks[idx]['chunk_id'] for idx in top15_indices]
    
    in_top15 = gold_cid in top15_cids
    rank = (top15_cids.index(gold_cid) + 1) if in_top15 else 0
    print(f"[{'PASS' if in_top15 else 'FAIL'}] {label} -> Gold Rank: {rank}")
    if not in_top15:
        all_order = np.argsort(-scores)
        all_cids = [chunks[idx]['chunk_id'] for idx in all_order]
        full_rank = all_cids.index(gold_cid) + 1
        print(f"  Full rank: {full_rank} | Top 3 retrieved: {top15_cids[:3]}")
