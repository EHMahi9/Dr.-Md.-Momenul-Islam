"""
Automated unit and integration tests for FastAPI backend prototype.
Uses FastAPI dependency overrides for fast, deterministic unit test execution.
"""

import os
import sys
import pytest
from typing import List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.schemas.api_models import RetrievedEvidenceChunk
from app.services.retrieval_service import BaseRetrievalService, get_retrieval_service

class MockFrozenDualAnchorRetrievalService(BaseRetrievalService):
    def get_strategy_name(self) -> str:
        return "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR"
        
    def get_chunk_count(self) -> int:
        return 68
        
    def retrieve(self, query: str, top_k: int = 5) -> Tuple[str, List[RetrievedEvidenceChunk]]:
        norm_query = f"{query} (normalized)"
        evidence = [
            RetrievedEvidenceChunk(
                rank=1,
                chunk_id="DOC-NHS-005-HYB-001",
                parent_source_id="DOC-NHS-005",
                source_title="Burns and scalds",
                source_url="https://www.nhs.uk/conditions/burns-and-scalds/",
                text="Cool the burn immediately with cool or lukewarm running water for 20 to 30 minutes.",
                rerank_score=0.8950,
                raw_dense_score=0.8200,
                lexical_overlap=0.4500
            ),
            RetrievedEvidenceChunk(
                rank=2,
                chunk_id="DOC-NHS-005-HYB-002",
                parent_source_id="DOC-NHS-005",
                source_title="Burns and scalds",
                source_url="https://www.nhs.uk/conditions/burns-and-scalds/",
                text="Remove clothing or jewellery near the burnt area of skin, unless it is stuck to the skin.",
                rerank_score=0.8420,
                raw_dense_score=0.7900,
                lexical_overlap=0.3000
            ),
            RetrievedEvidenceChunk(
                rank=3,
                chunk_id="DOC-NHS-006-HYB-001",
                parent_source_id="DOC-NHS-006",
                source_title="Cuts and grazes",
                source_url="https://www.nhs.uk/conditions/cuts-and-grazes/",
                text="Apply direct pressure to the wound using a clean dressing or bandage to stop bleeding.",
                rerank_score=0.8100,
                raw_dense_score=0.7600,
                lexical_overlap=0.2500
            ),
            RetrievedEvidenceChunk(
                rank=4,
                chunk_id="DOC-NHS-010-HYB-001",
                parent_source_id="DOC-NHS-010",
                source_title="High temperature (fever) in children",
                source_url="https://www.nhs.uk/conditions/fever-in-children/",
                text="A high temperature in children is 38C or above. Check temperature with a thermometer.",
                rerank_score=0.7800,
                raw_dense_score=0.7200,
                lexical_overlap=0.2000
            ),
            RetrievedEvidenceChunk(
                rank=5,
                chunk_id="DOC-NHS-011-HYB-001",
                parent_source_id="DOC-NHS-011",
                source_title="Anaphylaxis",
                source_url="https://www.nhs.uk/conditions/anaphylaxis/",
                text="Use an adrenaline auto-injector immediately if you suspect anaphylaxis and call 999.",
                rerank_score=0.7500,
                raw_dense_score=0.7000,
                lexical_overlap=0.1500
            )
        ]
        return norm_query, evidence[:top_k]

# Inject mock for test suite
app.dependency_overrides[get_retrieval_service] = lambda: MockFrozenDualAnchorRetrievalService()

client = TestClient(app)

def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "Dr. Md. Momenul Islam" in data["project"]
    assert data["docs"] == "/docs"

def test_health_endpoint():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["retrieval_strategy"] == "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR"
    assert data["candidate_hash"] == "07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736"
    assert data["active_corpus_chunks"] == 68
    assert data["staged_research_chunks"] == 51
    assert data["generation_enabled"] is False

def test_corpus_lifecycle_endpoint():
    resp = client.get("/api/v1/corpus")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    
    # Check Active Tier
    active = data["active_corpus"]
    assert active["name"] == "BASELINE_NHS_8_CONDITIONS"
    assert active["status"] == "ACTIVE"
    assert active["document_count"] == 8
    assert active["chunk_count"] == 68
    assert len(active["source_ids"]) == 8
    assert "DOC-NHS-004" in active["source_ids"]
    assert "DOC-NHS-011" in active["source_ids"]
    
    # Check Staged Tier
    staged = data["staged_research_corpus"]
    assert staged["name"] == "EXPANDED_NHS_6_CONDITIONS"
    assert staged["status"] == "STAGED_RESEARCH"
    assert staged["document_count"] == 6
    assert staged["chunk_count"] == 51
    assert "DOC-NHS-012" in staged["source_ids"]
    assert "DOC-NHS-017" in staged["source_ids"]
    
    # Check Validated Tier
    validated = data["validated_corpus"]
    assert validated["status"] == "NOT_ACTIVE"
    assert validated["chunk_count"] == 0
    
    # Check Retrieval Candidate
    cand = data["retrieval_candidate"]
    assert cand["strategy_name"] == "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR"
    assert cand["frozen_candidate_sha256"] == "07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736"

def test_staged_corpus_isolation_in_retrieval():
    """Verify that staged research sources (DOC-NHS-012..017) are never returned in active retrieval."""
    resp = client.post("/api/v1/retrieve", json={"query": "chest pain stroke sepsis meningitis", "top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    staged_sids = {"DOC-NHS-012", "DOC-NHS-013", "DOC-NHS-014", "DOC-NHS-015", "DOC-NHS-016", "DOC-NHS-017"}
    retrieved_sids = set(e["parent_source_id"] for e in data["evidence"])
    # Staged documents must have zero intersection with active retrieval output
    assert retrieved_sids.isdisjoint(staged_sids)

def test_retrieve_english_query():
    resp = client.post("/api/v1/retrieve", json={"query": "how to treat a minor burn with water", "top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["evidence_count"] == 5
    assert len(data["evidence"]) == 5
    
    top_chunk = data["evidence"][0]
    assert top_chunk["rank"] == 1
    assert "DOC-NHS-005" in top_chunk["parent_source_id"]
    assert "Burns and scalds" in top_chunk["source_title"]
    assert top_chunk["rerank_score"] is not None
    assert "Open Government Licence" in top_chunk["provenance_clause"]

def test_retrieve_bangla_query():
    resp = client.post("/api/v1/retrieve", json={"query": "হাত পুড়ে গেলে কী প্রাথমিক চিকিৎসা নেব?", "top_k": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data["evidence_count"] == 3
    assert "DOC-NHS-005" in data["evidence"][0]["parent_source_id"]

def test_retrieve_banglish_query():
    resp = client.post("/api/v1/retrieve", json={"query": "pora jaygay cold water dhalbo koto time?", "top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["evidence_count"] == 5
    retrieved_sids = [e["parent_source_id"] for e in data["evidence"]]
    assert any("DOC-NHS-005" in sid for sid in retrieved_sids)

def test_retrieve_empty_query_error():
    resp = client.post("/api/v1/retrieve", json={"query": "   ", "top_k": 5})
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()

def test_chat_endpoint_generation_disabled():
    resp = client.post("/api/v1/chat", json={"message": "What should I do if my child has a fever?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "research_prototype"
    assert data["generation_enabled"] is False
    assert "disabled" in data["synthetic_answer"].lower()
    assert data["evidence_count"] > 0
    assert len(data["evidence"]) == 5
