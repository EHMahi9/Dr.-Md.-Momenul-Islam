import json
import re
import sys
import numpy as np
from sentence_transformers import SentenceTransformer

sys.stdout.reconfigure(encoding='utf-8')

# Current baseline mapping
BASE_MAPPINGS = [
    (r'\b(pani\s*shunnota|pani\s*kom|dehydration|ডিহাইড্রেশন|পানিশূন্যতা)\b', 'dehydration fluid rehydration oral fluids'),
    (r'\b(shash\s*kosto|shash\s*nite\s*kosto|inhaler|asthma|হাঁপানি|শ্বাসকষ্ট|ইনহেলার)\b', 'asthma attack inhaler spacer breathing difficulty'),
    (r'\b(pura|pure\s*geche|burn|scald|blister|পুড়ে\s*গেলে|পোড়া|ফোস্কা)\b', 'burns scalds cold water cool running water blister first aid'),
    (r'\b(kete\s*geche|rokto|bleeding|cut|graze|antiseptic|কাটা|রক্তপাত|জীবাণুনাশক)\b', 'cuts grazes bleeding pressure clean dressing wound'),
    (r'\b(bomi|patla\s*paykhana|diarrhoea|vomiting|বমি|ডায়রিয়া|পাতলা\s*পায়খানা)\b', 'diarrhoea vomiting oral rehydration fluids'),
    (r'\b(matha\s*betha|headache|painkiller|paracetamol|মাথাব্যথা|প্যারাসিটামল)\b', 'headache pain relief painkillers paracetamol'),
    (r'\b(jor|fever|temperature|বাচ্চার\s*জ্বর|জ্বর)\b', 'fever high temperature children fluids paracetamol'),
    (r'\b(allergy|anaphylaxis|shash\s*bondho|অ্যালার্জি|অ্যানাফাইলাক্সিস)\b', 'anaphylaxis severe allergic reaction adrenaline 999'),
    (r'\b(emergency|999|hospital|duto|জরুরি|হাসপাতাল)\b', 'emergency call 999 go to A&E')
]

# Track A: Robust, transliteration-tolerant and procedural mapping
TRACK_A_MAPPINGS = [
    # Burns / Scalds
    (r'\b(pura|pure|pora|pore|পুড়ে|পোড়া|ফোস্কা|burn|burns|scald|scalds|blister)\b', 'burns scalds cool running water cold water first aid blister'),
    # Cuts / Bleeding
    (r'\b(kete|kata|katse|কাটা|rokt|rokto|রক্ত|রক্তপাত|bleeding|bleed|cut|cuts|graze|grazes|antiseptic|জীবাণুনাশক)\b', 'cuts grazes bleeding direct pressure clean dressing wound'),
    # Asthma / Breathing
    (r'\b(shash|shash\s*kosto|shash\s*nite\s*kosto|inhaler|inhalers|asthma|হাঁপানি|শ্বাসকষ্ট|ইনহেলার)\b', 'asthma attack inhaler spacer breathing difficulty'),
    # Dehydration / Fluids
    (r'\b(pani\s*shunnota|pani\s*kom|shukay|dehydration|dehydrated|ডিহাইড্রেশন|পানিশূন্যতা)\b', 'dehydration fluid rehydration oral fluids electrolytes'),
    # Diarrhoea / Vomiting
    (r'\b(bomi|patla\s*paykhana|diarrhoea|vomiting|বমি|ডায়রিয়া|পাতলা\s*পায়খানা)\b', 'diarrhoea vomiting oral rehydration fluids'),
    # Headache / Pain
    (r'\b(matha\s*betha|headache|painkiller|paracetamol|মাথাব্যথা|প্যারাসিটামল)\b', 'headache pain relief painkillers paracetamol'),
    # Fever
    (r'\b(jor|fever|temperature|বাচ্চার\s*জ্বর|জ্বর)\b', 'fever high temperature children fluids paracetamol'),
    # Severe Allergy / Anaphylaxis
    (r'\b(allergy|anaphylaxis|shash\s*bondho|অ্যালার্জি|অ্যানাফাইলাক্সিস)\b', 'anaphylaxis severe allergic reaction adrenaline 999'),
    # Emergency / Hospital / 999
    (r'\b(emergency|999|hospital|a&e|duto|জরুরি|হাসপাতাল)\b', 'emergency call 999 go to A&E ambulance'),
    # Procedural Duration / First Aid Timing
    (r'\b(koto\s*minute|kotokkhon|কতক্ষণ|কত\s*মিনিট|duration|minutes?)\b', 'cool running water 20 minutes duration direct pressure')
]

def normalize_text(query: str, mappings) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in mappings:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        return f"{query} ({' '.join(norm_terms)})"
    return query

# Load resources
with open('research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json', 'r', encoding='utf-8') as f:
    benchmark = json.load(f)
dev_queries = [q for q in benchmark if q['benchmark_split'] == 'DEV']

with open('research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

with open('research/gate_5_9_optimization/chunk_gold_labels.json', 'r', encoding='utf-8') as f:
    gold_labels = json.load(f)

print("Loading multilingual-e5-small...")
dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
passage_texts = [f"passage: {c['text']}" for c in chunks]
chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

def eval_dense(mappings, label):
    hits_15 = 0
    ranks = []
    per_query_res = []
    for q in dev_queries:
        qid = q['query_id']
        raw_q = q['query_text']
        norm_q = normalize_text(raw_q, mappings)
        acceptable_cids = gold_labels[qid]['gold_chunk_ids']

        q_emb = dense_model.encode([f"query: {norm_q}"], normalize_embeddings=True)
        scores = np.dot(q_emb, chunk_embeddings.T)[0]
        top15_indices = np.argsort(-scores)[:15]
        top15_cids = [chunks[idx]['chunk_id'] for idx in top15_indices]

        hit = any(cid in acceptable_cids for cid in top15_cids)
        if hit:
            hits_15 += 1
            # find rank
            all_indices = np.argsort(-scores)
            all_cids = [chunks[idx]['chunk_id'] for idx in all_indices]
            rank = min([all_cids.index(cid) + 1 for cid in acceptable_cids if cid in all_cids])
        else:
            rank = 0
        ranks.append(rank)
        per_query_res.append({
            "query_id": qid,
            "language": q['language_category'],
            "raw_query": raw_q,
            "normalized_query": norm_q,
            "dense_rank": rank,
            "in_top15": hit
        })

    print(f"\n{label} Dense Top-15 Recall: {hits_15}/40 ({hits_15/40*100:.2f}%)")
    for r in per_query_res:
        if not r['in_top15']:
            print(f"  FAILED: {r['query_id']} ({r['language']}) | {r['raw_query']}")
    return hits_15, ranks, per_query_res

print("=" * 80)
print("EVALUATING DENSE TOP-15 CANDIDATE POOL RECALL")
print("=" * 80)
eval_dense(BASE_MAPPINGS, "BASELINE")
eval_dense(TRACK_A_MAPPINGS, "TRACK_A_EXPANDED")
