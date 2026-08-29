export type RetrievalOutcomeState =
  | 'SUPPORTED_RETRIEVAL'
  | 'LOW_CONFIDENCE_RETRIEVAL'
  | 'POSSIBLE_MISMATCH'
  | 'NO_RELEVANT_EVIDENCE'
  | 'UNSUPPORTED_BY_ACTIVE_CORPUS'
  | 'INVALID_QUERY';

export type GenerationSafetyState =
  | 'SAFE_INFORMATIONAL'
  | 'POSSIBLE_EMERGENCY'
  | 'HIGH_RISK_MEDICAL'
  | 'DIAGNOSIS_SEEKING'
  | 'MEDICATION_OR_TREATMENT_REQUEST'
  | 'SELF_HARM_OR_CRISIS'
  | 'UNSUPPORTED_TOPIC'
  | 'SAFETY_REVIEW_REQUIRED';

export type GenerationStatus =
  | 'DISABLED'
  | 'GENERATING'
  | 'COMPLETED'
  | 'REFUSED_SAFETY'
  | 'REFUSED_INSUFFICIENT_EVIDENCE'
  | 'FAILED';

export interface ConfidenceAssessment {
  state: RetrievalOutcomeState;
  confidence_level: 'HIGH' | 'MODERATE' | 'LOW' | 'VERY_LOW' | 'NONE' | 'INVALID';
  top_score: number;
  score_spread: number;
  summary_reason: string;
}

export interface RetrievedEvidenceChunk {
  rank: number;
  chunk_id: string;
  parent_source_id: string;
  source_title: string;
  source_url: string;
  text: string;
  rerank_score: number;
  raw_dense_score?: number;
  lexical_overlap?: number;
  provenance_clause: string;
}

export interface CitationReference {
  citation_index: number;
  chunk_id: string;
  parent_source_id: string;
  source_title: string;
  source_url: string;
  excerpt_snippet: string;
}

export interface PostValidationResult {
  is_valid: boolean;
  citations_valid: boolean;
  fabricated_citations: string[];
  unsupported_claims: string[];
  safety_check_passed: boolean;
  validation_flags: string[];
  summary_notes: string;
}

export interface GenerationResult {
  answer: string;
  citations: CitationReference[];
  evidence_ids: string[];
  confidence_state: RetrievalOutcomeState;
  safety_state: GenerationSafetyState;
  generation_status: GenerationStatus;
  refusal_reason?: string;
  disclaimer: string;
  provider_name: string;
  model_name: string;
  validation_result?: PostValidationResult;
}

export interface RetrievalMetadata {
  strategy_name: string;
  candidate_hash: string;
  active_corpus_name: string;
  active_chunks_count: number;
  dense_k: number;
  final_top_k: number;
}

export interface RetrievalResponse {
  status: string;
  outcome_state: RetrievalOutcomeState;
  confidence_assessment: ConfidenceAssessment;
  strategy_used: string;
  query_raw: string;
  query_normalized: string;
  evidence_count: number;
  evidence: RetrievedEvidenceChunk[];
  retrieval_metadata?: RetrievalMetadata;
}

export interface ChatResponse {
  status: string;
  outcome_state: RetrievalOutcomeState;
  confidence_assessment: ConfidenceAssessment;
  generation_enabled: boolean;
  disclaimer: string;
  user_query: string;
  evidence_count: number;
  evidence: RetrievedEvidenceChunk[];
  synthetic_answer: string;
  retrieval_metadata?: RetrievalMetadata;
  generation_result?: GenerationResult;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  retrieval_strategy: string;
  candidate_hash: string;
  active_corpus_chunks: number;
  staged_research_chunks: number;
  generation_enabled: boolean;
}

export interface CorpusTierInfo {
  name: string;
  status: 'ACTIVE' | 'STAGED_RESEARCH' | 'NOT_ACTIVE' | 'PROMOTED';
  document_count: number;
  chunk_count: number;
  source_ids: string[];
  description: string;
}

export interface CorpusLifecycleResponse {
  status: string;
  active_corpus: CorpusTierInfo;
  staged_research_corpus: CorpusTierInfo;
  validated_corpus: CorpusTierInfo;
  retrieval_candidate: {
    strategy_name: string;
    frozen_candidate_sha256: string;
    dense_model: string;
    reranker_model: string;
    candidate_depth_k: number;
    final_top_k: number;
  };
}

export interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  outcomeState?: RetrievalOutcomeState;
  confidenceAssessment?: ConfidenceAssessment;
  evidence?: RetrievedEvidenceChunk[];
  generationEnabled?: boolean;
  retrievalMetadata?: RetrievalMetadata;
  generationResult?: GenerationResult;
}
