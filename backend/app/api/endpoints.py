"""
FastAPI route endpoints for health, retrieval, and research chat.
Includes robust input validation, error handling, and structured outcome classification.
"""

import time
import logging
import os
import json
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import settings
from app.schemas.api_models import (
    HealthResponse,
    CorpusTierInfo,
    CorpusLifecycleResponse,
    RetrievalRequest,
    RetrievalResponse,
    ChatRequest,
    ChatResponse,
    RetrievalMetadata,
    RetrievalOutcomeState,
    ConfidenceAssessment
)
from app.services.retrieval_service import (
    BaseRetrievalService,
    get_retrieval_service,
    classify_retrieval_outcome
)
from app.services.generation_service import (
    BaseGenerationService,
    get_generation_service
)

logger = logging.getLogger("dr_momenul_islam.api")
router = APIRouter()

def get_staged_corpus_stats():
    if os.path.exists(settings.STAGED_RESEARCH_MANIFEST_PATH):
        try:
            with open(settings.STAGED_RESEARCH_MANIFEST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            sids = sorted(list(set(c["parent_source_id"] for c in data)))
            return len(sids), len(data), sids
        except Exception as e:
            logger.warning(f"Failed to read staged corpus manifest: {e}")
    return 6, 51, ["DOC-NHS-012", "DOC-NHS-013", "DOC-NHS-014", "DOC-NHS-015", "DOC-NHS-016", "DOC-NHS-017"]

def build_retrieval_metadata(retrieval_service: BaseRetrievalService) -> RetrievalMetadata:
    return RetrievalMetadata(
        strategy_name=retrieval_service.get_strategy_name(),
        candidate_hash=settings.FROZEN_CANDIDATE_SHA256,
        active_corpus_name=settings.ACTIVE_CORPUS_NAME,
        active_chunks_count=retrieval_service.get_chunk_count(),
        dense_k=settings.DENSE_K,
        final_top_k=settings.TOP_K_FINAL
    )

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
    
    # Dynamically derive active source IDs from loaded corpus
    active_source_ids = sorted(list(set(
        c["parent_source_id"] for c in retrieval_service.chunks
    ))) if hasattr(retrieval_service, 'chunks') else []
    
    active_tier = CorpusTierInfo(
        name=settings.ACTIVE_CORPUS_NAME,
        status="ACTIVE",
        document_count=len(active_source_ids),
        chunk_count=active_chunks,
        source_ids=active_source_ids,
        description="Phase 6C promoted corpus: 8 original + 6 Gate 5.29-validated NHS sources."
    )
    
    staged_tier = CorpusTierInfo(
        name=settings.STAGED_RESEARCH_CORPUS_NAME,
        status="PROMOTED",
        document_count=0,
        chunk_count=0,
        source_ids=[],
        description="All 6 staged research sources (DOC-NHS-012..017) have been promoted to ACTIVE via Phase 6C."
    )
    
    validated_tier = CorpusTierInfo(
        name="PRODUCTION_VALIDATED_CORPUS",
        status="NOT_ACTIVE",
        document_count=0,
        chunk_count=0,
        source_ids=[],
        description="No additional sources pending validation."
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
    """Execute current frozen retrieval candidate on query with structured outcome classification."""
    clean_query = req.query.strip() if req.query else ""
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query text cannot be empty or contain only whitespace."
        )
        
    if len(clean_query) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query text exceeds maximum limit of 1000 characters."
        )
        
    try:
        norm_query, evidence = retrieval_service.retrieve(clean_query, top_k=req.top_k or 5)
        outcome_state, confidence_assessment = classify_retrieval_outcome(clean_query, evidence)
        metadata = build_retrieval_metadata(retrieval_service)
        
        return RetrievalResponse(
            status="success",
            outcome_state=outcome_state,
            confidence_assessment=confidence_assessment,
            strategy_used=retrieval_service.get_strategy_name(),
            query_raw=clean_query,
            query_normalized=norm_query,
            evidence_count=len(evidence),
            evidence=evidence,
            retrieval_metadata=metadata
        )
    except Exception as e:
        logger.error(f"Retrieval error for query '{clean_query[:50]}...': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Retrieval service encountered an internal error processing your query."
        )

@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat_endpoint(
    req: ChatRequest,
    retrieval_service: BaseRetrievalService = Depends(get_retrieval_service),
    generation_service: BaseGenerationService = Depends(get_generation_service)
):
    """
    Research prototype chat endpoint.
    Retrieves evidence, computes structured outcome states, and returns research-mode response with generation strictly disabled.
    """
    clean_msg = req.message.strip() if req.message else ""
    if not clean_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty or contain only whitespace."
        )
        
    if len(clean_msg) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message exceeds maximum limit of 1000 characters."
        )
        
    try:
        # 1. Retrieve evidence
        norm_query, evidence = retrieval_service.retrieve(clean_msg, top_k=5)
        outcome_state, confidence_assessment = classify_retrieval_outcome(clean_msg, evidence)
        metadata = build_retrieval_metadata(retrieval_service)
        
        # 2. Generation service (disabled by protocol)
        gen_result = generation_service.generate_response(clean_msg, evidence)
        
        return ChatResponse(
            status="research_prototype",
            outcome_state=outcome_state,
            confidence_assessment=confidence_assessment,
            generation_enabled=generation_service.is_generation_enabled(),
            disclaimer=gen_result["disclaimer"],
            user_query=clean_msg,
            evidence_count=len(evidence),
            evidence=evidence,
            synthetic_answer=gen_result["synthetic_answer"],
            retrieval_metadata=metadata,
            generation_result=gen_result.get("generation_result")
        )
    except Exception as e:
        logger.error(f"Chat retrieval error for message '{clean_msg[:50]}...': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat service encountered an internal error processing your request."
        )
