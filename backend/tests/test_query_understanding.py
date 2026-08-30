"""
Phase 7A Track B Query Understanding & Clarification Test Suite.
Verifies the 6 key requirements:
1. 'amar paye betha, ki korbo?' -> UNDERSPECIFIED_AMBIGUOUS, SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION, clarification generated.
2. 'হাত পুড়ে গেলে ঠাণ্ডা পানির নিচে কতক্ষণ রাখবো?' -> CLEARLY_ANSWERABLE, SHOW_GROUNDING_CARDS.
3. 'nak diye rokt porle ki korbo?' -> CLEARLY_ANSWERABLE, SHOW_GROUNDING_CARDS.
4. 'What are the symptoms of diabetes?' -> UNSUPPORTED_ACTIVE_CORPUS, SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION.
5. 'amar paye betha ar shash nite koshto hocche' -> POTENTIALLY_EMERGENCY, SHOW_EMERGENCY_OVERRIDE, is_emergency=True.
6. Ambiguous Banglish query ('matha betha ki korbo') -> UNDERSPECIFIED_AMBIGUOUS, clarification question offered.
"""

import pytest
from app.services.query_understanding_service import (
    get_query_understanding_service,
    QueryIntentCategory,
    EvidenceSufficiencyState
)
from app.services.retrieval_service import get_retrieval_service, classify_retrieval_outcome
from app.schemas.api_models import RetrievalOutcomeState

def test_query_1_underspecified_paye_betha():
    """
    Test Case 1: 'amar paye betha, ki korbo?'
    Must be identified as underspecified / ambiguous.
    Evidence presentation policy must suppress unrelated evidence cards.
    Must generate a targeted clarification question.
    """
    qu_service = get_query_understanding_service()
    query = "amar paye betha, ki korbo?"
    res = qu_service.analyze_query(query)
    
    assert res.intent_category == QueryIntentCategory.UNDERSPECIFIED_AMBIGUOUS
    assert res.sufficiency_state == EvidenceSufficiencyState.INSUFFICIENT
    assert res.evidence_presentation_policy == "SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION"
    assert res.is_emergency is False
    assert res.clarification_question is not None
    assert "মচকে যাওয়া" in res.clarification_question.question_text_bn or "sprain" in res.clarification_question.question_text_en.lower()
    assert len(res.clarification_question.options) >= 2

def test_query_2_clearly_answerable_native_bangla_burns():
    """
    Test Case 2: 'হাত পুড়ে গেলে ঠাণ্ডা পানির নিচে কতক্ষণ রাখবো?'
    Must be identified as clearly answerable from active corpus.
    Must retrieve burns and scalds source (DOC-NHS-005).
    """
    qu_service = get_query_understanding_service()
    retrieval_service = get_retrieval_service()
    
    query = "হাত পুড়ে গেলে ঠাণ্ডা পানির নিচে কতক্ষণ রাখবো?"
    qu_res = qu_service.analyze_query(query)
    assert qu_res.intent_category == QueryIntentCategory.CLEARLY_ANSWERABLE
    assert qu_res.sufficiency_state == EvidenceSufficiencyState.SUFFICIENT
    assert qu_res.evidence_presentation_policy == "SHOW_GROUNDING_CARDS"
    assert qu_res.is_emergency is False
    
    norm_q, evidence = retrieval_service.retrieve(query, top_k=5)
    assert len(evidence) == 5
    assert evidence[0].parent_source_id == "DOC-NHS-005"
    state, conf = classify_retrieval_outcome(query, evidence)
    assert state == RetrievalOutcomeState.SUPPORTED_RETRIEVAL

def test_query_3_clearly_answerable_banglish_nosebleed():
    """
    Test Case 3: 'nak diye rokt porle ki korbo?'
    Must be identified as clearly answerable.
    Must retrieve nosebleed source (DOC-NHS-016).
    """
    qu_service = get_query_understanding_service()
    retrieval_service = get_retrieval_service()
    
    query = "nak diye rokt porle ki korbo?"
    qu_res = qu_service.analyze_query(query)
    assert qu_res.intent_category == QueryIntentCategory.CLEARLY_ANSWERABLE
    assert qu_res.sufficiency_state == EvidenceSufficiencyState.SUFFICIENT
    assert qu_res.evidence_presentation_policy == "SHOW_GROUNDING_CARDS"
    
    norm_q, evidence = retrieval_service.retrieve(query, top_k=5)
    assert len(evidence) == 5
    assert evidence[0].parent_source_id == "DOC-NHS-016"

def test_query_4_unsupported_out_of_corpus_diabetes():
    """
    Test Case 4: 'What are the symptoms of diabetes?'
    Must be identified as out of active corpus scope.
    Must suppress unrelated cards and recommend consulting doctor / official resources.
    """
    qu_service = get_query_understanding_service()
    query = "What are the symptoms of diabetes?"
    res = qu_service.analyze_query(query)
    
    assert res.intent_category == QueryIntentCategory.UNSUPPORTED_ACTIVE_CORPUS
    assert res.sufficiency_state == EvidenceSufficiencyState.UNSUPPORTED
    assert res.evidence_presentation_policy == "SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION"
    assert res.is_emergency is False
    assert res.clarification_question is not None

def test_query_5_emergency_sensitive_leg_pain_dyspnea():
    """
    Test Case 5: 'amar paye betha ar shash nite koshto hocche'
    Must trigger immediate POTENTIALLY_EMERGENCY routing.
    Must have is_emergency = True and emergency_advice with 999 instructions.
    """
    qu_service = get_query_understanding_service()
    query = "amar paye betha ar shash nite koshto hocche"
    res = qu_service.analyze_query(query)
    
    assert res.intent_category == QueryIntentCategory.POTENTIALLY_EMERGENCY
    assert res.sufficiency_state == EvidenceSufficiencyState.EMERGENCY
    assert res.is_emergency is True
    assert res.evidence_presentation_policy == "SHOW_EMERGENCY_OVERRIDE"
    assert res.emergency_advice is not None
    assert "999" in res.emergency_advice.emergency_contact or "999" in res.emergency_advice.action_advice_bn

def test_query_6_ambiguous_banglish_matha_betha():
    """
    Test Case 6: 'matha betha ki korbo'
    Underspecified symptom query without duration/one-sided context.
    Must offer clarification instead of ungrounded certainty.
    """
    qu_service = get_query_understanding_service()
    query = "matha betha ki korbo"
    res = qu_service.analyze_query(query)
    
    assert res.intent_category == QueryIntentCategory.UNDERSPECIFIED_AMBIGUOUS
    assert res.clarification_question is not None
    assert res.evidence_presentation_policy == "SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION"
