"""
Application configuration for Dr. Md. Momenul Islam Backend.
"""

import os
from pydantic import BaseModel

from typing import List

def _resolve_corpus_manifest_path() -> str:
    # 1. Check explicit env var
    env_path = os.environ.get("CORPUS_MANIFEST_PATH")
    if env_path and os.path.exists(env_path):
        return os.path.abspath(env_path)
    
    # 2. Check packaged data inside app/data/
    bundled_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "promoted_corpus_manifest.json")
    )
    if os.path.exists(bundled_path):
        return bundled_path
        
    # 3. Check monorepo path (research/phase_6C/promoted_corpus_manifest.json)
    repo_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "research", "phase_6C", "promoted_corpus_manifest.json")
    )
    if os.path.exists(repo_path):
        return repo_path
        
    return bundled_path

class AppSettings(BaseModel):
    APP_NAME: str = "Dr. Md. Momenul Islam - Clinical Health Intelligence"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_VERSION: str = "0.7.0-prototype"
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "research_development")
    PORT: int = int(os.environ.get("PORT", "8000"))
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    
    # CORS Configuration
    CORS_ORIGINS: str = os.environ.get(
        "CORS_ORIGINS",
        "https://drmomenul.vercel.app,http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )
    
    def get_cors_origins(self) -> List[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # Corpus Lifecycle Configuration — Phase 6C Promoted
    ACTIVE_CORPUS_NAME: str = "NHS_14_CONDITIONS"
    ACTIVE_CORPUS_MANIFEST_PATH: str = _resolve_corpus_manifest_path()
    # Legacy alias
    CORPUS_MANIFEST_PATH: str = ACTIVE_CORPUS_MANIFEST_PATH
    
    # Pre-promotion backup for rollback
    PRE_PROMOTION_BACKUP_PATH: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "research", "phase_6C", "backups", "pre_promotion_active_manifest.json")
    )
    
    # Staged corpus (now empty — all promoted)
    STAGED_RESEARCH_CORPUS_NAME: str = "STAGED_EMPTY"
    STAGED_RESEARCH_MANIFEST_PATH: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "research", "gate_5_27_ingestion", "provenance_manifest.json")
    )
    
    # Retrieval Configuration (Promoted Candidate B — Phase 7A; Parent Strategy 5 from Gate 5.24.1 / Gate 5.29)
    RETRIEVAL_STRATEGY: str = "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR"
    ACTIVE_RETRIEVAL_CANDIDATE: str = "CANDIDATE_B_CONTEXT_AWARE_DISAMBIGUATION"
    CANDIDATE_B_FREEZE_SHA256: str = "92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A"
    PARENT_STRATEGY_SHA256: str = "1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae"
    # Legacy alias
    FROZEN_CANDIDATE_SHA256: str = PARENT_STRATEGY_SHA256
    DENSE_MODEL_NAME: str = "intfloat/multilingual-e5-small"
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-v2-m3"
    DENSE_K: int = 15
    TOP_K_FINAL: int = 5
    OVERVIEW_DEBIAS_MULTIPLIER: float = 0.85
    LAMBDA_DENSE_FUSION: float = 0.10
    ALPHA_LEXICAL_OVERLAP: float = 0.03
    
    # LLM Generation Configuration (Phase 6D Architecture — Generation Disabled by Protocol)
    GENERATION_ENABLED: bool = os.environ.get("GENERATION_ENABLED", "false").lower() in ("true", "1", "yes")
    LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "disabled")  # Options: "disabled", "mock", "gemini", "openai", "ollama"
    LLM_MODEL_NAME: str = os.environ.get("LLM_MODEL_NAME", "disabled")
    LLM_API_KEY_ENV_VAR: str = "LLM_API_KEY"  # Environment variable name for secret loading (NEVER hardcoded)
    LLM_MAX_TOKENS: int = int(os.environ.get("LLM_MAX_TOKENS", "1024"))
    LLM_TEMPERATURE: float = float(os.environ.get("LLM_TEMPERATURE", "0.2"))
    LLM_TIMEOUT_SECONDS: int = int(os.environ.get("LLM_TIMEOUT_SECONDS", "30"))
    LLM_MAX_RETRIES: int = int(os.environ.get("LLM_MAX_RETRIES", "2"))
    
    # Database URL
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./prototype_app.db")

settings = AppSettings()
