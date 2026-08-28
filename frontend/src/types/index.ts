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
  corpus_chunks_loaded: number;
  generation_enabled: boolean;
}

export interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  evidence?: RetrievedEvidenceChunk[];
  generationEnabled?: boolean;
}
