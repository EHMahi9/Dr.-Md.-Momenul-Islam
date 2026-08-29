"""
Pydantic API request and response schemas with structured retrieval outcome states.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RetrievalOutcomeState(str, Enum):
    SUPPORTED_RETRIEVAL = "SUPPORTED_RETRIEVAL"
    LOW_CONFIDENCE_RETRIEVAL = "LOW_CONFIDENCE_RETRIEVAL"
    POSSIBLE_MISMATCH = "POSSIBLE_MISMATCH"
    NO_RELEVANT_EVIDENCE = "NO_RELEVANT_EVIDENCE"
    UNSUPPORTED_BY_ACTIVE_CORPUS = "UNSUPPORTED_BY_ACTIVE_CORPUS"
    INVALID_QUERY = "INVALID_QUERY"

class ConfidenceAssessment(BaseModel):
    state: RetrievalOutcomeState
    confidence_level: str  # "HIGH", "MODERATE", "LOW", "VERY_LOW", "NONE", "INVALID"
    top_score: float
    score_spread: float
    summary_reason: str

class RetrievedEvidenceChunk(BaseModel):
    rank: int
    chunk_id: str
    parent_source_id: str
    source_title: str
    source_url: str
    text: str
    rerank_score: float
    raw_dense_score: Optional[float] = None
    lexical_overlap: Optional[float] = None
    provenance_clause: str = "Contains information from NHS England, licensed under Open Government Licence v3.0."

class RetrievalMetadata(BaseModel):
    strategy_name: str
    candidate_hash: str
    active_corpus_name: str
    active_chunks_count: int
    dense_k: int
    final_top_k: int

class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User question in English, Bangla, or Banglish")
    top_k: Optional[int] = Field(5, ge=1, le=15, description="Number of evidence chunks to retrieve")

class RetrievalResponse(BaseModel):
    status: str = "success"
    outcome_state: RetrievalOutcomeState
    confidence_assessment: ConfidenceAssessment
    strategy_used: str
    query_raw: str
    query_normalized: str
    evidence_count: int
    evidence: List[RetrievedEvidenceChunk]
    retrieval_metadata: Optional[RetrievalMetadata] = None

from app.schemas.generation_models import (
    GenerationSafetyState,
    GenerationStatus,
    CitationReference,
    GroundingEvidence,
    GenerationResult
)

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_history: Optional[List[ChatMessage]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    status: str = "research_prototype"
    outcome_state: RetrievalOutcomeState
    confidence_assessment: ConfidenceAssessment
    generation_enabled: bool = False
    disclaimer: str = "Research Prototype — Not for Medical Decision-Making. LLM generation is currently disabled."
    user_query: str
    evidence_count: int
    evidence: List[RetrievedEvidenceChunk]
    synthetic_answer: str = (
        "[RESEARCH PROTOTYPE MODE: LLM generation is currently disabled by protocol. "
        "The authoritative NHS evidence passages retrieved below represent the grounding context for this query.]"
    )
    retrieval_metadata: Optional[RetrievalMetadata] = None
    generation_result: Optional[GenerationResult] = None

class CorpusTierInfo(BaseModel):
    name: str
    status: str  # "ACTIVE", "STAGED_RESEARCH", "NOT_ACTIVE"
    document_count: int
    chunk_count: int
    source_ids: List[str]
    description: str

class CorpusLifecycleResponse(BaseModel):
    status: str = "success"
    active_corpus: CorpusTierInfo
    staged_research_corpus: CorpusTierInfo
    validated_corpus: CorpusTierInfo
    retrieval_candidate: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str = "healthy"
    app_name: str
    version: str
    environment: str
    retrieval_strategy: str
    candidate_hash: str
    active_corpus_chunks: int
    staged_research_chunks: int
    generation_enabled: bool
