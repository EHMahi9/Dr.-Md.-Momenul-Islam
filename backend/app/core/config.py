"""
Application configuration for Dr. Md. Momenul Islam Backend.
"""

import os
from pydantic import BaseModel

class AppSettings(BaseModel):
    APP_NAME: str = "Dr. Md. Momenul Islam - Clinical Health Intelligence"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_VERSION: str = "0.6.0-prototype"
    ENVIRONMENT: str = "research_development"
    
    # Corpus Lifecycle Configuration
    ACTIVE_CORPUS_NAME: str = "BASELINE_NHS_8_CONDITIONS"
    ACTIVE_CORPUS_MANIFEST_PATH: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "research", "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
    )
    # Legacy alias
    CORPUS_MANIFEST_PATH: str = ACTIVE_CORPUS_MANIFEST_PATH
    
    STAGED_RESEARCH_CORPUS_NAME: str = "EXPANDED_NHS_6_CONDITIONS"
    STAGED_RESEARCH_MANIFEST_PATH: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "research", "gate_5_27_ingestion", "provenance_manifest.json")
    )
    
    # Retrieval Configuration (Frozen Strategy 5 from Gate 5.24.1 / Gate 5.29)
    RETRIEVAL_STRATEGY: str = "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR"
    FROZEN_CANDIDATE_SHA256: str = "1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae"
    DENSE_MODEL_NAME: str = "intfloat/multilingual-e5-small"
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-v2-m3"
    DENSE_K: int = 15
    TOP_K_FINAL: int = 5
    OVERVIEW_DEBIAS_MULTIPLIER: float = 0.85
    LAMBDA_DENSE_FUSION: float = 0.10
    ALPHA_LEXICAL_OVERLAP: float = 0.03
    
    # LLM Generation Status
    GENERATION_ENABLED: bool = False
    
    # Database URL
    DATABASE_URL: str = "sqlite:///./prototype_app.db"

settings = AppSettings()
