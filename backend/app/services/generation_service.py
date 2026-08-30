"""
Abstract Generation Service with LLM Generation explicitly disabled (Phase 6D).
Defines complete generation service abstraction, safety routing state transitions,
and provider orchestration.

In Phase 6D:
- generation_enabled remains FALSE by research protocol.
- No external LLM is called.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import re
import logging

from app.core.config import settings
from app.schemas.api_models import (
    RetrievedEvidenceChunk,
    RetrievalOutcomeState
)
from app.schemas.generation_models import (
    GenerationSafetyState,
    GenerationStatus,
    GenerationResult,
    GroundedPrompt,
    PostValidationResult,
    CitationReference,
    LLMRequest,
    LLMResponse
)
from app.services.llm_provider import (
    BaseLLMProvider,
    DisabledLLMProvider,
    create_llm_provider
)
from app.services.prompt_builder import PromptBuilder
from app.services.output_validator import OutputValidator

logger = logging.getLogger("dr_momenul_islam.generation_service")


class BaseGenerationService(ABC):
    """
    Abstract interface for grounded clinical generation layer.
    Supports future provider substitution and post-generation validation.
    """

    @abstractmethod
    def is_generation_enabled(self) -> bool:
        """Return whether LLM generation is active."""
        pass

    @abstractmethod
    def generate_response(
        self,
        query: str,
        evidence: List[RetrievedEvidenceChunk],
        preferred_language: str = "auto"
    ) -> Dict[str, Any]:
        """Legacy dictionary interface for ChatResponse compatibility."""
        pass

    @abstractmethod
    def generate_answer(
        self,
        query: str,
        evidence: List[RetrievedEvidenceChunk],
        context: Optional[Dict[str, Any]] = None,
        preferred_language: str = "auto"
    ) -> GenerationResult:
        """
        Primary generation pipeline interface:
        Assess safety -> Build prompt -> Invoke provider (if enabled) -> Validate output -> Return GenerationResult.
        """
        pass

    @abstractmethod
    def assess_safety(self, query: str, evidence: List[RetrievedEvidenceChunk]) -> GenerationSafetyState:
        """Assess query intent and safety category."""
        pass

    @abstractmethod
    def build_grounded_prompt(
        self,
        query: str,
        evidence: List[RetrievedEvidenceChunk],
        preferred_language: str = "auto"
    ) -> GroundedPrompt:
        """Compose structured grounded prompt contract."""
        pass

    @abstractmethod
    def validate_output(
        self,
        generated_text: str,
        evidence: List[RetrievedEvidenceChunk]
    ) -> Tuple[PostValidationResult, List[CitationReference]]:
        """Run post-generation validation checks."""
        pass


class GroundedGenerationService(BaseGenerationService):
    """
    Complete Generation Service implementation with safety routing, prompt building,
    and provider orchestration. Operates in DISABLED mode by default in Phase 6D.
    """

    # Heuristic safety keyword patterns (Architectural design awaiting formal clinical evaluation)
    EMERGENCY_PATTERNS = [
        r'\b(chest pain|heart attack|angina|buker? betha|buke chap|stroke|muk beke|sepsis|rokte bishakta|meningitis|rash glass test|anaphylaxis|shash bondho)\b',
        r'(বুকের ব্যথা|হার্ট অ্যাটাক|স্ট্রোক|মুখ বেঁকে যাওয়া|সেপসিস|মেনিঞ্জাইটিস|অ্যানাফাইলাক্সিস|শ্বাস বন্ধ)'
    ]
    SELF_HARM_PATTERNS = [
        r'\b(suicide|kill myself|end my life|atmohotta|bish kheye|morbo)\b',
        r'(আত্মহত্যা|বিষ খেয়ে|মরে যাব)'
    ]
    DIAGNOSIS_PATTERNS = [
        r'\b(do i have|diagnose me|amar ki hoyese|ki rog)\b',
        r'(আমার কি হয়েছে|আমার কি রোগ)'
    ]
    MEDICATION_PATTERNS = [
        r'\b(what dose|how many mg|which medicine should i take|antibiotic dose|osudh ki)\b',
        r'(কি ওষুধ খাব|কত মিলিগ্রাম|অ্যান্টিবায়োটিক)'
    ]

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        validator: Optional[OutputValidator] = None
    ):
        self.provider = provider or create_llm_provider(settings.LLM_PROVIDER)
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.validator = validator or OutputValidator()

    def is_generation_enabled(self) -> bool:
        return settings.GENERATION_ENABLED and self.provider.is_available()

    def assess_safety(self, query: str, evidence: List[RetrievedEvidenceChunk]) -> GenerationSafetyState:
        """
        Safety and intent classifier based on heuristic patterns.
        NOTE: These are engineering heuristics, NOT medically validated safety boundaries.
        """
        q_lower = query.lower()

        # 1. Self-harm / crisis check
        for pat in self.SELF_HARM_PATTERNS:
            if re.search(pat, q_lower, re.IGNORECASE):
                return GenerationSafetyState.SELF_HARM_OR_CRISIS

        # 2. Emergency red flags
        for pat in self.EMERGENCY_PATTERNS:
            if re.search(pat, q_lower, re.IGNORECASE):
                return GenerationSafetyState.POSSIBLE_EMERGENCY

        # 3. Prescription / Medication dose request
        for pat in self.MEDICATION_PATTERNS:
            if re.search(pat, q_lower, re.IGNORECASE):
                return GenerationSafetyState.MEDICATION_OR_TREATMENT_REQUEST

        # 4. Diagnosis-seeking inquiry
        for pat in self.DIAGNOSIS_PATTERNS:
            if re.search(pat, q_lower, re.IGNORECASE):
                return GenerationSafetyState.DIAGNOSIS_SEEKING

        # 5. Unsupported by active corpus
        if not evidence:
            return GenerationSafetyState.UNSUPPORTED_TOPIC

        return GenerationSafetyState.SAFE_INFORMATIONAL

    def build_grounded_prompt(
        self,
        query: str,
        evidence: List[RetrievedEvidenceChunk],
        preferred_language: str = "auto"
    ) -> GroundedPrompt:
        return self.prompt_builder.build_prompt(query, evidence, preferred_language=preferred_language)

    def validate_output(
        self,
        generated_text: str,
        evidence: List[RetrievedEvidenceChunk]
    ) -> Tuple[PostValidationResult, List[CitationReference]]:
        return self.validator.validate_output(generated_text, evidence)

    def map_outcome_to_generation_policy(
        self,
        outcome_state: RetrievalOutcomeState,
        safety_state: GenerationSafetyState
    ) -> Tuple[bool, Optional[str]]:
        """
        State transition policy mapping retrieval outcome + safety to generation action.
        Returns: (allow_generation, refusal_or_constraint_reason)
        """
        if safety_state == GenerationSafetyState.SELF_HARM_OR_CRISIS:
            return False, "Crisis / self-harm safety guardrail triggered. Please contact emergency services or a crisis helpline immediately."

        if outcome_state == RetrievalOutcomeState.INVALID_QUERY:
            return False, "Query is invalid, empty, or exceeds maximum length."

        if outcome_state in [
            RetrievalOutcomeState.NO_RELEVANT_EVIDENCE,
            RetrievalOutcomeState.UNSUPPORTED_BY_ACTIVE_CORPUS
        ]:
            return False, "No relevant clinical evidence available in the active NHS knowledge base to ground an answer."

        if outcome_state == RetrievalOutcomeState.POSSIBLE_MISMATCH:
            return False, "Retrieved evidence has weak semantic alignment and cannot reliably support a factual answer."

        if outcome_state == RetrievalOutcomeState.LOW_CONFIDENCE_RETRIEVAL:
            # Can generate with explicit caution notice when generation is enabled
            return True, "Evidence confidence is moderate; generation must include uncertainty caveats."

        # SUPPORTED_RETRIEVAL
        return True, None

    def generate_answer(
        self,
        query: str,
        evidence: List[RetrievedEvidenceChunk],
        context: Optional[Dict[str, Any]] = None,
        preferred_language: str = "auto"
    ) -> GenerationResult:
        """
        Full grounded generation orchestration.
        In Phase 6D/6E/6F/6H, operates behind BaseLLMProvider with post-generation validation.
        """
        safety_state = self.assess_safety(query, evidence)
        evidence_ids = [c.chunk_id for c in evidence]

        # Determine retrieval outcome state from evidence
        if not evidence:
            confidence_state = RetrievalOutcomeState.NO_RELEVANT_EVIDENCE
        elif evidence[0].rerank_score >= 0.65:
            confidence_state = RetrievalOutcomeState.SUPPORTED_RETRIEVAL
        elif evidence[0].rerank_score >= 0.35:
            confidence_state = RetrievalOutcomeState.LOW_CONFIDENCE_RETRIEVAL
        elif evidence[0].rerank_score >= 0.18:
            confidence_state = RetrievalOutcomeState.POSSIBLE_MISMATCH
        else:
            confidence_state = RetrievalOutcomeState.UNSUPPORTED_BY_ACTIVE_CORPUS

        # Check policy
        allow_generation, policy_reason = self.map_outcome_to_generation_policy(confidence_state, safety_state)

        # Check if generation is enabled
        if not self.is_generation_enabled():
            return GenerationResult(
                answer=(
                    "[RESEARCH PROTOTYPE MODE: LLM generation is currently disabled by research protocol. "
                    "The authoritative NHS evidence passages retrieved below represent the grounding context for this query.]"
                ),
                citations=[],
                evidence_ids=evidence_ids,
                confidence_state=confidence_state,
                safety_state=safety_state,
                generation_status=GenerationStatus.DISABLED,
                refusal_reason="LLM generation disabled by research protocol.",
                disclaimer="Research Prototype — Not for Medical Decision-Making. LLM generation is disabled.",
                provider_name="disabled",
                model_name="none"
            )

        if not allow_generation:
            return GenerationResult(
                answer=(
                    f"I cannot provide a grounded answer for this query. Reason: {policy_reason}"
                ),
                citations=[],
                evidence_ids=evidence_ids,
                confidence_state=confidence_state,
                safety_state=safety_state,
                generation_status=(
                    GenerationStatus.REFUSED_SAFETY
                    if safety_state in [GenerationSafetyState.SELF_HARM_OR_CRISIS, GenerationSafetyState.POSSIBLE_EMERGENCY]
                    else GenerationStatus.REFUSED_INSUFFICIENT_EVIDENCE
                ),
                refusal_reason=policy_reason,
                disclaimer="Research Prototype — Not for Medical Decision-Making.",
                provider_name=self.provider.get_provider_name(),
                model_name=settings.LLM_MODEL_NAME
            )

        prompt = self.build_grounded_prompt(query, evidence, preferred_language=preferred_language)
        llm_req = LLMRequest(
            prompt=prompt,
            model_name=settings.LLM_MODEL_NAME,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            timeout_seconds=settings.LLM_TIMEOUT_SECONDS
        )
        llm_resp = self.provider.complete(llm_req)

        if llm_resp.error:
            return GenerationResult(
                answer="Generation service encountered a provider error.",
                citations=[],
                evidence_ids=evidence_ids,
                confidence_state=confidence_state,
                safety_state=safety_state,
                generation_status=GenerationStatus.FAILED,
                refusal_reason=llm_resp.error,
                disclaimer="Research Prototype — Not for Medical Decision-Making.",
                provider_name=self.provider.get_provider_name(),
                model_name=settings.LLM_MODEL_NAME
            )

        # Post-generation validation
        val_result, citations = self.validate_output(llm_resp.raw_text, evidence)

        return GenerationResult(
            answer=llm_resp.raw_text,
            citations=citations,
            evidence_ids=evidence_ids,
            confidence_state=confidence_state,
            safety_state=safety_state,
            generation_status=GenerationStatus.COMPLETED if val_result.is_valid else GenerationStatus.FAILED,
            refusal_reason=None if val_result.is_valid else f"Validation failed: {val_result.summary_notes}",
            disclaimer="Research Prototype — Not for Medical Decision-Making.",
            provider_name=self.provider.get_provider_name(),
            model_name=settings.LLM_MODEL_NAME,
            token_usage=llm_resp.token_usage,
            validation_result=val_result
        )

    def generate_response(
        self,
        query: str,
        evidence: List[RetrievedEvidenceChunk],
        preferred_language: str = "auto"
    ) -> Dict[str, Any]:
        """
        Legacy dictionary interface for ChatResponse compatibility.
        """
        res = self.generate_answer(query, evidence, preferred_language=preferred_language)
        return {
            "generation_enabled": self.is_generation_enabled(),
            "status": "research_prototype",
            "synthetic_answer": res.answer,
            "evidence_count": len(evidence),
            "top_source_title": evidence[0].source_title if evidence else "None",
            "disclaimer": res.disclaimer,
            "generation_result": res
        }


# Alias DisabledGenerationService to GroundedGenerationService for backward compatibility
DisabledGenerationService = GroundedGenerationService

_generation_service_instance: Optional[BaseGenerationService] = None

def get_generation_service() -> BaseGenerationService:
    global _generation_service_instance
    if _generation_service_instance is None:
        _generation_service_instance = GroundedGenerationService()
    return _generation_service_instance
