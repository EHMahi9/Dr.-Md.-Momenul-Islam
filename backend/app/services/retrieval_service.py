"""
Abstract Retrieval Service and Concrete Strategy 5 Implementation.
This service encapsulates the frozen experimental retrieval candidate.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import json
import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

from app.core.config import settings
from app.schemas.api_models import RetrievedEvidenceChunk

# Track A Unicode-Safe Procedural Normalization (Frozen Candidate)
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

def normalize_query_track_a(query: str) -> str:
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

def compute_token_overlap(q_text: str, chunk_text: str) -> float:
    q_tokens = set(re.findall(r'\w+', q_text.lower()))
    c_tokens = set(re.findall(r'\w+', chunk_text.lower()))
    if not q_tokens or not c_tokens:
        return 0.0
    return len(q_tokens.intersection(c_tokens)) / len(q_tokens)

class BaseRetrievalService(ABC):
    """Abstract interface defining the retrieval boundary."""
    
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> Tuple[str, List[RetrievedEvidenceChunk]]:
        """Retrieve top_k evidence passages for a query."""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return identifier of active strategy."""
        pass
    
    @abstractmethod
    def get_chunk_count(self) -> int:
        """Return total chunks indexed."""
        pass

class FrozenDualAnchorRetrievalService(BaseRetrievalService):
    """
    Production prototype wrapper around Strategy 5:
    Track A Normalization -> E5 Small -> Top-15 -> BGE Reranker -> 0.85x Overview Debiasing -> Dual Anchor Fusion.
    """
    
    def __init__(self):
        print(f"[RetrievalService] Initializing {settings.RETRIEVAL_STRATEGY}...")
        
        # 1. Load Corpus
        if not os.path.exists(settings.CORPUS_MANIFEST_PATH):
            raise FileNotFoundError(f"Corpus manifest missing at: {settings.CORPUS_MANIFEST_PATH}")
            
        with open(settings.CORPUS_MANIFEST_PATH, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
            
        self.chunks_by_id = {c["chunk_id"]: c for c in self.chunks}
        print(f"[RetrievalService] Loaded {len(self.chunks)} corpus chunks across 8 NHS documents.")
        
        # 2. Load Neural Models on CPU
        print(f"[RetrievalService] Loading dense model: {settings.DENSE_MODEL_NAME}...")
        self.dense_model = SentenceTransformer(settings.DENSE_MODEL_NAME, device="cpu")
        
        print(f"[RetrievalService] Loading cross-encoder: {settings.RERANKER_MODEL_NAME}...")
        self.reranker = CrossEncoder(settings.RERANKER_MODEL_NAME, device="cpu")
        
        # 3. Pre-encode Passages
        print("[RetrievalService] Pre-encoding corpus passages...")
        passage_texts = [f"passage: {c['text']}" for c in self.chunks]
        self.chunk_embeddings = self.dense_model.encode(passage_texts, normalize_embeddings=True)
        print("[RetrievalService] Corpus embedding index ready.")
        
    def get_strategy_name(self) -> str:
        return settings.RETRIEVAL_STRATEGY
        
    def get_chunk_count(self) -> int:
        return len(self.chunks)
        
    def retrieve(self, query: str, top_k: int = 5) -> Tuple[str, List[RetrievedEvidenceChunk]]:
        # Step 1: Normalization
        norm_query = normalize_query_track_a(query)
        
        # Step 2: Dense Retrieval (Top-15)
        q_emb = self.dense_model.encode([f"query: {norm_query}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, self.chunk_embeddings.T)[0]
        top_k_indices = np.argsort(-dense_scores)[:settings.DENSE_K]
        candidate_cids = [self.chunks[idx]["chunk_id"] for idx in top_k_indices]
        candidate_dense_scores = [float(dense_scores[idx]) for idx in top_k_indices]
        
        # Step 3: Cross-Encoder Reranking
        pairs = [[query, self.chunks_by_id[cid]["text"]] for cid in candidate_cids]
        raw_rerank_scores = self.reranker.predict(pairs)
        
        # Step 4: Overview Debiasing (0.85x) & Dual Anchor Fusion
        adjusted_scores = []
        token_overlaps = []
        
        for cid, r_score, d_score in zip(candidate_cids, raw_rerank_scores, candidate_dense_scores):
            score = float(r_score)
            if cid.endswith("-HYB-000"):
                score *= settings.OVERVIEW_DEBIAS_MULTIPLIER
                
            overlap = compute_token_overlap(query, self.chunks_by_id[cid]["text"])
            token_overlaps.append(overlap)
            
            # Dual Anchor Blend: score + lambda * dense + alpha * lexical
            final_score = score + (settings.LAMBDA_DENSE_FUSION * d_score) + (settings.ALPHA_LEXICAL_OVERLAP * overlap)
            adjusted_scores.append(final_score)
            
        # Step 5: Final Selection & Ordering
        ranked_order = np.argsort(-np.array(adjusted_scores))
        final_top_indices = ranked_order[:top_k]
        
        evidence_list: List[RetrievedEvidenceChunk] = []
        for rank_idx, i in enumerate(final_top_indices, start=1):
            cid = candidate_cids[i]
            c_info = self.chunks_by_id[cid]
            
            raw_title = c_info.get("source_title", "NHS Source")
            clean_title = raw_title.replace("\n", " ").replace(" - NHS", "").strip()
            
            evidence_list.append(RetrievedEvidenceChunk(
                rank=rank_idx,
                chunk_id=cid,
                parent_source_id=c_info["parent_source_id"],
                source_title=clean_title,
                source_url=c_info["requested_url"],
                text=c_info["text"],
                rerank_score=round(float(adjusted_scores[i]), 4),
                raw_dense_score=round(float(candidate_dense_scores[i]), 4),
                lexical_overlap=round(float(token_overlaps[i]), 4)
            ))
            
        return norm_query, evidence_list

# Singleton instance
_retrieval_service_instance: Optional[BaseRetrievalService] = None

def get_retrieval_service() -> BaseRetrievalService:
    global _retrieval_service_instance
    if _retrieval_service_instance is None:
        _retrieval_service_instance = FrozenDualAnchorRetrievalService()
    return _retrieval_service_instance
