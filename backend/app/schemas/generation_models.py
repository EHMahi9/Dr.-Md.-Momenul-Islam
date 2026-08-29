"""
Pydantic schemas and contracts for Grounded Generation Architecture (Phase 6D).
Defines prompt contracts, safety routing states, citation objects, provider interfaces,
and post-generation validation schemas.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.api_models import RetrievalOutcomeState, RetrievedEvidenceChunk


class GenerationSafetyState(str, Enum):
    """
    Safety routing classification states.
    Architectural design awaiting formal clinical evaluation.
    """
    SAFE_INFORMATIONAL = "SAFE_INFORMATIONAL"
    POSSIBLE_EMERGENCY = "POSSIBLE_EMERGENCY"
    HIGH_RISK_MEDICAL = "HIGH_RISK_MEDICAL"
    DIAGNOSIS_SEEKING = "DIAGNOSIS_SEEKING"
    MEDICATION_OR_TREATMENT_REQUEST = "MEDICATION_OR_TREATMENT_REQUEST"
    SELF_HARM_OR_CRISIS = "SELF_HARM_OR_CRISIS"
    UNSUPPORTED_TOPIC = "UNSUPPORTED_TOPIC"
    SAFETY_REVIEW_REQUIRED = "SAFETY_REVIEW_REQUIRED"


class GenerationStatus(str, Enum):
    """Lifecycle status of a generation request."""
    DISABLED = "DISABLED"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    REFUSED_SAFETY = "REFUSED_SAFETY"
    REFUSED_INSUFFICIENT_EVIDENCE = "REFUSED_INSUFFICIENT_EVIDENCE"
    FAILED = "FAILED"


class CitationReference(BaseModel):
    """
    Represents a verifiable link between a generated statement and retrieved evidence.
    Ensures answer claims map directly: claim -> evidence chunk -> parent source -> NHS URL.
    """
    citation_index: int = Field(..., description="1-based index appearing in the text, e.g. [1]")
    chunk_id: str = Field(..., description="Unique ID of the cited chunk (e.g., DOC-NHS-005-HYB-001)")
    parent_source_id: str = Field(..., description="Canonical source ID (e.g., DOC-NHS-005)")
    source_title: str = Field(..., description="Title of the source document")
    source_url: str = Field(..., description="Authoritative NHS URL")
    excerpt_snippet: str = Field(..., max_length=200, description="Brief exact quote from the chunk supporting the claim")


class GroundingEvidence(BaseModel):
    """
    Normalized, tamper-evident evidence format passed into the grounded prompt builder.
    """
    chunk_id: str
    parent_source_id: str
    source_title: str
    source_url: str
    excerpt: str
    retrieval_rank: int
    fused_score: float
    raw_dense_score: Optional[float] = None
    lexical_overlap: Optional[float] = None
    provenance_clause: str = "Contains information from NHS England, licensed under Open Government Licence v3.0."

    @classmethod
    def from_retrieved_chunk(cls, chunk: RetrievedEvidenceChunk) -> "GroundingEvidence":
        return cls(
            chunk_id=chunk.chunk_id,
            parent_source_id=chunk.parent_source_id,
            source_title=chunk.source_title,
            source_url=chunk.source_url,
            excerpt=chunk.text,
            retrieval_rank=chunk.rank,
            fused_score=chunk.rerank_score,
            raw_dense_score=chunk.raw_dense_score,
            lexical_overlap=chunk.lexical_overlap,
            provenance_clause=chunk.provenance_clause
        )


class GroundedPrompt(BaseModel):
    """
    Structured prompt contract separating user query, evidence, source metadata,
    system instructions, and safety guardrails.
    """
    user_question: str = Field(..., description="Normalized or raw user inquiry")
    retrieved_evidence: List[GroundingEvidence] = Field(default_factory=list, description="Top-k retrieved evidence passages")
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata regarding active corpus and licensing")
    system_instructions: str = Field(..., description="Foundational system persona and constraints")
    safety_instructions: str = Field(..., description="Explicit medical safety constraints and emergency handling")
    formatted_prompt_payload: Optional[str] = Field(None, description="Fully composed prompt ready for LLM input")


class TokenUsageMetadata(BaseModel):
    """Standardized token accounting metadata across providers."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMRequest(BaseModel):
    """Provider-agnostic request container."""
    prompt: GroundedPrompt
    model_name: str
    max_tokens: int = 1024
    temperature: float = 0.2
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Provider-agnostic response container."""
    raw_text: str = ""
    finish_reason: Optional[str] = None
    token_usage: Optional[TokenUsageMetadata] = None
    latency_ms: Optional[float] = None
    provider_name: str = "disabled"
    model_name: str = ""
    error: Optional[str] = None


class PostValidationResult(BaseModel):
    """
    Results of deterministic post-generation validation checks.
    """
    is_valid: bool = True
    citations_valid: bool = True
    fabricated_citations: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    safety_check_passed: bool = True
    validation_flags: List[str] = Field(default_factory=list)
    summary_notes: str = ""


class GenerationResult(BaseModel):
    """
    Structured grounded generation output schema.
    Does NOT expose internal raw chain-of-thought.
    """
    answer: str = Field(..., description="Grounded response text with inline citation tags like [1]")
    citations: List[CitationReference] = Field(default_factory=list, description="Verified citations mapped to retrieved chunks")
    evidence_ids: List[str] = Field(default_factory=list, description="List of chunk IDs referenced")
    confidence_state: RetrievalOutcomeState = Field(..., description="Retrieval outcome state inherited from evidence ranking")
    safety_state: GenerationSafetyState = Field(..., description="Safety assessment classification")
    generation_status: GenerationStatus = Field(..., description="Execution status")
    refusal_reason: Optional[str] = Field(None, description="Reason if generation was refused or constrained")
    disclaimer: str = Field(
        default="Research Prototype — Not for Medical Decision-Making or Emergency Triage.",
        description="Mandatory clinical guidance disclaimer"
    )
    provider_name: str = "none"
    model_name: str = "none"
    token_usage: Optional[TokenUsageMetadata] = None
    validation_result: Optional[PostValidationResult] = None
