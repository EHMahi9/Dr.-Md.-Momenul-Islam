"""
Phase 8A: Deployment Readiness Test Suite
Verifies CORS, health endpoint, packaged corpus integrity, and production runtime behavior.
"""

import pytest
import os
import hashlib
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.schemas.api_models import RetrievalOutcomeState, ConversationAction, ConversationContextState

@pytest.fixture
def client():
    return TestClient(app)

def test_packaged_corpus_manifest_integrity():
    """Verify that backend/app/data/promoted_corpus_manifest.json exists and matches frozen SHA-256."""
    packaged_path = os.path.join(os.path.dirname(__file__), "..", "app", "data", "promoted_corpus_manifest.json")
    assert os.path.exists(packaged_path), f"Packaged corpus missing at: {packaged_path}"
    
    with open(packaged_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest().upper()
        
    expected_hash = "44D0602F730D6460E6FEFA431BD5C09005B48CE92B47D02832532E5868D4AA58"
    assert file_hash == expected_hash, f"Packaged corpus hash mismatch: {file_hash} != {expected_hash}"

def test_health_endpoint_contract(client):
    """Verify GET /api/v1/health returns truthful, un-hardcoded metadata."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    
    assert data["status"] == "healthy"
    assert data["active_corpus_chunks"] == 119
    assert data["staged_research_chunks"] == 0
    assert data["active_candidate"] == "CANDIDATE_B_CONTEXT_AWARE_DISAMBIGUATION"
    assert data["generation_enabled"] is False
    assert data["candidate_b_hash"] == "92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A"

def test_corpus_lifecycle_endpoint(client):
    """Verify GET /api/v1/corpus reports 14 active NHS documents and 119 chunks."""
    res = client.get("/api/v1/corpus")
    assert res.status_code == 200
    data = res.json()
    
    active = data["active_corpus"]
    assert active["name"] == "NHS_14_CONDITIONS"
    assert active["chunk_count"] == 119
    assert active["document_count"] == 14
    assert len(active["source_ids"]) == 14
    assert data["staged_research_corpus"]["chunk_count"] == 0

def test_cors_preflight_for_vercel_frontend(client):
    """Verify CORS preflight OPTIONS request for Vercel production frontend origin."""
    headers = {
        "Origin": "https://drmomenul.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type"
    }
    res = client.options("/api/v1/chat", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://drmomenul.vercel.app"
    assert "POST" in res.headers.get("access-control-allow-methods", "")

def test_cors_preflight_for_local_dev(client):
    """Verify CORS preflight OPTIONS request for local Vite frontend origin."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type"
    }
    res = client.options("/api/v1/chat", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"

def test_query_understanding_endpoint(client):
    """Verify POST /api/v1/query/understand processes multilingual queries."""
    payload = {"query": "amar paye betha ki korbo", "preferred_language": "auto"}
    res = client.post("/api/v1/query/understand", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "banglish"
    assert data["intent_category"] == "UNDERSPECIFIED_AMBIGUOUS"

def test_chat_endpoint_multilingual_flow(client):
    """Verify POST /api/v1/chat handles English, Bangla, and Banglish correctly."""
    # 1. English
    res_en = client.post("/api/v1/chat", json={"message": "What is the first aid for nosebleeds?"})
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert len(data_en["evidence"]) > 0
    assert any("DOC-NHS-016" in chunk["parent_source_id"] for chunk in data_en["evidence"])

    # 2. Native Bangla
    res_bn = client.post("/api/v1/chat", json={"message": "নাক দিয়ে রক্ত পড়লে কি করণীয়?"})
    assert res_bn.status_code == 200
    data_bn = res_bn.json()
    assert len(data_bn["evidence"]) > 0

    # 3. Standard Banglish
    res_bg = client.post("/api/v1/chat", json={"message": "amar nak diye rokto porche ki korbo"})
    assert res_bg.status_code == 200
    data_bg = res_bg.json()
    assert len(data_bg["evidence"]) > 0

def test_chat_emergency_routing(client):
    """Verify emergency red flag queries route to EMERGENCY action."""
    payload = {"message": "Severe crushing chest pain and difficulty breathing"}
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["next_action"] == "EMERGENCY"

def test_chat_unsupported_out_of_corpus(client):
    """Verify unsupported out-of-corpus query behavior in both single-turn and multi-turn state."""
    # 1. Single-turn low confidence / unsupported
    payload = {"message": "amar pa mochkay geche gorali fule geche"}
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["outcome_state"] in ("NO_RELEVANT_EVIDENCE", "UNSUPPORTED_BY_ACTIVE_CORPUS", "POSSIBLE_MISMATCH")

    # 2. Multi-turn clarification stopping on out-of-corpus sprain
    ctx = {
        "turn_count": 1,
        "asked_questions": ["sub_location"],
        "body_location": "leg",
        "specific_location": "ankle"
    }
    payload_turn2 = {
        "message": "gorali mochkay geche",
        "context_state": ctx
    }
    res2 = client.post("/api/v1/chat", json=payload_turn2)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["next_action"] in ("ABSTAIN", "CLARIFY")
