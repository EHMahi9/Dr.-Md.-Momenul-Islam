"""
Provider Abstraction Layer for Grounded LLM Generation (Phase 6D / Phase 6E).
Defines vendor-agnostic interface supporting provider substitution:
- DisabledLLMProvider (Default: zero external calls)
- MockLLMProvider (Deterministic offline testing)
- OpenAICompatibleProvider (Real model integration: LibertAI, OpenAI, Groq, Ollama, vLLM)

ALL SECRETS ARE LOADED FROM ENVIRONMENT VARIABLES ONLY. NEVER HARDCODED.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os
import time
import json
import logging
import requests

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
        """Return canonical provider identifier (e.g., 'openai_compatible', 'gemini', 'disabled')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if provider is configured and available for inference."""
        pass


class DisabledLLMProvider(BaseLLMProvider):
    """
    Default provider implementation.
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


class OpenAICompatibleProvider(BaseLLMProvider):
    """
    Generic HTTP provider for OpenAI-compatible Chat Completions endpoints
    (e.g., LibertAI, OpenAI, Groq, local Ollama/vLLM).
    Handles retry policy, token usage tracking, and latency profiling.
    """

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        api_key_env_var: str = "LLM_API_KEY",
        default_model: str = "qwen3.6-35b-a3b",
        timeout_seconds: int = 30,
        max_retries: int = 2
    ):
        # Allow fallback to specific known provider keys if default LLM_API_KEY is not set
        self.api_key_env_var = api_key_env_var
        self.api_base_url = api_base_url or os.environ.get(
            "LLM_API_BASE_URL",
            "https://api.libertai.io/v1" if os.environ.get("LIBERTAI_API_KEY") else "https://api.openai.com/v1"
        )
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def _get_api_key(self) -> Optional[str]:
        """Fetch API key safely from environment variables without logging or hardcoding."""
        key = os.environ.get(self.api_key_env_var)
        if not key and self.api_key_env_var == "LLM_API_KEY":
            # Fallback check for common vendor env vars
            for alt in ["LIBERTAI_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]:
                val = os.environ.get(alt)
                if val:
                    return val
        return key

    def is_available(self) -> bool:
        """Provider is available if API key is present in environment."""
        key = self._get_api_key()
        return bool(key and len(key.strip()) > 0)

    def get_provider_name(self) -> str:
        if "libertai" in self.api_base_url.lower():
            return "libertai_openai_compatible"
        return "openai_compatible"

    def complete(self, request: LLMRequest) -> LLMResponse:
        api_key = self._get_api_key()
        model_name = request.model_name or self.default_model

        if not api_key:
            logger.warning("[OpenAICompatibleProvider] Missing API key in environment.")
            return LLMResponse(
                raw_text="",
                finish_reason="missing_api_key",
                provider_name=self.get_provider_name(),
                model_name=model_name,
                error=f"API key missing. Environment variable '{self.api_key_env_var}' is not set."
            )

        endpoint = f"{self.api_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Build clean message payload from GroundedPrompt
        system_content = f"{request.prompt.system_instructions}\n\n{request.prompt.safety_instructions}"
        
        grounding_evidence = request.prompt.retrieved_evidence
        evidence_blocks = []
        for idx, item in enumerate(grounding_evidence, start=1):
            evidence_blocks.append(
                f"--- EVIDENCE EXCERPT [{idx}] ---\n"
                f"Chunk ID: {item.chunk_id}\n"
                f"Source: {item.source_title} ({item.parent_source_id})\n"
                f"URL: {item.source_url}\n"
                f"Content:\n{item.excerpt.strip()}\n"
            )
        evidence_text = "\n".join(evidence_blocks) if evidence_blocks else "[NO EVIDENCE PASSAGES RETRIEVED]"
        meta = request.prompt.source_metadata
        
        user_content = (
            f"=== SOURCE METADATA ===\n"
            f"Corpus: Active NHS Knowledge Base ({meta.get('active_conditions', 14)} Conditions)\n"
            f"Licensing: {meta.get('licence', 'Open Government Licence v3.0')}\n\n"
            f"=== RETRIEVED CLINICAL EVIDENCE ===\n{evidence_text}\n\n"
            f"=== USER INQUIRY ===\n{request.prompt.user_question}\n\n"
            f"=== GROUNDED RESPONSE INSTRUCTIONS ===\n"
            f"Synthesize a clear, respectful summary answering the user inquiry based strictly on excerpts [1]..[{len(grounding_evidence)}]. "
            f"Use inline bracket citations like [1] for every supported factual statement."
        )

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }

        start_time = time.time()
        last_error = None

        for attempt in range(1, self.max_retries + 2):
            try:
                resp = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=request.timeout_seconds or self.timeout_seconds
                )
                latency_ms = (time.time() - start_time) * 1000.0

                if resp.status_code == 200:
                    data = resp.json()
                    choice = data["choices"][0]
                    raw_text = choice["message"]["content"] or ""
                    finish_reason = choice.get("finish_reason", "stop")

                    usage_raw = data.get("usage", {})
                    token_usage = TokenUsageMetadata(
                        prompt_tokens=usage_raw.get("prompt_tokens", 0),
                        completion_tokens=usage_raw.get("completion_tokens", 0),
                        total_tokens=usage_raw.get("total_tokens", 0)
                    )

                    return LLMResponse(
                        raw_text=raw_text.strip(),
                        finish_reason=finish_reason,
                        token_usage=token_usage,
                        latency_ms=round(latency_ms, 2),
                        provider_name=self.get_provider_name(),
                        model_name=model_name
                    )
                else:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    logger.warning(f"[OpenAICompatibleProvider] Attempt {attempt} failed: {last_error}")

            except requests.Timeout:
                last_error = f"Request timed out after {request.timeout_seconds}s"
                logger.warning(f"[OpenAICompatibleProvider] Attempt {attempt} timeout")
            except Exception as e:
                last_error = f"Connection error: {str(e)}"
                logger.warning(f"[OpenAICompatibleProvider] Attempt {attempt} error: {e}")

            if attempt <= self.max_retries:
                time.sleep(1.0 * attempt)

        latency_ms = (time.time() - start_time) * 1000.0
        return LLMResponse(
            raw_text="",
            finish_reason="error",
            latency_ms=round(latency_ms, 2),
            provider_name=self.get_provider_name(),
            model_name=model_name,
            error=last_error or "Unknown provider failure after retries"
        )


def create_llm_provider(provider_type: str = "disabled") -> BaseLLMProvider:
    """
    Factory function for provider instantiation.
    Defaults to DisabledLLMProvider for security.
    """
    if provider_type == "mock":
        return MockLLMProvider()
    elif provider_type in ["openai_compatible", "libertai", "real"]:
        return OpenAICompatibleProvider()
    return DisabledLLMProvider()
