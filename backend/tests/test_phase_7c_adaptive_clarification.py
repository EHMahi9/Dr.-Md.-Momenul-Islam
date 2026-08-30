"""
Phase 7C Adaptive Clarification & Conversation Quality Test Suite.
Tests:
1. Question-Utility Model scoring & explainability
2. Duplicate question prevention via asked_questions tracking
3. Free-text attribute extraction (Bangla, English, Banglish)
4. Out-of-corpus early stopping (Sprains/Strains)
5. Sufficient evidence early stopping (Cuts, Burns, Insect bites)
6. Hard turn limit (MAX=3) enforcement
7. Emergency safety-first override
8. Unnecessary clarification traps (zero redundant questions)
9. Multilingual quick-select options
10. Non-diagnostic invariance
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.api_models import (
    ConversationContextState,
    ConversationAction,
    ClarificationState,
    EvidenceSufficiencyState,
    RetrievedEvidenceChunk
)
from app.services.conversation_state_service import (
    get_conversation_state_service,
    QuestionCandidate
)

@pytest.fixture
def conv_service():
    return get_conversation_state_service()

@pytest.fixture
def client():
    return TestClient(app)


def test_question_utility_scoring(conv_service):
    """Test utility calculation, redundancy penalties, and confidence adjustments."""
    state = ConversationContextState(
        session_id="test-session",
        body_location="leg/foot",
        symptom="pain"
    )

    q = QuestionCandidate(
        field="precipitating_event",
        retrieval_gain=0.45,
        safety_gain=0.20,
        ambiguity_reduction=0.30,
        corpus_relevance=0.35,
        question_en="What happened?",
        question_bn="কী হয়েছিল?",
        options_en=["Cut", "Burn"],
        options_bn=["কাটা", "পোড়া"],
        rationale="Disambiguation"
    )

    # Clean state -> positive utility
    score = q.compute_utility(state)
    assert score > 1.0

    # If field is already in asked_questions -> penalty (-1.0)
    state.asked_questions.append("precipitating_event")
    assert q.compute_utility(state) == -1.0


def test_duplicate_question_prevention(conv_service):
    """Ensure that asked questions are never repeated in multi-turn sessions."""
    state = ConversationContextState(
        session_id="test-session",
        body_location="leg/foot",
        symptom="pain"
    )

    # First question planning
    q1 = conv_service.plan_clarification_question(state, preferred_lang="bn")
    assert q1 is not None
    field1 = q1.field_to_clarify
    assert field1 in state.asked_questions

    # Second question planning
    q2 = conv_service.plan_clarification_question(state, preferred_lang="bn")
    if q2:
        field2 = q2.field_to_clarify
        assert field2 != field1
        assert field2 in state.asked_questions


def test_free_text_attribute_extraction(conv_service):
    """Verify attribute extraction from free-text user answers."""
    # 1. Location extraction
    ext1 = conv_service.extract_attributes("gorar kache betha hocche")
    assert ext1["specific_location"] == "ankle/heel"

    # 2. Mechanism extraction
    ext2 = conv_service.extract_attributes("churi diye kete geche, rokto porche")
    assert ext2["precipitating_event"] == "cut/wound"

    # 3. Burn extraction
    ext3 = conv_service.extract_attributes("gorom tel pore pure geche")
    assert ext3["precipitating_event"] == "thermal_burn"

    # 4. No trauma extraction
    ext4 = conv_service.extract_attributes("pore jai nai, emnitei betha")
    assert ext4["precipitating_event"] == "spontaneous / no injury"
    assert "no trauma / injury reported" in ext4["relevant_negatives"]

    # 5. Age extraction
    ext5 = conv_service.extract_attributes("3 bochorer bacchar jor")
    assert ext5["user_age_group"] == "child"


def test_early_stopping_on_out_of_corpus_sprain(client):
    """Verify that user reporting a sprain stops questioning immediately with ABSTAIN."""
    # Turn 1
    r1 = client.post("/api/v1/chat", json={"message": "amar paye betha", "preferred_language": "bn"})
    d1 = r1.json()
    assert d1["next_action"] == "CLARIFY"
    assert d1["clarification_state"] == "IN_PROGRESS"

    # Turn 2: User responds with sprain / fall
    r2 = client.post("/api/v1/chat", json={
        "message": "pore giyechilam, moshke geche",
        "preferred_language": "bn",
        "context_state": d1["context_state"],
        "session_id": d1["session_id"]
    })
    d2 = r2.json()
    assert d2["next_action"] == "ABSTAIN"
    assert d2["clarification_state"] == "UNSUPPORTED_TOPIC"
    assert d2["evidence_presentation_policy"] == "SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION"


def test_early_stopping_on_sufficient_evidence(client):
    """Verify that user clarifying cut & bleeding immediately resolves to ANSWER."""
    # Turn 1
    r1 = client.post("/api/v1/chat", json={"message": "amar paye betha", "preferred_language": "bn"})
    d1 = r1.json()
    assert d1["next_action"] == "CLARIFY"

    # Turn 2: User responds with cut & bleeding
    r2 = client.post("/api/v1/chat", json={
        "message": "kete geche, rokto porche",
        "preferred_language": "bn",
        "context_state": d1["context_state"],
        "session_id": d1["session_id"]
    })
    d2 = r2.json()
    assert d2["next_action"] == "ANSWER"
    assert d2["clarification_state"] == "RESOLVED"
    assert d2["evidence_presentation_policy"] == "SHOW_GROUNDING_CARDS"
    assert len(d2["evidence"]) > 0
    assert d2["evidence"][0]["parent_source_id"] == "DOC-NHS-006"


def test_hard_turn_limit_enforcement(conv_service):
    """Verify that maximum clarification turns (3) stops clarification and abstains."""
    state = ConversationContextState(
        session_id="test-session",
        clarification_turn_count=3,
        max_clarification_turns=3
    )

    q = conv_service.plan_clarification_question(state, preferred_lang="bn")
    assert q is None
    assert state.clarification_state == ClarificationState.MAX_TURNS_EXCEEDED
    assert state.next_action == ConversationAction.ABSTAIN


def test_emergency_override_bypasses_clarification(client):
    """Verify that emergency symptoms route immediately to EMERGENCY."""
    resp = client.post("/api/v1/chat", json={
        "message": "amar buke prochondo betha ar shash nite koshto hocche",
        "preferred_language": "bn"
    })
    data = resp.json()
    assert data["next_action"] == "EMERGENCY"
    assert data["clarification_state"] == "NOT_NEEDED"
    assert data["evidence_presentation_policy"] == "SHOW_EMERGENCY_OVERRIDE"
    assert data["query_understanding"]["is_emergency"] is True


def test_unnecessary_clarification_trap_queries(client):
    """Verify that fully-specified first aid queries never trigger clarification."""
    queries = [
        "হাত পুড়ে গেলে ঠাণ্ডা পানিতে কতক্ষণ রাখবো?",
        "nak diye rokt porle ki korbo?",
        "How to treat a minor cut on my finger?",
        "What should I do if a bee stings my arm?"
    ]
    for q in queries:
        resp = client.post("/api/v1/chat", json={"message": q, "preferred_language": "auto"})
        data = resp.json()
        assert data["next_action"] == "ANSWER"
        assert data["clarification_state"] == "NOT_NEEDED"
        assert data["evidence_presentation_policy"] == "SHOW_GROUNDING_CARDS"


def test_multilingual_consistency_and_options(conv_service):
    """Verify Bengali vs English quick options generation."""
    state_bn = ConversationContextState(session_id="bn-sess", language_modality="bn")
    q_bn = conv_service.plan_clarification_question(state_bn, preferred_lang="bn")
    assert q_bn is not None
    assert any("কেটে" in opt or "আঘাত" in opt or "পুড়ে" in opt for opt in q_bn.options)

    state_en = ConversationContextState(session_id="en-sess", language_modality="en")
    q_en = conv_service.plan_clarification_question(state_en, preferred_lang="en")
    assert q_en is not None
    assert any("Cut" in opt or "Sprain" in opt or "Burn" in opt for opt in q_en.options)


def test_non_diagnostic_invariance(client):
    """Verify zero diagnostic assertions, probability labels, or prescriptions."""
    resp = client.post("/api/v1/chat", json={"message": "amar paye betha, ki korbo?", "preferred_language": "bn"})
    data = resp.json()
    qu = data.get("query_understanding", {})
    cq = qu.get("clarification_question", {})
    
    # Check that question text does not claim a diagnosis
    for forbidden in ["arthritis", "gout", "sciatica", "you have", "you probably have", "আপনার নিশ্চিত", "হয়েছে"]:
        if cq and cq.get("question_text_en"):
            assert forbidden not in cq["question_text_en"].lower()
