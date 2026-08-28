"""
Live integration test executing the frozen Strategy 5 models end-to-end.
"""

import pytest
from app.services.retrieval_service import FrozenDualAnchorRetrievalService

@pytest.fixture(scope="module")
def real_service():
    return FrozenDualAnchorRetrievalService()

def test_real_retrieval_english(real_service):
    norm_q, evidence = real_service.retrieve("how to treat a burn with cool running water", top_k=5)
    assert len(evidence) == 5
    assert evidence[0].rank == 1
    assert "DOC-NHS-005" in evidence[0].parent_source_id
    assert evidence[0].rerank_score is not None

def test_real_retrieval_bangla(real_service):
    norm_q, evidence = real_service.retrieve("হাত পুড়ে গেলে কী করব?", top_k=5)
    assert len(evidence) == 5
    sids = [e.parent_source_id for e in evidence]
    assert any("DOC-NHS-005" in s for s in sids)

def test_real_retrieval_banglish(real_service):
    norm_q, evidence = real_service.retrieve("kete geche bleeding tham tase na ki prothom shongshop korbo?", top_k=5)
    assert len(evidence) == 5
    sids = [e.parent_source_id for e in evidence]
    assert any("DOC-NHS-006" in s for s in sids)
