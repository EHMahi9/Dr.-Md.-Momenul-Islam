"""
Pydantic API request and response schemas.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

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

class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User question in English, Bangla, or Banglish")
    top_k: Optional[int] = Field(5, ge=1, le=15, description="Number of evidence chunks to retrieve")

class RetrievalResponse(BaseModel):
    status: str = "success"
    strategy_used: str
    query_raw: str
    query_normalized: str
    evidence_count: int
    evidence: List[RetrievedEvidenceChunk]

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_history: Optional[List[ChatMessage]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    status: str = "research_prototype"
    generation_enabled: bool = False
    disclaimer: str = "Research Prototype — Not for Medical Decision-Making. LLM generation is currently disabled."
    user_query: str
    evidence_count: int
    evidence: List[RetrievedEvidenceChunk]
    synthetic_answer: str = (
        "[RESEARCH PROTOTYPE MODE: LLM generation is currently disabled by protocol. "
        "The authoritative NHS evidence passages retrieved below represent the grounding context for this query.]"
    )

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
    retrieval_candidate: dict

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
