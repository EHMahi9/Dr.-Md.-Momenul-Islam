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

def normalize_candidate_b(query: str) -> str:
    """
    Candidate B: Context-Aware Compound Disambiguation (Frozen & Promoted in Phase 7A).
    Detects multi-token compound patterns with anatomical site grounding to strictly route
    queries and avoid cross-condition contamination.
    Freeze SHA-256: 92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A
    """
    q = normalize_query_track_a(query)
    lower_q = q.lower()
    
    # Compound Rules with Contextual Isolation
    # 1. Nosebleed compound: 'nak' + bleeding (RULE_B1)
    if re.search(r'\b(nak|nose)\b', lower_q) and re.search(r'\b(rokt|rokto|bleeding|porche|pora)\b', lower_q):
        lower_q += " nosebleed epistaxis pinch soft part of nose lean forward bleed from nose"
        
    # 2. Cut / Wound compound: trauma ('kete'/'chole'/'ghotona') + bleeding (RULE_B2)
    elif re.search(r'\b(kete|chole|keteche|injury|khoto|wound)\b', lower_q) and re.search(r'\b(rokt|rokto|bleeding|blood)\b', lower_q):
        lower_q += " cuts and grazes cut wound bleeding pressure clean dressing bandage stop bleeding"
        
    # 3. Heartburn compound: 'buk' + burning/pain (RULE_B3)
    if re.search(r'\b(buk|chest)\b', lower_q) and re.search(r'\b(jala|pora|betha|burning|pain)\b', lower_q):
        lower_q += " heartburn acid reflux indigestion chest burning sensation antacids stomach acid"
        
    # 4. Thermal Burns compound: thermal agent ('agune'/'gorom pani'/'tel'/'chaye') + 'pora'/'pure' (RULE_B4)
    elif re.search(r'\b(agune|gorom pani|tel|chayer pani|hot water|fire|steam)\b', lower_q) and re.search(r'\b(pora|pure|burn|scald)\b', lower_q):
        lower_q += " burns and scalds cool tap water 20 minutes remove jewellery cling film thermal burn"
        
    # 5. Pediatric fever: 'baccha'/'shishu' + 'jor'/'fever' (RULE_B5)
    if re.search(r'\b(baccha|bacchar|shishu|baby|child|children)\b', lower_q) and re.search(r'\b(jor|fever|tapmatra|temperature)\b', lower_q):
        lower_q += " high temperature fever in children paracetamol plenty of fluids signs of serious illness"
        
    # 6. Insect bites: 'pokar kamor' (RULE_B6)
    if re.search(r'\b(poka|pokar|insect|wasp|bee)\b', lower_q) and re.search(r'\b(kamor|khel|sting|bite|fule)\b', lower_q):
        lower_q += " insect bites and stings redness swelling itching remove sting cold compress"
        
    # 7. Migraine: 'mathar ekpashe' + betha (RULE_B7)
    if re.search(r'\b(matha|head)\b', lower_q) and re.search(r'\b(ekpashe|unilateral|one side|throbbing)\b', lower_q):
        lower_q += " migraine severe throbbing headache dark quiet room nausea visual disturbance"
        
    return lower_q.strip()

def compute_token_overlap(q_text: str, chunk_text: str) -> float:
    q_tokens = set(re.findall(r'\w+', q_text.lower()))
    c_tokens = set(re.findall(r'\w+', chunk_text.lower()))
    if not q_tokens or not c_tokens:
        return 0.0
    return len(q_tokens.intersection(c_tokens)) / len(q_tokens)

from app.schemas.api_models import (
    RetrievedEvidenceChunk,
    RetrievalOutcomeState,
    ConfidenceAssessment
)

def classify_retrieval_outcome(query: str, evidence: List[RetrievedEvidenceChunk]) -> Tuple[RetrievalOutcomeState, ConfidenceAssessment]:
    """
    Deterministic retrieval outcome classification based on ranking evidence and fused scores.
    """
    if not query or not query.strip():
        return RetrievalOutcomeState.INVALID_QUERY, ConfidenceAssessment(
            state=RetrievalOutcomeState.INVALID_QUERY,
            confidence_level="INVALID",
            top_score=0.0,
            score_spread=0.0,
            summary_reason="Query input is empty or contains only whitespace."
        )
    if len(query) > 1000:
        return RetrievalOutcomeState.INVALID_QUERY, ConfidenceAssessment(
            state=RetrievalOutcomeState.INVALID_QUERY,
            confidence_level="INVALID",
            top_score=0.0,
            score_spread=0.0,
            summary_reason="Query length exceeds maximum limit of 1000 characters."
        )
    if not evidence:
        return RetrievalOutcomeState.NO_RELEVANT_EVIDENCE, ConfidenceAssessment(
            state=RetrievalOutcomeState.NO_RELEVANT_EVIDENCE,
            confidence_level="NONE",
            top_score=0.0,
            score_spread=0.0,
            summary_reason="No evidence passages returned from active knowledge base."
        )

    top_score = evidence[0].rerank_score
    lowest_score = evidence[-1].rerank_score if len(evidence) > 1 else top_score
    spread = top_score - lowest_score

    # Clinical retrieval confidence tiers based on Strategy 5 fused score
    if top_score >= 0.65:
        state = RetrievalOutcomeState.SUPPORTED_RETRIEVAL
        conf = "HIGH"
        reason = "Authoritative clinical evidence with strong semantic alignment retrieved from active NHS corpus."
    elif top_score >= 0.35:
        state = RetrievalOutcomeState.LOW_CONFIDENCE_RETRIEVAL
        conf = "MODERATE"
        reason = "Supporting evidence retrieved with moderate confidence. Review context carefully."
    elif top_score >= 0.18:
        state = RetrievalOutcomeState.POSSIBLE_MISMATCH
        conf = "LOW"
        reason = "Retrieved evidence has weak semantic alignment and may relate to general triage or a different condition."
    elif top_score >= 0.10:
        state = RetrievalOutcomeState.UNSUPPORTED_BY_ACTIVE_CORPUS
        conf = "VERY_LOW"
        reason = "This clinical question appears outside the 14 conditions covered in the active knowledge base."
    else:
        state = RetrievalOutcomeState.NO_RELEVANT_EVIDENCE
        conf = "NONE"
        reason = "No relevant clinical evidence found in the active knowledge base for this query."

    return state, ConfidenceAssessment(
        state=state,
        confidence_level=conf,
        top_score=round(top_score, 4),
        score_spread=round(spread, 4),
        summary_reason=reason
    )

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
    def get_candidate_name(self) -> str:
        """Return identifier of active retrieval candidate."""
        pass

    @abstractmethod
    def get_candidate_hash(self) -> str:
        """Return frozen cryptographic hash of active candidate."""
        pass
    
    @abstractmethod
    def get_chunk_count(self) -> int:
        """Return total chunks indexed."""
        pass

class FrozenDualAnchorRetrievalService(BaseRetrievalService):
    """
    Production prototype wrapper around Strategy 5 with Promoted Candidate B:
    Candidate B Context-Aware Disambiguation -> E5 Small -> Top-15 -> BGE Reranker -> 0.85x Overview Debiasing -> Dual Anchor Fusion.
    Candidate B Freeze SHA-256: 92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A
    Parent Strategy 5 SHA-256: 1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae
    """
    
    def __init__(self):
        print(f"[RetrievalService] Initializing {settings.RETRIEVAL_STRATEGY} with active candidate: {settings.ACTIVE_RETRIEVAL_CANDIDATE}...")
        
        # 1. Load Corpus
        if not os.path.exists(settings.CORPUS_MANIFEST_PATH):
            raise FileNotFoundError(f"Corpus manifest missing at: {settings.CORPUS_MANIFEST_PATH}")
            
        with open(settings.CORPUS_MANIFEST_PATH, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
            
        self.chunks_by_id = {c["chunk_id"]: c for c in self.chunks}
        source_count = len(set(c["parent_source_id"] for c in self.chunks))
        print(f"[RetrievalService] Loaded {len(self.chunks)} corpus chunks across {source_count} NHS documents.")
        
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

    def get_candidate_name(self) -> str:
        return settings.ACTIVE_RETRIEVAL_CANDIDATE

    def get_candidate_hash(self) -> str:
        return settings.CANDIDATE_B_FREEZE_SHA256
        
    def get_chunk_count(self) -> int:
        return len(self.chunks)
        
    def retrieve(self, query: str, top_k: int = 5) -> Tuple[str, List[RetrievedEvidenceChunk]]:
        # Step 1: Normalization (Promoted Candidate B)
        norm_query = normalize_candidate_b(query)
        
        # Step 2: Dense Retrieval (Top-15)
        q_emb = self.dense_model.encode([f"query: {norm_query}"], normalize_embeddings=True)
        dense_scores = np.dot(q_emb, self.chunk_embeddings.T)[0]
        top_k_indices = np.argsort(-dense_scores)[:settings.DENSE_K]
        candidate_cids = [self.chunks[idx]["chunk_id"] for idx in top_k_indices]
        candidate_dense_scores = [float(dense_scores[idx]) for idx in top_k_indices]
        
        # Step 3: Cross-Encoder Reranking (Optimized non-semantic sub-batching to eliminate padding overhead)
        pairs = [[query, self.chunks_by_id[cid]["text"]] for cid in candidate_cids]
        raw_rerank_scores = self.reranker.predict(pairs, batch_size=8, max_length=512)
        
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
