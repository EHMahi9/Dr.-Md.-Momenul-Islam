"""
Phase 6H: Banglish Retrieval Normalization Candidate Evaluation Script.
Evaluates CONTROL, CANDIDATE A, CANDIDATE B, and CANDIDATE C against the 48-case development evaluation set
from Phase 6F on the 119-chunk active NHS corpus.

HYPERPARAMETERS (FROZEN STRATEGY 5):
- Dense candidate depth: K = 15 (multilingual-e5-small)
- Final output depth: Top-5 (BAAI/bge-reranker-v2-m3)
- Topical anchor weight: lambda = 0.10
- Lexical overlap weight: alpha = 0.03
- Overview debiasing penalty: 0.85 (applied to -HYB-000 chunks)
"""

import os
import sys
import json
import re
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer, CrossEncoder

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

from app.core.config import settings

# -----------------------------------------------------------------------------
# NORMALIZATION PIPELINES
# -----------------------------------------------------------------------------

# CONTROL: Current Strategy 5 Track A Normalization
CONTROL_MAPPINGS = [
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

def normalize_control(query: str) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in CONTROL_MAPPINGS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        unique_terms = []
        for term in norm_terms:
            if term not in unique_terms:
                unique_terms.append(term)
        return f"{query} ({' '.join(unique_terms)})"
    return query


# CANDIDATE A: Expanded Deterministic Transliteration Dictionary
CANDIDATE_A_MAPPINGS = [
    # Burns & Scalds (adds agun, agune, aguner, pura, porle)
    (r'(?:\b|(?<=^)|(?<=\s))(agun|agune|aguner|pura|pure|pora|pore|porle|burn|burns|scald|scalds|blister)(?:\b|(?=$)|(?=\s|[.,?!]))|(আগুন|আগুনে|পুড়ে|পোড়া|ফোস্কা)', 
     'burns scalds cool running water first aid remove clothing'),
    # Nosebleeds / Epistaxis (adds nak, naker, nak die, nak theke, nak diye)
    (r'(?:\b|(?<=^)|(?<=\s))(nak|naker|nak\s*die|nak\s*diye|nak\s*theke|nosebleed|epistaxis)(?:\b|(?=$)|(?=\s|[.,?!]))|(নাক\s*দিয়ে\s*রক্ত|নাক\s*থেকে\s*রক্ত|নাক)', 
     'nosebleed epistaxis pinch soft part nose lean forward first aid'),
    # Cuts & Grazes / General Bleeding
    (r'(?:\b|(?<=^)|(?<=\s))(kete|kata|katse|rokt|rokto|bleeding|bleed|cut|cuts|graze|grazes|antiseptic)(?:\b|(?=$)|(?=\s|[.,?!]))|(কাটা|রক্ত|রক্তপাত|জীবাণুনাশক)', 
     'cuts grazes bleeding pressure clean dressing wound'),
    # Stroke / FAST
    (r'(?:\b|(?<=^)|(?<=\s))(stroke|muk\s*beke|haat\s*obos|obosh|paralysis)(?:\b|(?=$)|(?=\s|[.,?!]))|(স্ট্রোক|প্যারালাইসিস|মুখ\s*বেঁকে)', 
     'stroke FAST face arms speech emergency call 999'),
    # Asthma / Breathing difficulty
    (r'(?:\b|(?<=^)|(?<=\s))(shash|shash\s*kosto|shash\s*nite\s*kosto|inhaler|inhalers|asthma)(?:\b|(?=$)|(?=\s|[.,?!]))|(হাঁপানি|শ্বাসকষ্ট|ইনহেলার)', 
     'asthma attack inhaler spacer breathing difficulty'),
    # Dehydration
    (r'(?:\b|(?<=^)|(?<=\s))(pani\s*shunnota|pani\s*kom|shukay|dehydration|dehydrated)(?:\b|(?=$)|(?=\s|[.,?!]))|(ডিহাইড্রেশন|পানিশূন্যতা)', 
     'dehydration fluid rehydration oral fluids'),
    # Diarrhoea & Vomiting
    (r'(?:\b|(?<=^)|(?<=\s))(bomi|patla\s*paykhana|diarrhoea|vomiting)(?:\b|(?=$)|(?=\s|[.,?!]))|(বমি|ডায়রিয়া|পাতলা\s*পায়খানা)', 
     'diarrhoea vomiting oral rehydration fluids'),
    # Headache & Painkillers
    (r'(?:\b|(?<=^)|(?<=\s))(matha\s*betha|matha\s*byatha|matha\s*ghura|headache|painkiller|paracetamol)(?:\b|(?=$)|(?=\s|[.,?!]))|(মাথাব্যথা|মাথা\s*ঘোরা|প্যারাসিটামল)', 
     'headache pain relief painkillers paracetamol'),
    # Fever in Children
    (r'(?:\b|(?<=^)|(?<=\s))(jor|fever|temperature|temp)(?:\b|(?=$)|(?=\s|[.,?!]))|(বাচ্চার\s*জ্বর|জ্বর)', 
     'fever high temperature children fluids paracetamol'),
    # Allergic Rhinitis & Allergy
    (r'(?:\b|(?<=^)|(?<=\s))(chulkani|hachi|sordi|allergy|anaphylaxis|shash\s*bondho)(?:\b|(?=$)|(?=\s|[.,?!]))|(অ্যালার্জি|অ্যানাফাইলাক্সিস|হাঁচি|সর্দি)', 
     'allergic rhinitis allergy sneezing antihistamines anaphylaxis 999'),
    # Emergency / Hospital
    (r'(?:\b|(?<=^)|(?<=\s))(emergency|999|hospital|duto|druto|borti)(?:\b|(?=$)|(?=\s|[.,?!]))|(জরুরি|হাসপাতাল|ভর্তি)', 
     'emergency call 999 go to A&E')
]

def normalize_candidate_a(query: str) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in CANDIDATE_A_MAPPINGS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        unique_terms = []
        for term in norm_terms:
            if term not in unique_terms:
                unique_terms.append(term)
        return f"{query} ({' '.join(unique_terms)})"
    return query


# CANDIDATE B: Context-Aware Disambiguation
def normalize_candidate_b(query: str) -> str:
    q_lower = query.lower()
    norm_terms = []
    
    # 1. Disambiguate Bleeding vs Nosebleed
    has_nose = bool(re.search(r'\b(nak|naker|nose|nasal|epistaxis)\b|(নাক|নাকের)', q_lower))
    has_bleeding = bool(re.search(r'\b(kete|kata|katse|rokt|rokto|bleeding|bleed|cut|cuts|graze|grazes)\b|(কাটা|রক্ত|রক্তপাত)', q_lower))
    
    if has_nose:
        norm_terms.append('nosebleed epistaxis pinch soft part nose lean forward first aid')
    elif has_bleeding:
        norm_terms.append('cuts grazes bleeding pressure clean dressing wound')
        
    # 2. Burns context check
    has_burn_context = bool(re.search(r'\b(agun|agune|pura|pure|pora|burn|burns|scald|scalds|blister)\b|(আগুন|আগুনে|পুড়ে|পোড়া|ফোস্কা)', q_lower))
    if has_burn_context:
        norm_terms.append('burns scalds cool running water first aid remove clothing')
        
    # 3. Standard other conditions
    if re.search(r'\b(shash|shash\s*kosto|inhaler|asthma)\b|(হাঁপানি|শ্বাসকষ্ট|ইনহেলার)', q_lower):
        norm_terms.append('asthma attack inhaler spacer breathing difficulty')
    if re.search(r'\b(pani\s*shunnota|pani\s*kom|dehydration|dehydrated)\b|(ডিহাইড্রেশন|পানিশূন্যতা)', q_lower):
        norm_terms.append('dehydration fluid rehydration oral fluids')
    if re.search(r'\b(bomi|patla\s*paykhana|diarrhoea|vomiting)\b|(বমি|ডায়রিয়া|পাতলা\s*পায়খানা)', q_lower):
        norm_terms.append('diarrhoea vomiting oral rehydration fluids')
    if re.search(r'\b(matha\s*betha|headache|painkiller|paracetamol)\b|(মাথাব্যথা|প্যারাসিটামল)', q_lower):
        norm_terms.append('headache pain relief painkillers paracetamol')
    if re.search(r'\b(jor|fever|temperature)\b|(বাচ্চার\s*জ্বর|জ্বর)', q_lower):
        norm_terms.append('fever high temperature children fluids paracetamol')
    if re.search(r'\b(allergy|anaphylaxis|shash\s*bondho)\b|(অ্যালার্জি|অ্যানাফাইলাক্সিস)', q_lower):
        norm_terms.append('anaphylaxis severe allergic reaction adrenaline 999')
    if re.search(r'\b(stroke|muk\s*beke|haat\s*obos)\b|(স্ট্রোক|মুখ\s*বেঁকে)', q_lower):
        norm_terms.append('stroke FAST face arms speech emergency call 999')
    if re.search(r'\b(emergency|999|hospital|duto)\b|(জরুরি|হাসপাতাল)', q_lower):
        norm_terms.append('emergency call 999 go to A&E')
        
    if norm_terms:
        unique_terms = []
        for term in norm_terms:
            if term not in unique_terms:
                unique_terms.append(term)
        return f"{query} ({' '.join(unique_terms)})"
    return query


# CANDIDATE C: Candidate A (Expanded Lexicon) + Candidate B (Contextual Disambiguation)
def normalize_candidate_c(query: str) -> str:
    q_lower = query.lower()
    norm_terms = []
    
    # 1. Contextual Disambiguation: Epistaxis vs Cuts/Grazes
    has_nose = bool(re.search(r'\b(nak|naker|nak\s*die|nak\s*diye|nak\s*theke|nose|nasal|nosebleed|epistaxis)\b|(নাক|নাকের|নাক\s*দিয়ে|নাক\s*থেকে)', q_lower))
    has_bleeding = bool(re.search(r'\b(kete|kata|katse|rokt|rokto|bleeding|bleed|cut|cuts|graze|grazes|antiseptic)\b|(কাটা|রক্ত|রক্তপাত|জীবাণুনাশক)', q_lower))
    
    if has_nose:
        norm_terms.append('nosebleed epistaxis pinch soft part nose lean forward first aid')
    elif has_bleeding:
        norm_terms.append('cuts grazes bleeding pressure clean dressing wound')

    # 2. Contextual Burns: agun, agune, aguner, pura, pure, pora, pore, porle + blister / scald
    has_burn = bool(re.search(r'\b(agun|agune|aguner|pura|pure|pora|pore|porle|burn|burns|scald|scalds|blister)\b|(আগুন|আগুনে|পুড়ে|পোড়া|ফোস্কা)', q_lower))
    if has_burn:
        norm_terms.append('burns scalds cool running water first aid remove clothing')

    # 3. Stroke / FAST
    if re.search(r'\b(stroke|muk\s*beke|haat\s*obos|obosh|paralysis)\b|(স্ট্রোক|প্যারালাইসিস|মুখ\s*বেঁকে)', q_lower):
        norm_terms.append('stroke FAST face arms speech emergency call 999')

    # 4. Asthma
    if re.search(r'\b(shash|shash\s*kosto|shash\s*nite\s*kosto|inhaler|inhalers|asthma)\b|(হাঁপানি|শ্বাসকষ্ট|ইনহেলার)', q_lower):
        norm_terms.append('asthma attack inhaler spacer breathing difficulty')

    # 5. Dehydration
    if re.search(r'\b(pani\s*shunnota|pani\s*kom|shukay|dehydration|dehydrated)\b|(ডিহাইড্রেশন|পানিশূন্যতা)', q_lower):
        norm_terms.append('dehydration fluid rehydration oral fluids')

    # 6. Diarrhoea & Vomiting
    if re.search(r'\b(bomi|patla\s*paykhana|diarrhoea|vomiting)\b|(বমি|ডায়রিয়া|পাতলা\s*পায়খানা)', q_lower):
        norm_terms.append('diarrhoea vomiting oral rehydration fluids')

    # 7. Headache & Painkillers
    if re.search(r'\b(matha\s*betha|matha\s*byatha|matha\s*ghura|headache|painkiller|paracetamol)\b|(মাথাব্যথা|মাথা\s*ঘোরা|প্যারাসিটামল)', q_lower):
        norm_terms.append('headache pain relief painkillers paracetamol')

    # 8. Fever in Children
    if re.search(r'\b(jor|fever|temperature|temp|baccar\s*jor)\b|(বাচ্চার\s*জ্বর|জ্বর)', q_lower):
        norm_terms.append('fever high temperature children fluids paracetamol')

    # 9. Allergic Rhinitis & Allergy
    if re.search(r'\b(chulkani|hachi|sordi|allergy|anaphylaxis|shash\s*bondho)\b|(অ্যালার্জি|অ্যানাফাইলাক্সিস|হাঁচি|সর্দি)', q_lower):
        norm_terms.append('allergic rhinitis allergy sneezing antihistamines anaphylaxis 999')

    # 10. Emergency & Hospital
    if re.search(r'\b(emergency|999|hospital|duto|druto|borti)\b|(জরুরি|হাসপাতাল|ভর্তি)', q_lower):
        norm_terms.append('emergency call 999 go to A&E')

    if norm_terms:
        unique_terms = []
        for term in norm_terms:
            if term not in unique_terms:
                unique_terms.append(term)
        return f"{query} ({' '.join(unique_terms)})"
    return query


# -----------------------------------------------------------------------------
# RETRIEVAL ENGINE (STRATEGY 5 WITH CONFIGURABLE NORMALIZER)
# -----------------------------------------------------------------------------

def compute_token_overlap(q_text: str, chunk_text: str) -> float:
    q_tokens = set(re.findall(r'\w+', q_text.lower()))
    c_tokens = set(re.findall(r'\w+', chunk_text.lower()))
    if not q_tokens or not c_tokens:
        return 0.0
    return len(q_tokens.intersection(c_tokens)) / len(q_tokens)


class RetrievalEngine:
    def __init__(self, corpus_chunks: List[Dict[str, Any]]):
        self.chunks = corpus_chunks
        self.chunk_ids = [c["chunk_id"] for c in corpus_chunks]
        self.chunk_texts = [f"{c['source_title']}: {c['text']}" for c in corpus_chunks]
        self.topical_chunk_indices = [
            idx for idx, c in enumerate(corpus_chunks)
            if c.get("is_topical_anchor", False) or c.get("chunk_id", "").endswith("-HYB-000") or c.get("chunk_id", "").endswith("-HYB-001")
        ]
        
        print("Loading bi-encoder: multilingual-e5-small...")
        self.bi_encoder = SentenceTransformer("intfloat/multilingual-e5-small")
        
        print("Loading cross-encoder: bge-reranker-v2-m3...")
        self.cross_encoder = CrossEncoder("BAAI/bge-reranker-v2-m3")
        
        print(f"Pre-encoding {len(self.chunks)} active passage embeddings...")
        passage_inputs = [f"passage: {t}" for t in self.chunk_texts]
        self.passage_embeddings = self.bi_encoder.encode(
            passage_inputs,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )

    def retrieve(self, raw_query: str, normalizer_func) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Execute Strategy 5 on query using specified normalizer_func.
        Returns: (normalized_query, dense_top15_candidates, final_top5_reranked)
        """
        norm_query = normalizer_func(raw_query)
        q_emb = self.bi_encoder.encode(f"query: {norm_query}", normalize_embeddings=True)
        dense_sims = np.dot(self.passage_embeddings, q_emb)
        
        top15_indices = np.argsort(dense_sims)[::-1][:15]
        
        dense_candidates = []
        for rank, idx in enumerate(top15_indices, start=1):
            dense_candidates.append({
                "rank": rank,
                "chunk_id": self.chunk_ids[idx],
                "parent_source_id": self.chunks[idx]["parent_source_id"],
                "source_title": self.chunks[idx]["source_title"],
                "text": self.chunks[idx]["text"],
                "dense_score": float(dense_sims[idx]),
                "is_topical_anchor": idx in self.topical_chunk_indices
            })
            
        # Cross-encoder reranking
        ce_pairs = [[norm_query, c["text"]] for c in dense_candidates]
        ce_logits = self.cross_encoder.predict(ce_pairs)
        ce_probs = 1.0 / (1.0 + np.exp(-ce_logits))
        
        fused_candidates = []
        for i, c in enumerate(dense_candidates):
            raw_prob = float(ce_probs[i])
            # Overview debiasing penalty (0.85 on -HYB-000 chunks)
            is_overview = c["chunk_id"].endswith("-HYB-000")
            debiased_score = raw_prob * (0.85 if is_overview else 1.0)
            
            # Topical anchor boost (lambda = 0.10)
            topical_boost = 0.10 if c["is_topical_anchor"] else 0.0
            
            # Lexical overlap boost (alpha = 0.03)
            lex_overlap = compute_token_overlap(norm_query, c["text"])
            lex_boost = 0.03 * lex_overlap
            
            final_score = debiased_score + topical_boost + lex_boost
            
            fused_candidates.append({
                "chunk_id": c["chunk_id"],
                "parent_source_id": c["parent_source_id"],
                "source_title": c["source_title"],
                "text": c["text"],
                "rerank_score": final_score,
                "raw_prob": raw_prob,
                "dense_score": c["dense_score"],
                "lexical_overlap": lex_overlap
            })
            
        fused_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        for r, c in enumerate(fused_candidates, start=1):
            c["final_rank"] = r
            
        return norm_query, dense_candidates, fused_candidates[:5]


def evaluate():
    print("=" * 80)
    print("PHASE 6H: BANGLISH RETRIEVAL NORMALIZATION EXPERIMENT")
    print("=" * 80)
    
    # 1. Load active corpus
    corpus_path = settings.ACTIVE_CORPUS_MANIFEST_PATH
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    print(f"Loaded active corpus: {len(corpus)} chunks across {len(set(c['parent_source_id'] for c in corpus))} sources.")
    
    # 2. Load development evaluation cases from Phase 6F
    eval_set_path = os.path.join(
        PROJECT_ROOT, "research", "phase_6F_grounded_generation_evaluation", "outputs", "phase_6F_evaluation_results.json"
    )
    with open(eval_set_path, "r", encoding="utf-8") as f:
        eval_data = json.load(f)
    eval_cases = eval_data["results"]
    print(f"Loaded development eval set: {len(eval_cases)} cases from Phase 6F.")
    
    engine = RetrievalEngine(corpus)
    
    candidates = {
        "CONTROL": normalize_control,
        "CANDIDATE_A": normalize_candidate_a,
        "CANDIDATE_B": normalize_candidate_b,
        "CANDIDATE_C": normalize_candidate_c
    }
    
    results = {}
    
    for cand_name, norm_fn in candidates.items():
        print(f"\nEvaluating {cand_name}...")
        cand_results = []
        
        # Counters
        total_eval_with_target = 0
        dense_hits_15 = 0
        final_hits_5 = 0
        final_hits_3 = 0
        final_hits_1 = 0
        rr_sum = 0.0
        
        # Modality breakdowns
        modalities = {
            "English": {"total": 0, "hits_5": 0, "hits_15": 0, "hits_1": 0},
            "Native Bangla": {"total": 0, "hits_5": 0, "hits_15": 0, "hits_1": 0},
            "Standard Banglish": {"total": 0, "hits_5": 0, "hits_15": 0, "hits_1": 0},
            "Abbreviated Banglish": {"total": 0, "hits_5": 0, "hits_15": 0, "hits_1": 0}
        }
        
        unsupported_count = 0
        
        for case in eval_cases:
            cid = case["case_id"]
            query = case["query_raw"]
            expected_sources = case.get("expected_sources", [])
            lang = case.get("language", "Unknown")
            cat = case.get("category", "")
            
            # Determine if this case is in-corpus supported
            is_supported = (cat != "UNSUPPORTED" and len(expected_sources) > 0 and expected_sources != ["NONE"])
            
            norm_q, top15, top5 = engine.retrieve(query, norm_fn)
            
            top15_sids = [c["parent_source_id"] for c in top15]
            top5_sids = [c["parent_source_id"] for c in top5]
            top3_sids = [c["parent_source_id"] for c in top5[:3]]
            top1_sid = top5[0]["parent_source_id"] if top5 else None
            
            dense_hit = False
            final_hit_5 = False
            final_hit_3 = False
            final_hit_1 = False
            reciprocal_rank = 0.0
            
            if is_supported:
                total_eval_with_target += 1
                
                # Check Dense 15
                dense_hit = any(ts in top15_sids for ts in expected_sources)
                if dense_hit:
                    dense_hits_15 += 1
                    
                # Check Final 5 & MRR
                final_hit_5 = any(ts in top5_sids for ts in expected_sources)
                final_hit_3 = any(ts in top3_sids for ts in expected_sources)
                final_hit_1 = (top1_sid in expected_sources)
                
                if final_hit_1:
                    final_hits_1 += 1
                if final_hit_5:
                    final_hits_5 += 1
                if final_hit_3:
                    final_hits_3 += 1
                    
                for r_idx, c in enumerate(top5, start=1):
                    if c["parent_source_id"] in expected_sources:
                        reciprocal_rank = 1.0 / r_idx
                        break
                rr_sum += reciprocal_rank
                
                # Modality tracking
                if lang in modalities:
                    modalities[lang]["total"] += 1
                    if dense_hit:
                        modalities[lang]["hits_15"] += 1
                    if final_hit_5:
                        modalities[lang]["hits_5"] += 1
                    if final_hit_1:
                        modalities[lang]["hits_1"] += 1
            else:
                unsupported_count += 1
                
            cand_results.append({
                "case_id": cid,
                "query": query,
                "language": lang,
                "category": cat,
                "is_supported": is_supported,
                "normalized_query": norm_q,
                "expected_sources": expected_sources,
                "dense_top15_sources": top15_sids,
                "final_top5_sources": top5_sids,
                "top_retrieved_chunk": top5[0]["chunk_id"] if top5 else None,
                "top_source": top1_sid,
                "top_score": top5[0]["rerank_score"] if top5 else 0.0,
                "dense_hit": dense_hit,
                "final_hit_5": final_hit_5,
                "final_hit_3": final_hit_3,
                "final_hit_1": final_hit_1,
                "reciprocal_rank": reciprocal_rank
            })
            
        recall_15 = (dense_hits_15 / total_eval_with_target * 100.0) if total_eval_with_target else 0.0
        recall_5 = (final_hits_5 / total_eval_with_target * 100.0) if total_eval_with_target else 0.0
        recall_3 = (final_hits_3 / total_eval_with_target * 100.0) if total_eval_with_target else 0.0
        top1_acc = (final_hits_1 / total_eval_with_target * 100.0) if total_eval_with_target else 0.0
        mrr = (rr_sum / total_eval_with_target) if total_eval_with_target else 0.0
        
        results[cand_name] = {
            "total_supported_cases": total_eval_with_target,
            "unsupported_cases": unsupported_count,
            "dense_recall_at_15": round(recall_15, 2),
            "final_source_recall_at_5": round(recall_5, 2),
            "final_source_recall_at_3": round(recall_3, 2),
            "final_top1_accuracy": round(top1_acc, 2),
            "mrr_at_5": round(mrr, 4),
            "modalities": modalities,
            "detailed_cases": cand_results
        }
        
        print(f"  -> Recall@15: {recall_15:.2f}% | Top-5 Recall: {recall_5:.2f}% | Top-3 Recall: {recall_3:.2f}% | Top-1 Acc: {top1_acc:.2f}% | MRR@5: {mrr:.4f}")
        for mod, counts in modalities.items():
            if counts["total"] > 0:
                mod_rec5 = (counts["hits_5"] / counts["total"] * 100.0)
                mod_rec1 = (counts["hits_1"] / counts["total"] * 100.0)
                print(f"     * {mod} (N={counts['total']}): Top-5 Recall = {mod_rec5:.1f}% | Top-1 Acc = {mod_rec1:.1f}%")
                
    # Movement comparison vs CONTROL
    control_cases = {c["case_id"]: c for c in results["CONTROL"]["detailed_cases"]}
    movement_analysis = {}
    
    for cand_name in ["CANDIDATE_A", "CANDIDATE_B", "CANDIDATE_C"]:
        cand_cases = {c["case_id"]: c for c in results[cand_name]["detailed_cases"]}
        helped = []
        harmed = []
        unchanged_success = []
        unchanged_failure = []
        
        for cid, ctrl_c in control_cases.items():
            if not ctrl_c["is_supported"]:
                continue
            cand_c = cand_cases[cid]
            ctrl_hit = ctrl_c["final_hit_5"]
            cand_hit = cand_c["final_hit_5"]
            
            if not ctrl_hit and cand_hit:
                helped.append({
                    "case_id": cid,
                    "query": ctrl_c["query"],
                    "language": ctrl_c["language"],
                    "expected_sources": ctrl_c["expected_sources"],
                    "control_top_source": ctrl_c["top_source"],
                    "candidate_top_source": cand_c["top_source"],
                    "control_score": ctrl_c["top_score"],
                    "candidate_score": cand_c["top_score"]
                })
            elif ctrl_hit and not cand_hit:
                harmed.append({
                    "case_id": cid,
                    "query": ctrl_c["query"],
                    "language": ctrl_c["language"],
                    "expected_sources": ctrl_c["expected_sources"],
                    "control_top_source": ctrl_c["top_source"],
                    "candidate_top_source": cand_c["top_source"]
                })
            elif ctrl_hit and cand_hit:
                unchanged_success.append(cid)
            else:
                unchanged_failure.append(cid)
                
        movement_analysis[cand_name] = {
            "helped_count": len(helped),
            "harmed_count": len(harmed),
            "net_gain": len(helped) - len(harmed),
            "helped_cases": helped,
            "harmed_cases": harmed,
            "unchanged_success_count": len(unchanged_success),
            "unchanged_failure_count": len(unchanged_failure)
        }
        
    out_payload = {
        "phase": "6H",
        "dataset": "development_grounding_eval_set (48 cases from Phase 6F)",
        "active_corpus_chunks": len(corpus),
        "active_conditions": len(set(c["parent_source_id"] for c in corpus)),
        "metrics_summary": {
            k: {
                "dense_recall_at_15": v["dense_recall_at_15"],
                "final_source_recall_at_5": v["final_source_recall_at_5"],
                "final_source_recall_at_3": v["final_source_recall_at_3"],
                "final_top1_accuracy": v["final_top1_accuracy"],
                "mrr_at_5": v["mrr_at_5"]
            }
            for k, v in results.items()
        },
        "modality_breakdown": {
            k: v["modalities"] for k, v in results.items()
        },
        "movement_analysis": movement_analysis,
        "raw_results": results
    }
    
    out_dir = os.path.join(PROJECT_ROOT, "research", "phase_6H_banglish_retrieval_experiment", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "phase_6H_experiment_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2, ensure_ascii=False)
        
    print(f"\nExperiment complete. Saved detailed results to: {out_file}")


if __name__ == "__main__":
    evaluate()
