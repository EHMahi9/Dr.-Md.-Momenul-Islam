import json
import re
import sys
import numpy as np
from sentence_transformers import SentenceTransformer

sys.stdout.reconfigure(encoding='utf-8')

# Clean, robust procedural normalization
CLEAN_PROCEDURAL_MAPPINGS = [
    # Burns / Scalds
    (r'\b(pura|pure|pora|pore|পুড়ে|পোড়া|ফোস্কা|burn|burns|scald|scalds|blister)\b', 'burns scalds cool running water first aid'),
    # Cuts / Bleeding
    (r'\b(kete|kata|katse|কাটা|rokt|rokto|রক্ত|রক্তপাত|bleeding|bleed|cut|cuts|graze|grazes|antiseptic|জীবাণুনাশক)\b', 'cuts grazes bleeding pressure clean dressing wound'),
    # Asthma / Breathing
    (r'\b(shash|shash\s*kosto|shash\s*nite\s*kosto|inhaler|inhalers|asthma|হাঁপানি|শ্বাসকষ্ট|ইনহেলার)\b', 'asthma attack inhaler spacer breathing difficulty'),
    # Dehydration / Fluids
    (r'\b(pani\s*shunnota|pani\s*kom|shukay|dehydration|dehydrated|ডিহাইড্রেশন|পানিশূন্যতা)\b', 'dehydration fluid rehydration oral fluids'),
    # Diarrhoea / Vomiting
    (r'\b(bomi|patla\s*paykhana|diarrhoea|vomiting|বমি|ডায়রিয়া|পাতলা\s*পায়খানা)\b', 'diarrhoea vomiting oral rehydration fluids'),
    # Headache / Pain
    (r'\b(matha\s*betha|headache|painkiller|paracetamol|মাথাব্যথা|প্যারাসিটামল)\b', 'headache pain relief painkillers paracetamol'),
    # Fever
    (r'\b(jor|fever|temperature|বাচ্চার\s*জ্বর|জ্বর)\b', 'fever high temperature children fluids paracetamol'),
    # Severe Allergy / Anaphylaxis
    (r'\b(allergy|anaphylaxis|shash\s*bondho|অ্যালার্জি|অ্যানাফাইলাক্সিস)\b', 'anaphylaxis severe allergic reaction adrenaline 999'),
    # Emergency / Hospital / 999
    (r'\b(emergency|999|hospital|duto|জরুরি|হাসপাতাল)\b', 'emergency call 999 go to A&E')
]

def normalize_text(query: str) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in CLEAN_PROCEDURAL_MAPPINGS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        return f"{query} ({' '.join(norm_terms)})"
    return query

with open('research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json', 'r', encoding='utf-8') as f:
    benchmark = json.load(f)
dev_queries = [q for q in benchmark if q['benchmark_split'] == 'DEV']

with open('research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

with open('research/gate_5_9_optimization/chunk_gold_labels.json', 'r', encoding='utf-8') as f:
    gold_labels = json.load(f)

dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
passage_texts = [f"passage: {c['text']}" for c in chunks]
chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

hits_15 = 0
results = []
for q in dev_queries:
    qid = q['query_id']
    raw_q = q['query_text']
    norm_q = normalize_text(raw_q)
    acceptable_cids = gold_labels[qid]['gold_chunk_ids']

    q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
    scores = np.dot(q_emb, chunk_embeddings.T)[0]
    top15_indices = np.argsort(-scores)[:15]
    top15_cids = [chunks[idx]['chunk_id'] for idx in top15_indices]

    hit = any(cid in acceptable_cids for cid in top15_cids)
    if hit:
        hits_15 += 1
    else:
        all_order = np.argsort(-scores)
        all_cids = [chunks[idx]['chunk_id'] for idx in all_order]
        best_rank = min([all_cids.index(cid) + 1 for cid in acceptable_cids if cid in all_cids])
        print(f"FAILED: {qid} ({q['language_category']}) - {raw_q}")
        print(f"  Normalized: {norm_q}")
        print(f"  Gold CIDs: {acceptable_cids} | Best Rank: {best_rank}")

print(f"\nDense Candidate Pool Recall@15 on DEV: {hits_15}/40 ({hits_15/40*100:.2f}%)")
