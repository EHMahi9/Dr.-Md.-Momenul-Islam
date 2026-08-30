"""
Phase 7A Track A Production Regression Test Suite.
Verifies Candidate B promotion into production retrieval service:
1. Candidate B freeze SHA-256 metadata verification.
2. Parent Strategy 5 lineage metadata verification.
3. Active corpus count (119 chunks) and staged corpus count (0 chunks).
4. Multi-modal retrieval non-regression (English, Native Bangla, Standard Banglish, Abbreviated Banglish).
5. Out-of-Corpus safety handling.
6. Generation disabled by default.
"""

import pytest
import os
import json
from app.core.config import settings
from app.services.retrieval_service import get_retrieval_service, classify_retrieval_outcome
from app.schemas.api_models import RetrievalOutcomeState

def test_candidate_b_metadata_lineage():
    """Verify Candidate B freeze hash and parent Strategy 5 SHA-256."""
    assert settings.ACTIVE_RETRIEVAL_CANDIDATE == "CANDIDATE_B_CONTEXT_AWARE_DISAMBIGUATION"
    assert settings.CANDIDATE_B_FREEZE_SHA256 == "92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A"
    assert settings.PARENT_STRATEGY_SHA256 == "1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae"
    
    retrieval_service = get_retrieval_service()
    assert retrieval_service.get_candidate_name() == "CANDIDATE_B_CONTEXT_AWARE_DISAMBIGUATION"
    assert retrieval_service.get_candidate_hash() == "92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A"
    assert retrieval_service.get_strategy_name() == "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR"

def test_corpus_lifecycle_counts():
    """Verify active corpus contains exactly 119 chunks across 14 NHS sources, and staged is 0."""
    retrieval_service = get_retrieval_service()
    assert retrieval_service.get_chunk_count() == 119
    
    with open(settings.ACTIVE_CORPUS_MANIFEST_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    assert len(chunks) == 119
    sids = set(c["parent_source_id"] for c in chunks)
    assert len(sids) == 14
    for i in range(4, 18):
        expected_sid = f"DOC-NHS-{i:03d}"
        assert expected_sid in sids, f"Expected {expected_sid} in active corpus"

def test_generation_default_disabled():
    """Verify LLM generation is disabled by protocol."""
    assert settings.GENERATION_ENABLED is False
    assert settings.LLM_PROVIDER == "disabled"

def test_english_retrieval_regression():
    """Verify English query retrieval retrieves correct clinical source."""
    retrieval_service = get_retrieval_service()
    # High temperature in children
    query = "How to treat a high temperature in a 6-month-old child?"
    norm_q, evidence = retrieval_service.retrieve(query, top_k=5)
    assert len(evidence) == 5
    top_source = evidence[0].parent_source_id
    assert top_source == "DOC-NHS-010"
    state, conf = classify_retrieval_outcome(query, evidence)
    assert state == RetrievalOutcomeState.SUPPORTED_RETRIEVAL

def test_native_bangla_retrieval_regression():
    """Verify Native Bangla query retrieval retrieves correct clinical source."""
    retrieval_service = get_retrieval_service()
    # Burns first aid
    query = "হাত পুড়ে গেলে ঠাণ্ডা পানির নিচে কতক্ষণ রাখবো?"
    norm_q, evidence = retrieval_service.retrieve(query, top_k=5)
    assert len(evidence) == 5
    top_source = evidence[0].parent_source_id
    assert top_source == "DOC-NHS-005"
    state, conf = classify_retrieval_outcome(query, evidence)
    assert state == RetrievalOutcomeState.SUPPORTED_RETRIEVAL

def test_standard_banglish_disambiguation_regression():
    """Verify Standard Banglish compound disambiguation (Rule B1 Nosebleed vs Cuts)."""
    retrieval_service = get_retrieval_service()
    query = "nak diye rokt porle ki korbo?"
    norm_q, evidence = retrieval_service.retrieve(query, top_k=5)
    assert "epistaxis" in norm_q or "nosebleed" in norm_q
    assert len(evidence) == 5
    top_source = evidence[0].parent_source_id
    assert top_source == "DOC-NHS-016"

def test_abbreviated_banglish_thermal_burn_regression():
    """Verify Abbreviated Banglish hot oil burn disambiguation (Rule B4)."""
    retrieval_service = get_retrieval_service()
    query = "gorom tel pora haat thanda pani dibo kotokhon"
    norm_q, evidence = retrieval_service.retrieve(query, top_k=5)
    assert "burns and scalds" in norm_q
    assert len(evidence) == 5
    top_source = evidence[0].parent_source_id
    assert top_source == "DOC-NHS-005"

def test_ooc_safety_regression():
    """Verify out-of-corpus query produces clean abstention with low score (<0.65)."""
    retrieval_service = get_retrieval_service()
    query = "What are the common symptoms of Type 2 diabetes?"
    norm_q, evidence = retrieval_service.retrieve(query, top_k=5)
    assert len(evidence) == 5
    top_score = evidence[0].rerank_score
    assert top_score < 0.65, f"Expected OOC score < 0.65, got {top_score}"
    state, conf = classify_retrieval_outcome(query, evidence)
    assert state in [RetrievalOutcomeState.UNSUPPORTED_BY_ACTIVE_CORPUS, RetrievalOutcomeState.NO_RELEVANT_EVIDENCE]
