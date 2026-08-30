"""
FastAPI route endpoints for health, retrieval, and research chat.
Includes robust input validation, error handling, and structured outcome classification.
"""

import time
import logging
import os
import json
import re
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
from app.services.query_understanding_service import (
    QueryUnderstandingService,
    get_query_understanding_service,
    QueryIntentCategory,
    QueryUnderstandingResult
)

from app.services.conversation_state_service import (
    ConversationStateService,
    get_conversation_state_service
)
from app.schemas.api_models import (
    ConversationAction,
    ClarificationState,
    ConversationContextState,
    EvidenceSufficiencyState
)

logger = logging.getLogger("dr_momenul_islam.api")
router = APIRouter()

def get_staged_corpus_stats():
    """
    Return staged research corpus stats.
    When ACTIVE_CORPUS_NAME is NHS_14_CONDITIONS, all 6 research sources
    (DOC-NHS-012..017) are promoted into ACTIVE, leaving 0 staged research chunks.
    """
    if settings.ACTIVE_CORPUS_NAME == "NHS_14_CONDITIONS":
        return 0, 0, []
    if os.path.exists(settings.STAGED_RESEARCH_MANIFEST_PATH):
        try:
            with open(settings.STAGED_RESEARCH_MANIFEST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            sids = sorted(list(set(c["parent_source_id"] for c in data)))
            return len(sids), len(data), sids
        except Exception as e:
            logger.warning(f"Failed to read staged corpus manifest: {e}")
    return 0, 0, []

def build_retrieval_metadata(retrieval_service: BaseRetrievalService) -> RetrievalMetadata:
    return RetrievalMetadata(
        strategy_name=retrieval_service.get_strategy_name(),
        active_candidate=retrieval_service.get_candidate_name(),
        candidate_hash=settings.FROZEN_CANDIDATE_SHA256,
        candidate_b_hash=settings.CANDIDATE_B_FREEZE_SHA256,
        parent_strategy_hash=settings.PARENT_STRATEGY_SHA256,
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
        active_candidate=retrieval_service.get_candidate_name(),
        candidate_hash=settings.FROZEN_CANDIDATE_SHA256,
        candidate_b_hash=settings.CANDIDATE_B_FREEZE_SHA256,
        parent_strategy_hash=settings.PARENT_STRATEGY_SHA256,
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
            "active_candidate": settings.ACTIVE_RETRIEVAL_CANDIDATE,
            "candidate_b_freeze_sha256": settings.CANDIDATE_B_FREEZE_SHA256,
            "parent_strategy_sha256": settings.PARENT_STRATEGY_SHA256,
            "dense_model": settings.DENSE_MODEL_NAME,
            "reranker_model": settings.RERANKER_MODEL_NAME,
            "candidate_depth_k": settings.DENSE_K,
            "final_top_k": settings.TOP_K_FINAL
        }
    )

@router.post("/query/understand", response_model=QueryUnderstandingResult, tags=["Query Understanding"])
def analyze_query_endpoint(
    req: RetrievalRequest,
    qu_service: QueryUnderstandingService = Depends(get_query_understanding_service)
):
    """Inspect query understanding, ambiguity classification, and emergency detection."""
    clean_query = req.query.strip() if req.query else ""
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query text cannot be empty or contain only whitespace."
        )
    return qu_service.analyze_query(clean_query, preferred_language=req.preferred_language or "auto")

@router.post("/retrieve", response_model=RetrievalResponse, tags=["Retrieval"])
def retrieve_evidence(
    req: RetrievalRequest,
    retrieval_service: BaseRetrievalService = Depends(get_retrieval_service),
    qu_service: QueryUnderstandingService = Depends(get_query_understanding_service)
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
        
        # Track B: Query Understanding & Evidence Sufficiency Assessment
        pref_lang = req.preferred_language or "auto"
        qu_result = qu_service.analyze_query(clean_query, preferred_language=pref_lang)
        
        # Determine deterministic presentation policy
        if qu_result.is_emergency:
            policy = "SHOW_EMERGENCY_OVERRIDE"
        elif (
            qu_result.intent_category in [
                QueryIntentCategory.UNDERSPECIFIED_AMBIGUOUS,
                QueryIntentCategory.UNSUPPORTED_ACTIVE_CORPUS
            ]
            or outcome_state in [
                RetrievalOutcomeState.NO_RELEVANT_EVIDENCE,
                RetrievalOutcomeState.UNSUPPORTED_BY_ACTIVE_CORPUS
            ]
        ):
            policy = "SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION"
        else:
            policy = "SHOW_GROUNDING_CARDS"
        
        return RetrievalResponse(
            status="success",
            outcome_state=outcome_state,
            confidence_assessment=confidence_assessment,
            strategy_used=retrieval_service.get_strategy_name(),
            query_raw=clean_query,
            query_normalized=norm_query,
            evidence_count=len(evidence),
            evidence=evidence,
            retrieval_metadata=metadata,
            query_understanding=qu_result,
            evidence_presentation_policy=policy
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
    generation_service: BaseGenerationService = Depends(get_generation_service),
    qu_service: QueryUnderstandingService = Depends(get_query_understanding_service),
    conv_service: ConversationStateService = Depends(get_conversation_state_service)
):
    """
    Phase 7B Conversational Chat Endpoint.
    Integrates multi-turn context tracking, deterministic clarification planning, and refined Candidate B retrieval.
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
        pref_lang = req.preferred_language or "auto"
        session_id = req.session_id or f"sess-{abs(hash(clean_msg)) % 1000000}"
        
        # 1. Turn-level Query Understanding & Emergency Screening
        qu_result = qu_service.analyze_query(clean_msg, preferred_language=pref_lang)
        
        # 2. Emergency Red Flag Intercept (Immediate Priority)
        if qu_result.is_emergency:
            context_state = conv_service.update_context_state(
                req.context_state,
                clean_msg,
                detected_lang=qu_result.detected_language,
                preferred_lang=pref_lang
            )
            context_state.next_action = ConversationAction.EMERGENCY
            context_state.clarification_state = ClarificationState.NOT_NEEDED
            
            norm_query, evidence = retrieval_service.retrieve(clean_msg, top_k=5)
            outcome_state, confidence_assessment = classify_retrieval_outcome(clean_msg, evidence)
            metadata = build_retrieval_metadata(retrieval_service)
            gen_result = generation_service.generate_response(clean_msg, evidence, preferred_language=pref_lang)
            
            return ChatResponse(
                status="research_prototype",
                outcome_state=outcome_state,
                confidence_assessment=confidence_assessment,
                generation_enabled=generation_service.is_generation_enabled(),
                disclaimer=gen_result["disclaimer"],
                session_id=session_id,
                user_query=clean_msg,
                preferred_language=pref_lang,
                response_language=qu_result.resolved_response_language,
                next_action=ConversationAction.EMERGENCY,
                clarification_state=ClarificationState.NOT_NEEDED,
                context_state=context_state,
                evidence_count=len(evidence),
                evidence=evidence,
                synthetic_answer=gen_result["synthetic_answer"],
                retrieval_metadata=metadata,
                generation_result=gen_result.get("generation_result"),
                query_understanding=qu_result,
                evidence_presentation_policy="SHOW_EMERGENCY_OVERRIDE"
            )

        # 3. Explicit Out-of-Corpus Topic Intercept
        if qu_result.intent_category == QueryIntentCategory.UNSUPPORTED_ACTIVE_CORPUS:
            context_state = conv_service.update_context_state(
                req.context_state,
                clean_msg,
                detected_lang=qu_result.detected_language,
                preferred_lang=pref_lang
            )
            context_state.next_action = ConversationAction.ABSTAIN
            context_state.clarification_state = ClarificationState.UNSUPPORTED_TOPIC
            
            norm_query, evidence = retrieval_service.retrieve(clean_msg, top_k=5)
            outcome_state, confidence_assessment = classify_retrieval_outcome(clean_msg, evidence)
            metadata = build_retrieval_metadata(retrieval_service)
            gen_result = generation_service.generate_response(clean_msg, evidence, preferred_language=pref_lang)
            
            return ChatResponse(
                status="research_prototype",
                outcome_state=outcome_state,
                confidence_assessment=confidence_assessment,
                generation_enabled=generation_service.is_generation_enabled(),
                disclaimer=gen_result["disclaimer"],
                session_id=session_id,
                user_query=clean_msg,
                preferred_language=pref_lang,
                response_language=qu_result.resolved_response_language,
                next_action=ConversationAction.ABSTAIN,
                clarification_state=ClarificationState.UNSUPPORTED_TOPIC,
                context_state=context_state,
                evidence_count=len(evidence),
                evidence=evidence,
                synthetic_answer=gen_result["synthetic_answer"],
                retrieval_metadata=metadata,
                generation_result=gen_result.get("generation_result"),
                query_understanding=qu_result,
                evidence_presentation_policy="SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION"
            )

        # 4. Multi-Turn Conversation State Update
        context_state = conv_service.update_context_state(
            req.context_state,
            clean_msg,
            detected_lang=qu_result.detected_language,
            preferred_lang=pref_lang,
            initial_qu_body_location=qu_result.extracted_body_location
        )
        context_state.session_id = session_id
        
        # Check if this is a follow-up clarification turn (turn_count > 1)
        if context_state.turn_count > 1 and req.context_state is not None:
            # Build Refined Query Representation from accumulated context
            refined_query = conv_service.build_refined_query(context_state)
            norm_query, evidence = retrieval_service.retrieve(refined_query, top_k=5)
            outcome_state, confidence_assessment = classify_retrieval_outcome(refined_query, evidence)
            
            # Evaluate Evidence Sufficiency on Refined Retrieval
            suff_state, next_act, reason = conv_service.evaluate_evidence_sufficiency(evidence, context_state)
            
            if next_act == ConversationAction.ANSWER:
                next_action = ConversationAction.ANSWER
                clar_state = ClarificationState.RESOLVED
                policy = "SHOW_GROUNDING_CARDS"
                qu_result.intent_category = QueryIntentCategory.CLEARLY_ANSWERABLE
                qu_result.sufficiency_state = EvidenceSufficiencyState.SUFFICIENT
                qu_result.clarification_question = None
            elif next_act == ConversationAction.CLARIFY:
                next_clar = conv_service.plan_clarification_question(context_state, preferred_lang=pref_lang)
                if next_clar:
                    qu_result.clarification_question = next_clar
                    next_action = ConversationAction.CLARIFY
                    clar_state = ClarificationState.IN_PROGRESS
                    policy = "SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION"
                else:
                    next_action = ConversationAction.ABSTAIN
                    clar_state = ClarificationState.MAX_TURNS_EXCEEDED
                    policy = "SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION"
            else: # ABSTAIN
                next_action = ConversationAction.ABSTAIN
                clar_state = ClarificationState.MAX_TURNS_EXCEEDED
                policy = "SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION"
        else:
            # Turn 1: Initial user query
            if qu_result.intent_category == QueryIntentCategory.UNDERSPECIFIED_AMBIGUOUS:
                # Plan first clarification question
                first_clar = conv_service.plan_clarification_question(context_state, preferred_lang=pref_lang)
                if first_clar:
                    qu_result.clarification_question = first_clar
                next_action = ConversationAction.CLARIFY
                clar_state = ClarificationState.IN_PROGRESS
                policy = "SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION"
                
                # Execute retrieval for diagnostic baseline
                norm_query, evidence = retrieval_service.retrieve(clean_msg, top_k=5)
                outcome_state, confidence_assessment = classify_retrieval_outcome(clean_msg, evidence)
            else:
                # Clearly answerable single-turn query
                next_action = ConversationAction.ANSWER
                clar_state = ClarificationState.NOT_NEEDED
                policy = "SHOW_GROUNDING_CARDS"
                
                norm_query, evidence = retrieval_service.retrieve(clean_msg, top_k=5)
                outcome_state, confidence_assessment = classify_retrieval_outcome(clean_msg, evidence)

        metadata = build_retrieval_metadata(retrieval_service)
        gen_result = generation_service.generate_response(clean_msg, evidence, preferred_language=pref_lang)
        actual_response_lang = qu_result.resolved_response_language
        
        context_state.next_action = next_action
        context_state.clarification_state = clar_state
        
        return ChatResponse(
            status="research_prototype",
            outcome_state=outcome_state,
            confidence_assessment=confidence_assessment,
            generation_enabled=generation_service.is_generation_enabled(),
            disclaimer=gen_result["disclaimer"],
            session_id=session_id,
            user_query=clean_msg,
            preferred_language=pref_lang,
            response_language=actual_response_lang,
            next_action=next_action,
            clarification_state=clar_state,
            context_state=context_state,
            evidence_count=len(evidence),
            evidence=evidence,
            synthetic_answer=gen_result["synthetic_answer"],
            retrieval_metadata=metadata,
            generation_result=gen_result.get("generation_result"),
            query_understanding=qu_result,
            evidence_presentation_policy=policy
        )
    except Exception as e:
        logger.error(f"Chat retrieval error for message '{clean_msg[:50]}...': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat service encountered an internal error processing your request."
        )
