import os
import json
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAND_DIR = os.path.join(BASE_DIR, "candidate")
os.makedirs(CAND_DIR, exist_ok=True)

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

config = {
    "gate": "GATE_5.19",
    "configuration_name": "ROBUST_UNICODE_PROCEDURAL_NORMALIZATION_WITH_085_OVERVIEW_DEBIASING",
    "dense_embedding_model": "intfloat/multilingual-e5-small",
    "dense_candidate_depth_k": 15,
    "similarity_metric": "normalized_cosine_dot_product",
    "reranker_model": "BAAI/bge-reranker-v2-m3",
    "reranker_passage_representation": "raw_chunk_text",
    "overview_debiasing_multiplier": 0.85,
    "delivered_context_window": "Top-5",
    "bm25_enabled": False,
    "rrf_enabled": False,
    "normalization_rules": [
        {"pattern": pat, "expansion": exp}
        for pat, exp in TRACK_A_MAPPINGS
    ]
}

config_json = json.dumps(config, indent=2, ensure_ascii=False)
config_hash = hashlib.sha256(config_json.encode('utf-8')).hexdigest()
config["configuration_sha256"] = config_hash

cfg_path = os.path.join(CAND_DIR, "frozen_candidate_configuration.json")
with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"Saved frozen candidate configuration to {cfg_path}")
print(f"Configuration SHA-256: {config_hash}")
