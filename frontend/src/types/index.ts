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

export type QueryIntentCategory =
  | 'CLEARLY_ANSWERABLE'
  | 'UNDERSPECIFIED_AMBIGUOUS'
  | 'UNSUPPORTED_ACTIVE_CORPUS'
  | 'POTENTIALLY_EMERGENCY';

export type EvidenceSufficiencyState =
  | 'SUFFICIENT'
  | 'INSUFFICIENT'
  | 'UNSUPPORTED'
  | 'EMERGENCY';

export type EvidencePresentationPolicy =
  | 'SHOW_GROUNDING_CARDS'
  | 'SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION'
  | 'SHOW_EMERGENCY_OVERRIDE';

export interface ClarificationQuestion {
  field_to_clarify: string;
  question_text_en: string;
  question_text_bn: string;
  options: string[];
  utility_score?: number;
  selection_rationale?: string;
}

export interface EmergencyAdvice {
  is_emergency: boolean;
  alert_title_en: string;
  alert_title_bn: string;
  action_advice_en: string;
  action_advice_bn: string;
  emergency_contact: string;
}

export interface QueryUnderstandingResult {
  query_raw: string;
  detected_language: 'en' | 'bn' | 'banglish';
  resolved_response_language: 'en' | 'bn';
  intent_category: QueryIntentCategory;
  sufficiency_state: EvidenceSufficiencyState;
  extracted_symptoms: string[];
  extracted_body_location?: string;
  extracted_duration?: string;
  red_flags_detected: string[];
  is_emergency: boolean;
  emergency_advice?: EmergencyAdvice;
  clarification_question?: ClarificationQuestion;
  evidence_presentation_policy: EvidencePresentationPolicy;
  explanation: string;
}

export interface RetrievalMetadata {
  strategy_name: string;
  active_candidate?: string;
  candidate_hash: string;
  candidate_b_hash?: string;
  parent_strategy_hash?: string;
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
  query_understanding?: QueryUnderstandingResult;
  evidence_presentation_policy?: EvidencePresentationPolicy;
}

export type ConversationAction = 'ANSWER' | 'CLARIFY' | 'ABSTAIN' | 'EMERGENCY';

export type ClarificationState =
  | 'NOT_NEEDED'
  | 'IN_PROGRESS'
  | 'RESOLVED'
  | 'MAX_TURNS_EXCEEDED'
  | 'UNSUPPORTED_TOPIC';

export interface ConversationContextState {
  session_id: string;
  turn_count: number;
  clarification_turn_count: number;
  max_clarification_turns: number;
  language_modality: 'en' | 'bn' | 'banglish';
  response_language_preference: string;
  symptom?: string;
  body_location?: string;
  specific_location?: string;
  onset?: string;
  duration?: string;
  severity_stated?: string;
  associated_symptoms: string[];
  precipitating_event?: string;
  user_age_group?: string;
  red_flags: string[];
  relevant_negatives: string[];
  asked_questions: string[];
  missing_high_value_fields: string[];
  candidate_question_scores?: Record<string, number>;
  stopping_reason?: string;
  clarification_state: ClarificationState;
  unanswered_fields: string[];
  next_action: ConversationAction;
  refined_retrieval_query?: string;
  conversation_summary?: string;
}

export interface ChatResponse {
  status: string;
  outcome_state: RetrievalOutcomeState;
  confidence_assessment: ConfidenceAssessment;
  generation_enabled: boolean;
  disclaimer: string;
  session_id?: string;
  user_query: string;
  preferred_language?: string;
  response_language?: string;
  next_action?: ConversationAction;
  clarification_state?: ClarificationState;
  context_state?: ConversationContextState;
  evidence_count: number;
  evidence: RetrievedEvidenceChunk[];
  synthetic_answer: string;
  retrieval_metadata?: RetrievalMetadata;
  generation_result?: GenerationResult;
  query_understanding?: QueryUnderstandingResult;
  evidence_presentation_policy?: EvidencePresentationPolicy;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  retrieval_strategy: string;
  active_candidate?: string;
  candidate_hash: string;
  candidate_b_hash?: string;
  parent_strategy_hash?: string;
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
    active_candidate?: string;
    candidate_b_freeze_sha256?: string;
    parent_strategy_sha256?: string;
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
  nextAction?: ConversationAction;
  clarificationState?: ClarificationState;
  contextState?: ConversationContextState;
  evidence?: RetrievedEvidenceChunk[];
  generationEnabled?: boolean;
  retrievalMetadata?: RetrievalMetadata;
  generationResult?: GenerationResult;
  queryUnderstanding?: QueryUnderstandingResult;
  evidencePresentationPolicy?: EvidencePresentationPolicy;
}
