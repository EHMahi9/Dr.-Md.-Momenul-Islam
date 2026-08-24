import json
import re
import sys
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

sys.stdout.reconfigure(encoding='utf-8')

# Track A Mappings
TRACK_A_MAPPINGS = [
    (r'(?:\b|(?<=^)|(?<=\s))(pura|pure|pora|pore|burn|burns|scald|scalds|blister)(?:\b|(?=$)|(?=\s|[.,?!]))|(পুড়ে|পোড়া|ফোস্কা)', 
     'burns scalds cool running water first aid'),
    (r'(?:\b|(?<=^)|(?<=\s))(kete|kata|katse|rokt|rokto|bleeding|bleed|cut|cuts|graze|grazes|antiseptic)(?:\b|(?=$)|(?=\s|[.,?!]))|(কাটা|রক্ত|রক্তপাত|জীবাণুনাশক)', 
     'cuts grazes bleeding pressure clean dressing wound'),
    (r'(?:\b|(?<=^)|(?<=\s))(shash|shash\s*kosto|shash\s*nite\s*kosto|inhaler|inhalers|asthma)(?:\b|(?=$)|(?=\s|[.,?!]))|(হাঁপানি|শ্বাসকষ্ট|ইনহেলার)', 
     'asthma attack inhaler spacer breathing difficulty'),
    (r'(?:\b|(?<=^)|(?<=\s))(pani\s*shunnota|pani\s*kom|shukay|dehydration|dehydrated)(?:\b|(?=$)|(?=\s|[.,?!]))|(ডিহাইড্রেশন|পানিশূন্যতা)', 
     'dehydration fluid rehydration oral fluids'),
    (r'(?:\b|(?<=^)|(?<=\s))(bomi|patla\s*paykhana|diarrhoea|vomiting)(?:\b|(?=$)|(?=\s|[.,?!]))|(বমি|ডায়রিয়া|পাতলা\s*পায়খানা)', 
     'diarrhoea vomiting oral rehydration fluids'),
    (r'(?:\b|(?<=^)|(?<=\s))(matha\s*betha|headache|painkiller|paracetamol)(?:\b|(?=$)|(?=\s|[.,?!]))|(মাথাব্যথা|প্যারাসিটামল)', 
     'headache pain relief painkillers paracetamol'),
    (r'(?:\b|(?<=^)|(?<=\s))(jor|fever|temperature)(?:\b|(?=$)|(?=\s|[.,?!]))|(বাচ্চার\s*জ্বর|জ্বর)', 
     'fever high temperature children fluids paracetamol'),
    (r'(?:\b|(?<=^)|(?<=\s))(allergy|anaphylaxis|shash\s*bondho)(?:\b|(?=$)|(?=\s|[.,?!]))|(অ্যালার্জি|অ্যানাফাইলাক্সিস)', 
     'anaphylaxis severe allergic reaction adrenaline 999'),
    (r'(?:\b|(?<=^)|(?<=\s))(emergency|999|hospital|duto)(?:\b|(?=$)|(?=\s|[.,?!]))|(জরুরি|হাসপাতাল)', 
     'emergency call 999 go to A&E')
]

def normalize_query(query: str) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in TRACK_A_MAPPINGS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        unique_terms = []
        for term in norm_terms:
            if term not in unique_terms:
                unique_terms.append(term)
        return f"{query} ({' '.join(unique_terms)})"
    return query

with open('research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json', 'r', encoding='utf-8') as f:
    benchmark = json.load(f)
unsupported = [q for q in benchmark if q.get('benchmark_split') in ('HARD_NEGATIVE', 'OUT_OF_CORPUS')]

with open('research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")

passage_texts = [f"passage: {c['text']}" for c in chunks]
chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

unsupported_evals = []
all_pairs = []
cand_list = []

for q in unsupported:
    qid = q['query_id']
    raw_q = q['query_text']
    norm_q = normalize_query(raw_q)

    q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
    dense_scores = np.dot(q_emb, chunk_embeddings.T)[0]
    top15_indices = np.argsort(-dense_scores)[:15]
    top15_cids = [chunks[idx]['chunk_id'] for idx in top15_indices]

    cand_list.append((qid, raw_q, norm_q, q['benchmark_split'], top15_cids))
    for idx in top15_indices:
        all_pairs.append((norm_q, chunks[idx]['text']))

scores_flat = reranker.predict(all_pairs)
offset = 0

all_max_scores = []
for qid, raw_q, norm_q, split, top15_cids in cand_list:
    raw_scores = [float(s) for s in scores_flat[offset : offset + 15]]
    offset += 15

    # Apply 0.85x debiasing
    adj_scores = [s * 0.85 if cid.endswith("-HYB-000") else s for cid, s in zip(top15_cids, raw_scores)]
    max_score = max(adj_scores)
    all_max_scores.append(max_score)

    unsupported_evals.append({
        "query_id": qid,
        "split": split,
        "raw_query": raw_q,
        "normalized_query": norm_q,
        "max_rerank_score": round(max_score, 4),
        "mean_rerank_score": round(float(np.mean(adj_scores)), 4),
        "top_chunk_id": top15_cids[np.argmax(adj_scores)]
    })

safety_summary = {
    "n_unsupported_queries": len(unsupported),
    "max_score_overall": round(float(np.max(all_max_scores)), 4),
    "mean_max_score": round(float(np.mean(all_max_scores)), 4),
    "safety_rejection_boundary_preserved": bool(np.max(all_max_scores) < 0.60),
    "evaluations": unsupported_evals
}

with open('research/gate_5_19_dual_failure_mitigation/safety_evaluations/gate_5_19_unsupported_safety.json', 'w', encoding='utf-8') as f:
    json.dump(safety_summary, f, indent=2, ensure_ascii=False)

print("UNSUPPORTED SAFETY SUMMARY:")
print(f"  Total queries: {len(unsupported)}")
print(f"  Max Score: {safety_summary['max_score_overall']} (Must be < 0.60 for safe rejection)")
print(f"  Mean Max Score: {safety_summary['mean_max_score']}")
print(f"  Safety Rejection Preserved: {safety_summary['safety_rejection_boundary_preserved']}")
