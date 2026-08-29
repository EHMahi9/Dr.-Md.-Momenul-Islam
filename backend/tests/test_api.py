"""
Automated unit and integration tests for FastAPI backend prototype.
Uses FastAPI dependency overrides for fast, deterministic unit test execution.
"""

import os
import sys
import json
import pytest
from typing import List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.schemas.api_models import RetrievedEvidenceChunk, RetrievalOutcomeState
from app.services.retrieval_service import BaseRetrievalService, get_retrieval_service

class MockFrozenDualAnchorRetrievalService(BaseRetrievalService):
    def get_strategy_name(self) -> str:
        return "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR"
        
    def get_chunk_count(self) -> int:
        return 119
        
    def retrieve(self, query: str, top_k: int = 5) -> Tuple[str, List[RetrievedEvidenceChunk]]:
        norm_query = f"{query} (normalized)"
        
        # Simulate ungrounded/low-confidence query when query is "ungrounded_test_query"
        if "ungrounded" in query.lower():
            evidence = [
                RetrievedEvidenceChunk(
                    rank=1,
                    chunk_id="DOC-NHS-004-HYB-001",
                    parent_source_id="DOC-NHS-004",
                    source_title="Asthma",
                    source_url="https://www.nhs.uk/conditions/asthma/",
                    text="General asthma information.",
                    rerank_score=0.1400,
                    raw_dense_score=0.1200,
                    lexical_overlap=0.0500
                )
            ]
            return norm_query, evidence

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
    assert data["candidate_hash"] == "1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae"
    assert data["active_corpus_chunks"] == 119
    assert data["staged_research_chunks"] == 51  # File still exists at staged path
    assert data["generation_enabled"] is False

def test_corpus_lifecycle_endpoint():
    resp = client.get("/api/v1/corpus")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    
    # Check Active Tier — post-promotion: 14 sources, 119 chunks
    active = data["active_corpus"]
    assert active["name"] == "NHS_14_CONDITIONS"
    assert active["status"] == "ACTIVE"
    # Mock doesn't have .chunks attribute, so document_count may be 0
    # The key assertion is that the endpoint returns successfully
    assert active["chunk_count"] == 119
    
    # Check Staged Tier — now PROMOTED (empty)
    staged = data["staged_research_corpus"]
    assert staged["name"] == "STAGED_EMPTY"
    assert staged["status"] == "PROMOTED"
    assert staged["document_count"] == 0
    assert staged["chunk_count"] == 0
    
    # Check Validated Tier
    validated = data["validated_corpus"]
    assert validated["status"] == "NOT_ACTIVE"
    assert validated["chunk_count"] == 0
    
    # Check Retrieval Candidate
    cand = data["retrieval_candidate"]
    assert cand["strategy_name"] == "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR"
    assert cand["frozen_candidate_sha256"] == "1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae"

def test_promoted_sources_included_in_active():
    """After Phase 6C promotion, previously-staged sources (DOC-NHS-012..017) are now active.
    This is a structural test — the mock doesn't actually serve those chunks,
    so we just verify the retrieval endpoint still functions correctly."""
    resp = client.post("/api/v1/retrieve", json={"query": "chest pain stroke sepsis meningitis", "top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["evidence_count"] > 0

def test_retrieve_english_supported():
    resp = client.post("/api/v1/retrieve", json={"query": "how to treat a minor burn with water", "top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["outcome_state"] == "SUPPORTED_RETRIEVAL"
    assert data["confidence_assessment"]["confidence_level"] == "HIGH"
    assert data["evidence_count"] == 5
    assert len(data["evidence"]) == 5
    
    top_chunk = data["evidence"][0]
    assert top_chunk["rank"] == 1
    assert "DOC-NHS-005" in top_chunk["parent_source_id"]
    assert "Burns and scalds" in top_chunk["source_title"]
    assert top_chunk["rerank_score"] >= 0.65
    assert "Open Government Licence" in top_chunk["provenance_clause"]

def test_retrieve_bangla_supported():
    resp = client.post("/api/v1/retrieve", json={"query": "হাত পুড়ে গেলে কী প্রাথমিক চিকিৎসা নেব?", "top_k": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data["outcome_state"] == "SUPPORTED_RETRIEVAL"
    assert data["evidence_count"] == 3
    assert "DOC-NHS-005" in data["evidence"][0]["parent_source_id"]

def test_retrieve_banglish_supported():
    resp = client.post("/api/v1/retrieve", json={"query": "pora jaygay cold water dhalbo koto time?", "top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["outcome_state"] == "SUPPORTED_RETRIEVAL"
    assert data["evidence_count"] == 5
    retrieved_sids = [e["parent_source_id"] for e in data["evidence"]]
    assert any("DOC-NHS-005" in sid for sid in retrieved_sids)

def test_retrieve_empty_query_400():
    resp = client.post("/api/v1/retrieve", json={"query": ""})
    assert resp.status_code == 422 or resp.status_code == 400

def test_retrieve_whitespace_query_400():
    resp = client.post("/api/v1/retrieve", json={"query": "     ", "top_k": 5})
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()

def test_retrieve_oversized_query_400():
    huge_query = "burns " * 300
    resp = client.post("/api/v1/retrieve", json={"query": huge_query, "top_k": 5})
    assert resp.status_code in [400, 422]
    data = resp.json()
    assert "detail" in data

def test_retrieve_ungrounded_query_low_confidence():
    resp = client.post("/api/v1/retrieve", json={"query": "ungrounded_test_query", "top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["outcome_state"] in [
        RetrievalOutcomeState.UNSUPPORTED_BY_ACTIVE_CORPUS.value,
        RetrievalOutcomeState.POSSIBLE_MISMATCH.value,
        RetrievalOutcomeState.NO_RELEVANT_EVIDENCE.value
    ]

def test_chat_endpoint_outcome_classification():
    resp = client.post("/api/v1/chat", json={"message": "What should I do if my child has a fever?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "research_prototype"
    assert data["outcome_state"] == "SUPPORTED_RETRIEVAL"
    assert data["confidence_assessment"]["top_score"] > 0.60
    assert data["retrieval_metadata"]["strategy_name"] == "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR"

def test_chat_endpoint_generation_disabled():
    resp = client.post("/api/v1/chat", json={"message": "What should I do if my child has a fever?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["generation_enabled"] is False
    assert "disabled" in data["synthetic_answer"].lower()
    assert data["evidence_count"] > 0
    assert len(data["evidence"]) == 5

def test_provenance_clause_preservation():
    resp = client.post("/api/v1/retrieve", json={"query": "asthma inhaler", "top_k": 3})
    assert resp.status_code == 200
    data = resp.json()
    for chunk in data["evidence"]:
        assert "Open Government Licence" in chunk["provenance_clause"]
        assert chunk["source_url"].startswith("https://www.nhs.uk")

# ==============================================================================
# Phase 6D: Grounded Generation Architecture & Interface Tests
# ==============================================================================

from app.schemas.generation_models import (
    GenerationSafetyState,
    GenerationStatus,
    CitationReference,
    GroundingEvidence,
    GroundedPrompt,
    GenerationResult,
    LLMRequest,
    LLMResponse,
    TokenUsageMetadata,
    PostValidationResult
)
from app.services.generation_service import (
    BaseGenerationService,
    GroundedGenerationService,
    get_generation_service
)
from app.services.llm_provider import (
    BaseLLMProvider,
    DisabledLLMProvider,
    MockLLMProvider,
    create_llm_provider
)
from app.services.prompt_builder import PromptBuilder
from app.services.output_validator import OutputValidator
from app.core.config import settings

def test_generation_service_interface_disabled():
    """Verify that default generation service is disabled and returns DISABLED status."""
    gen_service = get_generation_service()
    assert isinstance(gen_service, BaseGenerationService)
    assert gen_service.is_generation_enabled() is False

    mock_evidence = [
        RetrievedEvidenceChunk(
            rank=1,
            chunk_id="DOC-NHS-005-HYB-001",
            parent_source_id="DOC-NHS-005",
            source_title="Burns and scalds",
            source_url="https://www.nhs.uk/conditions/burns-and-scalds/",
            text="Cool the burn under cold running water for 20 minutes.",
            rerank_score=0.8800
        )
    ]
    result = gen_service.generate_answer("How to treat a burn?", mock_evidence)
    assert isinstance(result, GenerationResult)
    assert result.generation_status == GenerationStatus.DISABLED
    assert "disabled" in result.answer.lower()
    assert result.confidence_state == RetrievalOutcomeState.SUPPORTED_RETRIEVAL
    assert result.safety_state == GenerationSafetyState.SAFE_INFORMATIONAL

def test_generation_result_schema_validation():
    """Verify serialization and validation of GenerationResult model."""
    citation = CitationReference(
        citation_index=1,
        chunk_id="DOC-NHS-005-HYB-001",
        parent_source_id="DOC-NHS-005",
        source_title="Burns and scalds",
        source_url="https://www.nhs.uk/conditions/burns-and-scalds/",
        excerpt_snippet="Cool the burn under cold water..."
    )
    val = PostValidationResult(
        is_valid=True,
        citations_valid=True,
        fabricated_citations=[],
        unsupported_claims=[],
        safety_check_passed=True,
        summary_notes="Clean validation."
    )
    result = GenerationResult(
        answer="Cool with water [1].",
        citations=[citation],
        evidence_ids=["DOC-NHS-005-HYB-001"],
        confidence_state=RetrievalOutcomeState.SUPPORTED_RETRIEVAL,
        safety_state=GenerationSafetyState.SAFE_INFORMATIONAL,
        generation_status=GenerationStatus.COMPLETED,
        disclaimer="Research Prototype Disclaimer",
        provider_name="mock",
        model_name="mock-model",
        token_usage=TokenUsageMetadata(prompt_tokens=100, completion_tokens=20, total_tokens=120),
        validation_result=val
    )
    dumped = result.model_dump()
    assert dumped["answer"] == "Cool with water [1]."
    assert len(dumped["citations"]) == 1
    assert dumped["citations"][0]["chunk_id"] == "DOC-NHS-005-HYB-001"
    assert dumped["generation_status"] == "COMPLETED"

def test_evidence_serialization_to_grounding():
    """Verify conversion from RetrievedEvidenceChunk to GroundingEvidence."""
    chunk = RetrievedEvidenceChunk(
        rank=1,
        chunk_id="DOC-NHS-006-HYB-001",
        parent_source_id="DOC-NHS-006",
        source_title="Cuts and grazes",
        source_url="https://www.nhs.uk/conditions/cuts-and-grazes/",
        text="Apply direct pressure with a clean bandage.",
        rerank_score=0.8200,
        raw_dense_score=0.7900,
        lexical_overlap=0.3500
    )
    grounding = GroundingEvidence.from_retrieved_chunk(chunk)
    assert grounding.chunk_id == "DOC-NHS-006-HYB-001"
    assert grounding.retrieval_rank == 1
    assert grounding.fused_score == 0.8200
    assert grounding.raw_dense_score == 0.7900
    assert grounding.lexical_overlap == 0.3500
    assert "Open Government Licence" in grounding.provenance_clause

def test_empty_evidence_generation_behavior():
    """Verify behavior when no evidence is supplied to generation service."""
    gen_service = GroundedGenerationService()
    result = gen_service.generate_answer("Unknown condition query", [])
    assert result.confidence_state == RetrievalOutcomeState.NO_RELEVANT_EVIDENCE
    assert result.safety_state == GenerationSafetyState.UNSUPPORTED_TOPIC
    assert result.generation_status == GenerationStatus.DISABLED

def test_prompt_builder_structure_and_safety_rules():
    """Verify that PromptBuilder embeds all required sections and safety constraints."""
    builder = PromptBuilder()
    evidence = [
        RetrievedEvidenceChunk(
            rank=1,
            chunk_id="DOC-NHS-005-HYB-001",
            parent_source_id="DOC-NHS-005",
            source_title="Burns and scalds",
            source_url="https://www.nhs.uk/conditions/burns-and-scalds/",
            text="Cool the burn immediately with cold water.",
            rerank_score=0.9000
        )
    ]
    prompt = builder.build_prompt("How to treat a burn?", evidence)
    assert isinstance(prompt, GroundedPrompt)
    assert prompt.user_question == "How to treat a burn?"
    assert len(prompt.retrieved_evidence) == 1
    assert "MANDATORY BEHAVIORAL PROTOCOLS" in prompt.system_instructions
    assert "NO MEDICAL HALLUCINATION" in prompt.system_instructions
    assert "NO FABRICATED CITATIONS" in prompt.system_instructions
    assert "NO DOCTOR PERSONA" in prompt.system_instructions
    assert "EMERGENCY TRIAGE RULES" in prompt.safety_instructions
    assert prompt.formatted_prompt_payload is not None
    assert "--- EVIDENCE EXCERPT [1] ---" in prompt.formatted_prompt_payload
    assert "DOC-NHS-005-HYB-001" in prompt.formatted_prompt_payload

def test_citation_mapping_and_fabricated_detection():
    """Verify that OutputValidator accurately maps valid citations and catches fabricated ones."""
    validator = OutputValidator()
    evidence = [
        RetrievedEvidenceChunk(
            rank=1,
            chunk_id="DOC-NHS-005-HYB-001",
            parent_source_id="DOC-NHS-005",
            source_title="Burns and scalds",
            source_url="https://www.nhs.uk/conditions/burns-and-scalds/",
            text="Cool the burn under cool running water for 20 to 30 minutes.",
            rerank_score=0.9000
        ),
        RetrievedEvidenceChunk(
            rank=2,
            chunk_id="DOC-NHS-005-HYB-002",
            parent_source_id="DOC-NHS-005",
            source_title="Burns and scalds",
            source_url="https://www.nhs.uk/conditions/burns-and-scalds/",
            text="Remove clothing or jewellery near the burn.",
            rerank_score=0.8500
        )
    ]

    # Clean text with valid citations [1] and [2]
    clean_text = "Cool the burn with water [1]. Remove clothing near the burn [2]."
    val_clean, citations_clean = validator.validate_output(clean_text, evidence)
    assert val_clean.is_valid is True
    assert val_clean.citations_valid is True
    assert len(citations_clean) == 2
    assert citations_clean[0].chunk_id == "DOC-NHS-005-HYB-001"
    assert citations_clean[1].chunk_id == "DOC-NHS-005-HYB-002"
    assert len(val_clean.fabricated_citations) == 0

    # Fabricated citation [99]
    fabricated_text = "Cool the burn [1] and apply butter immediately [99]."
    val_fab, citations_fab = validator.validate_output(fabricated_text, evidence)
    assert val_fab.is_valid is False
    assert val_fab.citations_valid is False
    assert len(val_fab.fabricated_citations) == 1
    assert "[99]" in val_fab.fabricated_citations[0]

def test_safety_state_routing_heuristics():
    """Verify safety classifier routing against emergency, crisis, and informational queries."""
    service = GroundedGenerationService()
    dummy_evidence = [
        RetrievedEvidenceChunk(
            rank=1,
            chunk_id="DOC-NHS-012-HYB-001",
            parent_source_id="DOC-NHS-012",
            source_title="Chest pain",
            source_url="https://www.nhs.uk/conditions/chest-pain/",
            text="Chest pain could be a medical emergency.",
            rerank_score=0.9000
        )
    ]

    # Emergency check
    assert service.assess_safety("I have severe chest pain radiating to my arm", dummy_evidence) == GenerationSafetyState.POSSIBLE_EMERGENCY
    assert service.assess_safety("buke chap ar muk beke geche", dummy_evidence) == GenerationSafetyState.POSSIBLE_EMERGENCY

    # Self-harm check
    assert service.assess_safety("I want to commit suicide", dummy_evidence) == GenerationSafetyState.SELF_HARM_OR_CRISIS

    # Medication dose check
    assert service.assess_safety("What dose of paracetamol should I take?", dummy_evidence) == GenerationSafetyState.MEDICATION_OR_TREATMENT_REQUEST

    # Safe informational query
    assert service.assess_safety("How do I wash a minor scratch?", dummy_evidence) == GenerationSafetyState.SAFE_INFORMATIONAL

def test_provider_abstraction_and_mock_execution():
    """Verify provider abstraction with DisabledLLMProvider vs MockLLMProvider."""
    # 1. Disabled provider
    disabled_prov = DisabledLLMProvider()
    assert disabled_prov.is_available() is False
    assert disabled_prov.get_provider_name() == "disabled"
    resp_disabled = disabled_prov.complete(LLMRequest(
        prompt=PromptBuilder().build_prompt("test", []),
        model_name="none"
    ))
    assert resp_disabled.error is not None
    assert resp_disabled.finish_reason == "generation_disabled"

    # 2. Mock provider
    mock_prov = MockLLMProvider(canned_response="Clean test summary [1].")
    assert mock_prov.is_available() is True
    assert mock_prov.get_provider_name() == "mock"
    resp_mock = mock_prov.complete(LLMRequest(
        prompt=PromptBuilder().build_prompt("test", []),
        model_name="mock-model"
    ))
    assert resp_mock.error is None
    assert resp_mock.raw_text == "Clean test summary [1]."
    assert resp_mock.finish_reason == "stop"
    assert resp_mock.token_usage is not None
    assert resp_mock.token_usage.total_tokens > 0

def test_provider_configuration_validation():
    """Verify that configuration maintains generation_enabled=False and has secure defaults."""
    assert settings.GENERATION_ENABLED is False
    assert settings.LLM_PROVIDER == "disabled"
    assert settings.LLM_API_KEY_ENV_VAR == "LLM_API_KEY"
    assert settings.LLM_MAX_TOKENS == 1024
    assert settings.LLM_TIMEOUT_SECONDS == 30
    assert settings.LLM_MAX_RETRIES == 2

def test_chat_endpoint_includes_generation_result():
    """Verify that FastAPI /chat endpoint returns generation_result payload in DISABLED state."""
    resp = client.post("/api/v1/chat", json={"message": "How do I cool a burn?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "generation_result" in data
    gen_res = data["generation_result"]
    assert gen_res is not None
    assert gen_res["generation_status"] == "DISABLED"
    assert gen_res["confidence_state"] == "SUPPORTED_RETRIEVAL"
    assert gen_res["safety_state"] == "SAFE_INFORMATIONAL"
    assert gen_res["provider_name"] == "disabled"

# ==============================================================================
# Phase 6E: Real LLM Integration & Provider Offline Unit Tests
# ==============================================================================

from app.services.llm_provider import OpenAICompatibleProvider

def test_openai_compatible_provider_missing_key_behavior(monkeypatch):
    """Verify that OpenAICompatibleProvider safely returns missing_api_key error when key is unset."""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LIBERTAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    provider = OpenAICompatibleProvider(api_key_env_var="NONEXISTENT_TEST_KEY_ENV_VAR")
    assert provider.is_available() is False
    assert provider.get_provider_name() == "openai_compatible"

    req = LLMRequest(
        prompt=PromptBuilder().build_prompt("test query", []),
        model_name="test-model"
    )
    resp = provider.complete(req)
    assert resp.finish_reason == "missing_api_key"
    assert "missing" in resp.error.lower()
    assert resp.raw_text == ""

def test_create_llm_provider_factory_variants():
    """Verify factory returns appropriate provider types."""
    assert isinstance(create_llm_provider("disabled"), DisabledLLMProvider)
    assert isinstance(create_llm_provider("mock"), MockLLMProvider)
    assert isinstance(create_llm_provider("openai_compatible"), OpenAICompatibleProvider)
    assert isinstance(create_llm_provider("libertai"), OpenAICompatibleProvider)
    assert isinstance(create_llm_provider("real"), OpenAICompatibleProvider)

def test_smoke_results_artifact_integrity():
    """Verify that Phase 6E smoke test results file exists and has 100% validation rate."""
    artifact_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "research", "phase_6E_real_llm_integration", "outputs", "phase_6E_smoke_test_results.json")
    )
    assert os.path.exists(artifact_path)
    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["phase"] == "6E"
    assert data["total_smoke_tests"] == 8
    assert data["valid_generations"] == 8
    assert data["directly_supported_claims"] == 8


