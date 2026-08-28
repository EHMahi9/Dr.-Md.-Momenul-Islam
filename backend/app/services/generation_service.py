"""
Abstract Generation Service with LLM Generation explicitly disabled.
In Phase 6A, responses return retrieved evidence and research notices only.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.api_models import RetrievedEvidenceChunk

class BaseGenerationService(ABC):
    """Abstract interface for generation layer."""
    
    @abstractmethod
    def generate_response(self, query: str, evidence: List[RetrievedEvidenceChunk]) -> Dict[str, Any]:
        """Generate response grounded on evidence."""
        pass
        
    @abstractmethod
    def is_generation_enabled(self) -> bool:
        """Return whether LLM generation is active."""
        pass

class DisabledGenerationService(BaseGenerationService):
    """
    Phase 6A implementation: LLM generation is strictly disabled.
    Returns structured grounding metadata without external model inference.
    """
    
    def is_generation_enabled(self) -> bool:
        return False
        
    def generate_response(self, query: str, evidence: List[RetrievedEvidenceChunk]) -> Dict[str, Any]:
        return {
            "generation_enabled": False,
            "status": "research_prototype",
            "synthetic_answer": (
                "[RESEARCH PROTOTYPE MODE: LLM generation is currently disabled by research protocol. "
                "The authoritative NHS evidence passages retrieved below represent the grounding context for this query.]"
            ),
            "evidence_count": len(evidence),
            "top_source_title": evidence[0].source_title if evidence else "None",
            "disclaimer": "Research Prototype — Not for Medical Decision-Making."
        }

_generation_service_instance = None

def get_generation_service() -> BaseGenerationService:
    global _generation_service_instance
    if _generation_service_instance is None:
        _generation_service_instance = DisabledGenerationService()
    return _generation_service_instance
