import json
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_FILE = os.path.join(BASE_DIR, "frozen_candidate_configuration.json")

candidate_config = {
    "gate": "GATE_5.21",
    "selected_candidate": "STRATEGY_2_TRACK_A_NORM_ONLY",
    "architecture_definition": {
        "query_normalization": {
            "type": "unicode_aware_procedural_normalization",
            "regex_strategy": "explicit_boundary_or_whitespace_non_ascii_safe",
            "dictionaries": [
                {"concept": "burns_scalds", "terms": "pura, pure, pora, pore, burn, burns, scald, scalds, blister, পুড়ে, পোড়া, ফোস্কা", "expansion": "burns scalds cool running water first aid"},
                {"concept": "cuts_bleeding", "terms": "kete, kata, katse, rokt, rokto, bleeding, bleed, cut, cuts, graze, grazes, antiseptic, কাটা, রক্ত, রক্তপাত, জীবাণুনাশক", "expansion": "cuts grazes bleeding pressure clean dressing wound"},
                {"concept": "asthma_breathing", "terms": "shash, shash kosto, shash nite kosto, inhaler, inhalers, asthma, হাঁপানি, শ্বাসকষ্ট, ইনহেলার", "expansion": "asthma attack inhaler spacer breathing difficulty"},
                {"concept": "dehydration_fluids", "terms": "pani shunnota, pani kom, shukay, dehydration, dehydrated, ডিহাইড্রেশন, পানিশূন্যতা", "expansion": "dehydration fluid rehydration oral fluids"},
                {"concept": "diarrhoea_vomiting", "terms": "bomi, patla paykhana, diarrhoea, vomiting, বমি, ডায়রিয়া, পাতলা পায়খানা", "expansion": "diarrhoea vomiting oral rehydration fluids"},
                {"concept": "headache_painkillers", "terms": "matha betha, headache, painkiller, paracetamol, মাথাব্যথা, প্যারাসিটামল", "expansion": "headache pain relief painkillers paracetamol"},
                {"concept": "fever_temperature", "terms": "jor, fever, temperature, বাচ্চার জ্বর, জ্বর", "expansion": "fever high temperature children fluids paracetamol"},
                {"concept": "anaphylaxis_allergy", "terms": "allergy, anaphylaxis, shash bondho, অ্যালার্জি, অ্যানাফাইলাক্সিস", "expansion": "anaphylaxis severe allergic reaction adrenaline 999"},
                {"concept": "emergency_urgent", "terms": "emergency, 999, hospital, duto, জরুরি, হাসপাতাল", "expansion": "emergency call 999 go to A&E"}
            ]
        },
        "dense_retrieval": {
            "model": "intfloat/multilingual-e5-small",
            "candidate_depth_k": 15,
            "query_prefix": "query: ",
            "passage_prefix": "passage: ",
            "similarity": "cosine"
        },
        "cross_encoder_reranking": {
            "model": "BAAI/bge-reranker-v2-m3",
            "input_format": "raw_chunk_text",
            "scoring": "raw_logits_sigmoid"
        },
        "overview_debiasing": {
            "rule": "0.85x score multiplier for introductory overview chunks ending in -HYB-000",
            "multiplier": 0.85
        },
        "context_assembly": {
            "final_top_k": 5,
            "diversification_cap": "none (tested max_per_doc=2 and max_per_doc=3 degraded R@5 on DEV)"
        }
    },
    "selection_justification": "Strategy 2 achieved the highest R@5 (39/40 = 97.5%), highest R@3 (31/40 = 77.5%), highest R@1 (22/40 = 55.0%), and highest MRR (0.6908) on DEV with 0 regressions. Same-source caps (Strategy 3 & 4) severely degraded R@5 (to 87.5% and 72.5%) by forcing out-of-topic chunks into Top-5. Lexical specificity scoring (Strategy 5) reduced MRR and R@3."
}

config_json = json.dumps(candidate_config, indent=2, sort_keys=True, ensure_ascii=False)
sha256_hash = hashlib.sha256(config_json.encode("utf-8")).hexdigest()
candidate_config["configuration_sha256"] = sha256_hash

with open(CANDIDATE_FILE, "w", encoding="utf-8") as f:
    json.dump(candidate_config, f, indent=2, ensure_ascii=False)

print(f"Frozen Gate 5.21 candidate configuration written to {CANDIDATE_FILE}")
print(f"SHA-256: {sha256_hash}")
