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
    active_candidate: str = "Candidate B (Context-Aware Compound Disambiguation)"
    candidate_hash: str
    candidate_b_hash: Optional[str] = None
    parent_strategy_hash: Optional[str] = None
    active_corpus_name: str
    active_chunks_count: int
    dense_k: int
    final_top_k: int

class QueryIntentCategory(str, Enum):
    CLEARLY_ANSWERABLE = "CLEARLY_ANSWERABLE"
    UNDERSPECIFIED_AMBIGUOUS = "UNDERSPECIFIED_AMBIGUOUS"
    UNSUPPORTED_ACTIVE_CORPUS = "UNSUPPORTED_ACTIVE_CORPUS"
    POTENTIALLY_EMERGENCY = "POTENTIALLY_EMERGENCY"

class EvidenceSufficiencyState(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    UNSUPPORTED = "UNSUPPORTED"
    EMERGENCY = "EMERGENCY"

class ConversationAction(str, Enum):
    ANSWER = "ANSWER"
    CLARIFY = "CLARIFY"
    ABSTAIN = "ABSTAIN"
    EMERGENCY = "EMERGENCY"

class ClarificationState(str, Enum):
    NOT_NEEDED = "NOT_NEEDED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    MAX_TURNS_EXCEEDED = "MAX_TURNS_EXCEEDED"
    UNSUPPORTED_TOPIC = "UNSUPPORTED_TOPIC"

class ConversationContextState(BaseModel):
    session_id: str = "default-session"
    turn_count: int = 0
    clarification_turn_count: int = 0
    max_clarification_turns: int = 3
    language_modality: str = "en"  # "en", "bn", "banglish"
    response_language_preference: str = "auto"  # "auto", "bn", "en"
    symptom: Optional[str] = None
    body_location: Optional[str] = None
    specific_location: Optional[str] = None
    onset: Optional[str] = None
    duration: Optional[str] = None
    severity_stated: Optional[str] = None  # strictly only if user explicitly stated
    associated_symptoms: List[str] = Field(default_factory=list)
    precipitating_event: Optional[str] = None  # e.g., "sprain/trauma", "burn", "cut", "insect_bite"
    user_age_group: Optional[str] = None  # strictly only if explicitly provided (e.g., "child", "adult")
    red_flags: List[str] = Field(default_factory=list)
    relevant_negatives: List[str] = Field(default_factory=list)  # e.g., "no trauma reported", "no bleeding"
    clarification_state: ClarificationState = ClarificationState.NOT_NEEDED
    unanswered_fields: List[str] = Field(default_factory=list)
    next_action: ConversationAction = ConversationAction.ANSWER
    refined_retrieval_query: Optional[str] = None
    conversation_summary: Optional[str] = None

class ClarificationQuestion(BaseModel):
    field_to_clarify: str
    question_text_en: str
    question_text_bn: str
    options: List[str] = Field(default_factory=list)

class EmergencyAdvice(BaseModel):
    is_emergency: bool = True
    alert_title_en: str
    alert_title_bn: str
    action_advice_en: str
    action_advice_bn: str
    emergency_contact: str = "999 (UK) / 999 (BD) / Local Emergency Services"

class QueryUnderstandingResult(BaseModel):
    query_raw: str
    detected_language: str  # "en", "bn", "banglish"
    resolved_response_language: str  # "en", "bn"
    intent_category: QueryIntentCategory
    sufficiency_state: EvidenceSufficiencyState
    extracted_symptoms: List[str] = Field(default_factory=list)
    extracted_body_location: Optional[str] = None
    extracted_duration: Optional[str] = None
    red_flags_detected: List[str] = Field(default_factory=list)
    is_emergency: bool = False
    emergency_advice: Optional[EmergencyAdvice] = None
    clarification_question: Optional[ClarificationQuestion] = None
    evidence_presentation_policy: str  # "SHOW_GROUNDING_CARDS", "SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION", "SHOW_EMERGENCY_OVERRIDE"
    explanation: str

class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User question in English, Bangla, or Banglish")
    top_k: Optional[int] = Field(5, ge=1, le=15, description="Number of evidence chunks to retrieve")
    preferred_language: Optional[str] = Field("auto", description="Preferred response language: 'auto', 'bn', 'en'")

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
    query_understanding: Optional[QueryUnderstandingResult] = None
    evidence_presentation_policy: str = "SHOW_GROUNDING_CARDS"

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, description="Optional session/conversation ID")
    conversation_history: Optional[List[ChatMessage]] = Field(default_factory=list)
    context_state: Optional[ConversationContextState] = Field(None, description="Current structured conversation context state")
    preferred_language: Optional[str] = Field("auto", description="Preferred response language: 'auto', 'bn', 'en'")

class ChatResponse(BaseModel):
    status: str = "research_prototype"
    outcome_state: RetrievalOutcomeState
    confidence_assessment: ConfidenceAssessment
    generation_enabled: bool = False
    disclaimer: str = "Research Prototype — Not for Medical Decision-Making. LLM generation is currently disabled."
    session_id: Optional[str] = "default-session"
    user_query: str
    preferred_language: str = "auto"
    response_language: Optional[str] = "en"
    next_action: ConversationAction = ConversationAction.ANSWER
    clarification_state: ClarificationState = ClarificationState.NOT_NEEDED
    context_state: Optional[ConversationContextState] = None
    evidence_count: int
    evidence: List[RetrievedEvidenceChunk]
    synthetic_answer: str = (
        "[RESEARCH PROTOTYPE MODE: LLM generation is currently disabled by protocol. "
        "The authoritative NHS evidence passages retrieved below represent the grounding context for this query.]"
    )
    retrieval_metadata: Optional[RetrievalMetadata] = None
    generation_result: Optional[Any] = None
    query_understanding: Optional[QueryUnderstandingResult] = None
    evidence_presentation_policy: str = "SHOW_GROUNDING_CARDS"

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
    active_candidate: str = "Candidate B (Context-Aware Compound Disambiguation)"
    candidate_hash: str
    candidate_b_hash: Optional[str] = None
    parent_strategy_hash: Optional[str] = None
    active_corpus_chunks: int
    staged_research_chunks: int
    generation_enabled: bool
