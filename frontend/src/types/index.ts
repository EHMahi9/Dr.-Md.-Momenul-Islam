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

export interface ChatResponse {
  status: string;
  generation_enabled: boolean;
  disclaimer: string;
  user_query: string;
  evidence_count: number;
  evidence: RetrievedEvidenceChunk[];
  synthetic_answer: string;
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
  status: 'ACTIVE' | 'STAGED_RESEARCH' | 'NOT_ACTIVE';
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
  evidence?: RetrievedEvidenceChunk[];
  generationEnabled?: boolean;
}

