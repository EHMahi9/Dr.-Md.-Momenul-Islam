"""
FastAPI route endpoints for health, retrieval, and research chat.
"""

import time
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from app.schemas.api_models import (
    HealthResponse,
    RetrievalRequest,
    RetrievalResponse,
    ChatRequest,
    ChatResponse
)
from app.services.retrieval_service import BaseRetrievalService, get_retrieval_service
from app.services.generation_service import BaseGenerationService, get_generation_service

router = APIRouter()

@router.get("/health", response_model=HealthResponse, tags=["System"])
def get_health(
    retrieval_service: BaseRetrievalService = Depends(get_retrieval_service),
    generation_service: BaseGenerationService = Depends(get_generation_service)
):
    """System health check and retrieval status."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.PROJECT_VERSION,
        environment=settings.ENVIRONMENT,
        retrieval_strategy=retrieval_service.get_strategy_name(),
        corpus_chunks_loaded=retrieval_service.get_chunk_count(),
        generation_enabled=generation_service.is_generation_enabled()
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
