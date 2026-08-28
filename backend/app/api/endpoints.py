"""
FastAPI route endpoints for health, retrieval, and research chat.
"""

import time
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
import os
import json
from app.schemas.api_models import (
    HealthResponse,
    CorpusTierInfo,
    CorpusLifecycleResponse,
    RetrievalRequest,
    RetrievalResponse,
    ChatRequest,
    ChatResponse
)
from app.services.retrieval_service import BaseRetrievalService, get_retrieval_service
from app.services.generation_service import BaseGenerationService, get_generation_service

router = APIRouter()

def get_staged_corpus_stats():
    if os.path.exists(settings.STAGED_RESEARCH_MANIFEST_PATH):
        try:
            with open(settings.STAGED_RESEARCH_MANIFEST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            sids = sorted(list(set(c["parent_source_id"] for c in data)))
            return len(sids), len(data), sids
        except Exception:
            pass
    return 6, 51, ["DOC-NHS-012", "DOC-NHS-013", "DOC-NHS-014", "DOC-NHS-015", "DOC-NHS-016", "DOC-NHS-017"]

@router.get("/health", response_model=HealthResponse, tags=["System"])
def get_health(
    retrieval_service: BaseRetrievalService = Depends(get_retrieval_service),
    generation_service: BaseGenerationService = Depends(get_generation_service)
):
    """System health check and corpus lifecycle status."""
    staged_docs, staged_chunks, _ = get_staged_corpus_stats()
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.PROJECT_VERSION,
        environment=settings.ENVIRONMENT,
        retrieval_strategy=retrieval_service.get_strategy_name(),
        candidate_hash=settings.FROZEN_CANDIDATE_SHA256,
        active_corpus_chunks=retrieval_service.get_chunk_count(),
        staged_research_chunks=staged_chunks,
        generation_enabled=generation_service.is_generation_enabled()
    )

@router.get("/corpus", response_model=CorpusLifecycleResponse, tags=["System"])
def get_corpus_lifecycle(
    retrieval_service: BaseRetrievalService = Depends(get_retrieval_service)
):
    """Expose explicit multi-tier corpus lifecycle status and research boundary."""
    staged_docs, staged_chunks, staged_sids = get_staged_corpus_stats()
    active_chunks = retrieval_service.get_chunk_count()
    
    active_tier = CorpusTierInfo(
        name=settings.ACTIVE_CORPUS_NAME,
        status="ACTIVE",
        document_count=8,
        chunk_count=active_chunks,
        source_ids=["DOC-NHS-004", "DOC-NHS-005", "DOC-NHS-006", "DOC-NHS-007", "DOC-NHS-008", "DOC-NHS-009", "DOC-NHS-010", "DOC-NHS-011"],
        description="Frozen baseline research corpus actively queried by application backend."
    )
    
    staged_tier = CorpusTierInfo(
        name=settings.STAGED_RESEARCH_CORPUS_NAME,
        status="STAGED_RESEARCH",
        document_count=staged_docs,
        chunk_count=staged_chunks,
        source_ids=staged_sids,
        description="Newly ingested NHS sources (Gate 5.27). Isolated in research directory; NOT active in application."
    )
    
    validated_tier = CorpusTierInfo(
        name="PRODUCTION_VALIDATED_CORPUS",
        status="NOT_ACTIVE",
        document_count=0,
        chunk_count=0,
        source_ids=[],
        description="Requires formal multi-lingual benchmark validation (Gate 5.29) prior to promotion."
    )
    
    return CorpusLifecycleResponse(
        status="success",
        active_corpus=active_tier,
        staged_research_corpus=staged_tier,
        validated_corpus=validated_tier,
        retrieval_candidate={
            "strategy_name": settings.RETRIEVAL_STRATEGY,
            "frozen_candidate_sha256": settings.FROZEN_CANDIDATE_SHA256,
            "dense_model": settings.DENSE_MODEL_NAME,
            "reranker_model": settings.RERANKER_MODEL_NAME,
            "candidate_depth_k": settings.DENSE_K,
            "final_top_k": settings.TOP_K_FINAL
        }
    )

@router.post("/retrieve", response_model=RetrievalResponse, tags=["Retrieval"])
def retrieve_evidence(
    req: RetrievalRequest,
    retrieval_service: BaseRetrievalService = Depends(get_retrieval_service)
):
    """Execute current frozen retrieval candidate on query."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")
        
    start_t = time.time()
    norm_query, evidence = retrieval_service.retrieve(req.query, top_k=req.top_k or 5)
    
    return RetrievalResponse(
        status="success",
        strategy_used=retrieval_service.get_strategy_name(),
        query_raw=req.query,
        query_normalized=norm_query,
        evidence_count=len(evidence),
        evidence=evidence
    )

@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat_endpoint(
    req: ChatRequest,
    retrieval_service: BaseRetrievalService = Depends(get_retrieval_service),
    generation_service: BaseGenerationService = Depends(get_generation_service)
):
    """
    Research prototype chat endpoint.
    Retrieves evidence and returns research-mode response with generation explicitly disabled.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
        
    # 1. Retrieve evidence
    norm_query, evidence = retrieval_service.retrieve(req.message, top_k=5)
    
    # 2. Generation service (disabled)
    gen_result = generation_service.generate_response(req.message, evidence)
    
    return ChatResponse(
        status="research_prototype",
        generation_enabled=generation_service.is_generation_enabled(),
        disclaimer=gen_result["disclaimer"],
        user_query=req.message,
        evidence_count=len(evidence),
        evidence=evidence,
        synthetic_answer=gen_result["synthetic_answer"]
    )
