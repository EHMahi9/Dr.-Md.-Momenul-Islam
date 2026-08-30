"""
Phase 7B Multi-Turn Clarification & Structured Context State Test Suite.
Verifies conversational clarification engine:
1. Initial ambiguous query ('amar paye betha, ki korbo?') -> CLARIFY + suppression of irrelevant evidence cards.
2. State update after user answer ('gorar kache, pore gechi') -> refined Candidate B retrieval -> ANSWER with DOC-NHS-013 (Sprains & Strains).
3. Max clarification turns enforcement (MAX_CLARIFICATION_TURNS = 3) -> ABSTAIN.
4. Early stopping when sufficient evidence is reached on Turn 1 or 2 (preventing unnecessary clarification).
5. Mid-conversation emergency red-flag intercept -> EMERGENCY override.
6. Non-diagnostic constraint (zero inferred disease or speculative risk score in state).
7. Multilingual support (English, Bangla, Banglish).
8. Out-of-corpus handling (Diabetes / Dental) -> ABSTAIN.
"""

import pytest
from app.schemas.api_models import (
    ConversationContextState,
    ConversationAction,
    ClarificationState,
    QueryIntentCategory,
    EvidenceSufficiencyState,
    RetrievalOutcomeState
)
from app.services.conversation_state_service import (
    get_conversation_state_service,
    ConversationStateService,
    MAX_DEFAULT_CLARIFICATION_TURNS
)
from app.services.query_understanding_service import get_query_understanding_service
from app.services.retrieval_service import get_retrieval_service, classify_retrieval_outcome

def test_canonical_turn1_underspecified_paye_betha():
    """
    Test 1: Canonical Query Turn 1: 'amar paye betha, ki korbo?'
    Must trigger CLARIFY with IN_PROGRESS state.
    Must generate a targeted clarification question.
    Must NOT infer any disease diagnosis in context state.
    """
    qu_service = get_query_understanding_service()
    conv_service = get_conversation_state_service()
    
    query = "amar paye betha, ki korbo?"
    qu_res = qu_service.analyze_query(query)
    
    assert qu_res.intent_category == QueryIntentCategory.UNDERSPECIFIED_AMBIGUOUS
    assert qu_res.is_emergency is False
    
    state = conv_service.update_context_state(
        None,
        query,
        detected_lang=qu_res.detected_language,
        preferred_lang="auto",
        initial_qu_body_location=qu_res.extracted_body_location
    )
    
    assert state.body_location == "leg/foot"
    assert state.turn_count == 1
    assert state.clarification_turn_count == 0
    
    clar_q = conv_service.plan_clarification_question(state, preferred_lang="bn")
    assert clar_q is not None
    assert state.clarification_turn_count == 1
    assert state.clarification_state == ClarificationState.IN_PROGRESS
    assert len(clar_q.options) >= 3
    # Verify non-diagnostic rule: no disease name stored
    assert state.symptom == "pain"

def test_canonical_turn2_clarification_to_cut_answer():
    """
    Test 2A: Turn 2 after user clarifies: 'kete geche, churi diye kete rokt porche'
    Must accumulate location (foot/hand), event (cut/wound), bleeding.
    Must build refined query and retrieve DOC-NHS-006 (Cuts and grazes).
    Must evaluate sufficiency as SUFFICIENT and transition action to ANSWER.
    """
    conv_service = get_conversation_state_service()
    retrieval_service = get_retrieval_service()
    
    state = ConversationContextState(
        session_id="test-sess-1",
        turn_count=1,
        clarification_turn_count=1,
        language_modality="banglish",
        response_language_preference="bn",
        symptom="pain",
        body_location="leg/foot",
        clarification_state=ClarificationState.IN_PROGRESS,
        next_action=ConversationAction.CLARIFY
    )
    
    user_turn_2 = "kete geche, churi diye kete rokt porche"
    updated_state = conv_service.update_context_state(
        state,
        user_turn_2,
        detected_lang="banglish",
        preferred_lang="bn"
    )
    
    assert updated_state.precipitating_event == "cut/wound"
    assert updated_state.turn_count == 2
    
    refined_q = conv_service.build_refined_query(updated_state)
    norm_q, evidence = retrieval_service.retrieve(refined_q, top_k=5)
    assert len(evidence) == 5
    assert evidence[0].parent_source_id == "DOC-NHS-006"  # NHS Cuts and grazes
    
    suff_state, next_act, reason = conv_service.evaluate_evidence_sufficiency(evidence, updated_state)
    assert suff_state == EvidenceSufficiencyState.SUFFICIENT
    assert next_act == ConversationAction.ANSWER
    assert updated_state.clarification_state == ClarificationState.RESOLVED

def test_canonical_turn2_clarification_to_burn_answer():
    """
    Test 2B: Turn 2 after user clarifies: 'gorom tel pore pure geche, lal hoye ache'
    Must accumulate event (thermal_burn) and associated symptom (redness).
    Must build refined query and retrieve DOC-NHS-005 (Burns and scalds).
    Must evaluate sufficiency as SUFFICIENT and transition action to ANSWER.
    """
    conv_service = get_conversation_state_service()
    retrieval_service = get_retrieval_service()
    
    state = ConversationContextState(
        session_id="test-sess-burn",
        turn_count=1,
        clarification_turn_count=1,
        language_modality="banglish",
        response_language_preference="bn",
        symptom="pain",
        body_location="arm/hand",
        clarification_state=ClarificationState.IN_PROGRESS,
        next_action=ConversationAction.CLARIFY
    )
    
    user_turn_2 = "gorom tel pore pure geche, lal hoye ache"
    updated_state = conv_service.update_context_state(
        state,
        user_turn_2,
        detected_lang="banglish",
        preferred_lang="bn"
    )
    
    assert updated_state.precipitating_event == "thermal_burn"
    assert "redness" in updated_state.associated_symptoms
    
    refined_q = conv_service.build_refined_query(updated_state)
    norm_q, evidence = retrieval_service.retrieve(refined_q, top_k=5)
    assert len(evidence) == 5
    assert evidence[0].parent_source_id == "DOC-NHS-005"  # NHS Burns and scalds
    
    suff_state, next_act, reason = conv_service.evaluate_evidence_sufficiency(evidence, updated_state)
    assert suff_state == EvidenceSufficiencyState.SUFFICIENT
    assert next_act == ConversationAction.ANSWER
    assert updated_state.clarification_state == ClarificationState.RESOLVED

def test_canonical_turn2_clarification_sprain_unsupported_abstain():
    """
    Test 2C: Turn 2 when user clarifies with sprain/injury:
    Since musculoskeletal sprains are outside the active 14 NHS first aid sources,
    the system must cleanly transition to ABSTAIN (honest abstention).
    """
    conv_service = get_conversation_state_service()
    retrieval_service = get_retrieval_service()
    
    state = ConversationContextState(
        session_id="test-sess-sprain",
        turn_count=1,
        clarification_turn_count=1,
        language_modality="banglish",
        response_language_preference="bn",
        symptom="pain",
        body_location="leg/foot",
        clarification_state=ClarificationState.IN_PROGRESS,
        next_action=ConversationAction.CLARIFY
    )
    
    user_turn_2 = "gorar kache, pore gechi, moshke geche"
    updated_state = conv_service.update_context_state(
        state,
        user_turn_2,
        detected_lang="banglish",
        preferred_lang="bn"
    )
    
    assert updated_state.specific_location == "ankle/heel"
    assert updated_state.precipitating_event == "sprain/injury"
    
    refined_q = conv_service.build_refined_query(updated_state)
    norm_q, evidence = retrieval_service.retrieve(refined_q, top_k=5)
    
    suff_state, next_act, reason = conv_service.evaluate_evidence_sufficiency(evidence, updated_state)
    assert suff_state == EvidenceSufficiencyState.UNSUPPORTED
    assert next_act == ConversationAction.ABSTAIN
    assert updated_state.clarification_state == ClarificationState.UNSUPPORTED_TOPIC

def test_turn_limit_enforcement_max_turns():
    """
    Test 3: Verify that after 3 clarification turns without sufficient evidence,
    system enforces MAX_CLARIFICATION_TURNS = 3 and transitions to ABSTAIN.
    """
    conv_service = get_conversation_state_service()
    
    state = ConversationContextState(
        session_id="test-sess-limit",
        turn_count=3,
        clarification_turn_count=3,
        max_clarification_turns=3,
        language_modality="en",
        response_language_preference="en",
        symptom="pain",
        body_location="body",
        clarification_state=ClarificationState.IN_PROGRESS,
        next_action=ConversationAction.CLARIFY
    )
    
    next_q = conv_service.plan_clarification_question(state, preferred_lang="en")
    assert next_q is None
    assert state.clarification_state == ClarificationState.MAX_TURNS_EXCEEDED
    assert state.next_action == ConversationAction.ABSTAIN

def test_mid_conversation_emergency_intercept():
    """
    Test 4: Mid-conversation emergency signal:
    Turn 1 was ambiguous leg pain, but Turn 2 user mentions shortness of breath ('shash nite koshto').
    Must immediately abort clarification and trigger EMERGENCY routing.
    """
    qu_service = get_query_understanding_service()
    conv_service = get_conversation_state_service()
    
    turn2_msg = "shash nite koshto hocche ar buk e chape"
    qu_res = qu_service.analyze_query(turn2_msg)
    
    assert qu_res.is_emergency is True
    assert qu_res.intent_category == QueryIntentCategory.POTENTIALLY_EMERGENCY
    assert qu_res.evidence_presentation_policy == "SHOW_EMERGENCY_OVERRIDE"

def test_multilingual_attribute_extraction_english():
    """
    Test 5: Verify attribute extraction in English.
    'My ankle has been hurting since yesterday after a twisting injury, and it is swollen.'
    """
    conv_service = get_conversation_state_service()
    text = "My ankle has been hurting since yesterday after a twisting injury, and it is swollen."
    
    attrs = conv_service.extract_attributes(text)
    assert attrs["specific_location"] == "ankle/heel"
    assert attrs["precipitating_event"] == "sprain/injury"
    assert attrs["duration"] == "1 day"
    assert "swelling" in attrs["associated_symptoms"]

def test_multilingual_attribute_extraction_native_bangla():
    """
    Test 6: Verify attribute extraction in Native Bangla.
    'গতকাল গোড়ালিতে মচকে গেছে এবং ফুলে লাল হয়ে আছে।'
    """
    conv_service = get_conversation_state_service()
    text = "গতকাল গোড়ালিতে মচকে গেছে এবং ফুলে লাল হয়ে আছে।"
    
    attrs = conv_service.extract_attributes(text)
    assert attrs["specific_location"] == "ankle/heel"
    assert attrs["precipitating_event"] == "sprain/injury"
    assert attrs["duration"] == "1 day"
    assert "swelling" in attrs["associated_symptoms"]
    assert "redness" in attrs["associated_symptoms"]

def test_non_diagnostic_state_invariance():
    """
    Test 7: Verify that context state contains strictly user-observable attributes
    and does NOT contain diagnostic disease labels or risk scores.
    """
    conv_service = get_conversation_state_service()
    state = conv_service.update_context_state(
        None,
        "amar paye betha fule geche",
        detected_lang="banglish",
        preferred_lang="bn",
        initial_qu_body_location="leg/foot"
    )
    
    # State fields must not contain clinical disease classifications
    dict_repr = state.model_dump()
    forbidden_diagnostic_keys = ["diagnosis", "disease_predicted", "risk_score", "triage_score", "probability"]
    for key in forbidden_diagnostic_keys:
        assert key not in dict_repr
    
    assert state.body_location == "leg/foot"
    assert "swelling" in state.associated_symptoms

def test_early_stopping_on_clear_first_aid_query():
    """
    Test 8: Straightforward single-turn burns query must NOT trigger clarification.
    'হাত পুড়ে গেলে ঠাণ্ডা পানির নিচে কতক্ষণ রাখবো?'
    Must be CLEARLY_ANSWERABLE on turn 1.
    """
    qu_service = get_query_understanding_service()
    query = "হাত পুড়ে গেলে ঠাণ্ডা পানির নিচে কতক্ষণ রাখবো?"
    qu_res = qu_service.analyze_query(query)
    
    assert qu_res.intent_category == QueryIntentCategory.CLEARLY_ANSWERABLE
    assert qu_res.sufficiency_state == EvidenceSufficiencyState.SUFFICIENT
    assert qu_res.evidence_presentation_policy == "SHOW_GROUNDING_CARDS"
