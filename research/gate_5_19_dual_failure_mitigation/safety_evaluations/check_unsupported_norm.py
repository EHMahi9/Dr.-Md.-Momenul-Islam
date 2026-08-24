import json
import re
import sys
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

sys.stdout.reconfigure(encoding='utf-8')

# Robust Unicode-aware procedural normalization dictionary
PROCEDURAL_NORMALIZATION_RULES = [
    # Burns & Scalds (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(pura|pure|pora|pore|burn|burns|scald|scalds|blister)(?:\b|(?=$)|(?=\s|[.,?!]))|(পুড়ে|পোড়া|ফোস্কা)', 
     'burns scalds cool running water first aid'),
    
    # Cuts, Grazes & Bleeding (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(kete|kata|katse|rokt|rokto|bleeding|bleed|cut|cuts|graze|grazes|antiseptic)(?:\b|(?=$)|(?=\s|[.,?!]))|(কাটা|রক্ত|রক্তপাত|জীবাণুনাশক)', 
     'cuts grazes bleeding pressure clean dressing wound'),
    
    # Asthma & Breathing (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(shash|shash\s*kosto|shash\s*nite\s*kosto|inhaler|inhalers|asthma)(?:\b|(?=$)|(?=\s|[.,?!]))|(হাঁপানি|শ্বাসকষ্ট|ইনহেলার)', 
     'asthma attack inhaler spacer breathing difficulty'),
    
    # Dehydration & Fluids (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(pani\s*shunnota|pani\s*kom|shukay|dehydration|dehydrated)(?:\b|(?=$)|(?=\s|[.,?!]))|(ডিহাইড্রেশন|পানিশূন্যতা)', 
     'dehydration fluid rehydration oral fluids'),
    
    # Diarrhoea & Vomiting (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(bomi|patla\s*paykhana|diarrhoea|vomiting)(?:\b|(?=$)|(?=\s|[.,?!]))|(বমি|ডায়রিয়া|পাতলা\s*পায়খানা)', 
     'diarrhoea vomiting oral rehydration fluids'),
    
    # Headache & Painkillers (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(matha\s*betha|headache|painkiller|paracetamol)(?:\b|(?=$)|(?=\s|[.,?!]))|(মাথাব্যথা|প্যারাসিটামল)', 
     'headache pain relief painkillers paracetamol'),
    
    # Fever (Bengali + Banglish + English)
    (r'(?:\b|(?<=^)|(?<=\s))(jor|fever|temperature)(?:\b|(?=$)|(?=\s|[.,?!]))|(বাচ্চার\s*জ্বর|জ্বর)', 
     'fever high temperature children fluids paracetamol'),
    
    # Anaphylaxis & Severe Allergy
    (r'(?:\b|(?<=^)|(?<=\s))(allergy|anaphylaxis|shash\s*bondho)(?:\b|(?=$)|(?=\s|[.,?!]))|(অ্যালার্জি|অ্যানাফাইলাক্সিস)', 
     'anaphylaxis severe allergic reaction adrenaline 999'),
    
    # Emergency / Hospital / 999
    (r'(?:\b|(?<=^)|(?<=\s))(emergency|999|hospital|duto)(?:\b|(?=$)|(?=\s|[.,?!]))|(জরুরি|হাসপাতাল)', 
     'emergency call 999 go to A&E')
]

def normalize_query_robust(query: str) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in PROCEDURAL_NORMALIZATION_RULES:
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
unsupported_queries = [q for q in benchmark if q.get('is_unsupported', False)]

with open('research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

dense_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
passage_texts = [f"passage: {c['text']}" for c in chunks]
chunk_embeddings = dense_model.encode(passage_texts, normalize_embeddings=True)

print(f"Total Unsupported Queries: {len(unsupported_queries)}")
for q in unsupported_queries:
    raw_q = q['query_text']
    norm_q = normalize_query_robust(raw_q)
    print(f"[{q['query_id']}] {raw_q}")
    if raw_q != norm_q:
        print(f"  -> Normalized: {norm_q}")

print("\nSafety check on unsupported query text normalization: Complete.")
