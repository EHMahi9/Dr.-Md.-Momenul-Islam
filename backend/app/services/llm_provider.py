"""
Provider Abstraction Layer for Grounded LLM Generation (Phase 6D).
Defines vendor-agnostic interface supporting future provider substitution
(e.g., Google Gemini, OpenAI, Anthropic, Ollama, local models).

NO EXTERNAL LLM PROVIDER IS CALLED IN THIS PHASE.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import time
import logging

from app.schemas.generation_models import (
    LLMRequest,
    LLMResponse,
    TokenUsageMetadata
)

logger = logging.getLogger("dr_momenul_islam.llm_provider")


class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM provider implementations.
    Decouples core application logic from specific model vendors.
    """

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Execute a completion request with timeout and error handling.
        Must return a structured LLMResponse object.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return canonical provider identifier (e.g., 'gemini', 'openai', 'disabled')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if provider is configured and available for inference."""
        pass


class DisabledLLMProvider(BaseLLMProvider):
    """
    Default provider implementation for Phase 6D.
    Strictly prevents any outbound model inference while preserving interface compliance.
    """

    def complete(self, request: LLMRequest) -> LLMResponse:
        logger.info("[DisabledLLMProvider] Completion invoked while generation is disabled by protocol.")
        return LLMResponse(
            raw_text="",
            finish_reason="generation_disabled",
            token_usage=TokenUsageMetadata(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            latency_ms=0.0,
            provider_name=self.get_provider_name(),
            model_name=request.model_name or "none",
            error="LLM generation is disabled by research protocol."
        )

    def get_provider_name(self) -> str:
        return "disabled"

    def is_available(self) -> bool:
        return False


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic mock provider for interface and unit testing only.
    NOT for claiming real model capabilities.
    """

    def __init__(self, canned_response: str = "", fail: bool = False, latency_ms: float = 10.0):
        self.canned_response = canned_response
        self.fail = fail
        self.latency_ms = latency_ms

    def complete(self, request: LLMRequest) -> LLMResponse:
        if self.fail:
            return LLMResponse(
                raw_text="",
                finish_reason="error",
                provider_name=self.get_provider_name(),
                model_name=request.model_name,
                error="Simulated provider connection failure."
            )

        text = self.canned_response or (
            "Based on the retrieved NHS clinical guidance, burns should be cooled under running water for 20 to 30 minutes [1]. "
            "Remove clothing or jewellery near the burnt area unless stuck [2]."
        )
        return LLMResponse(
            raw_text=text,
            finish_reason="stop",
            token_usage=TokenUsageMetadata(prompt_tokens=150, completion_tokens=45, total_tokens=195),
            latency_ms=self.latency_ms,
            provider_name=self.get_provider_name(),
            model_name=request.model_name or "mock-model-v1"
        )

    def get_provider_name(self) -> str:
        return "mock"

    def is_available(self) -> bool:
        return True


def create_llm_provider(provider_type: str = "disabled") -> BaseLLMProvider:
    """
    Factory function for provider instantiation.
    Defaults to DisabledLLMProvider.
    """
    if provider_type == "mock":
        return MockLLMProvider()
    return DisabledLLMProvider()
